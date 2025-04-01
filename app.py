import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QLabel, QPushButton, QHBoxLayout, QFileDialog, QMessageBox,
    QStatusBar, QLineEdit, QComboBox, QCheckBox, QMenu, QMenuBar,
    QDialog, QDialogButtonBox, QSplitter, QProgressBar, QScrollBar, QTextEdit,
    QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSettings, QRect, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction, QIcon, QKeySequence, QFont, QImage, QClipboard
import mss
import mss.tools
import keyboard
import numpy as np
from PIL import Image

# Import custom OCR modules
from ocr_utils import OCRProcessor
from ocr_ui import OCRResultsWidget, OCRImageViewer
# Import custom item database modules
from item_database import ItemDatabase
from item_ui import RecentlyLoggedWidget, ItemDatabaseWidget
# Import tooltip overlay
from tooltip_overlay import TooltipOverlay
# Import inventory UI
from inventory_ui import InventoryWidget
# Import ledger UI
from ledger_ui import LedgerWidget

class ScreenCaptureThread(QThread):
    capture_complete = pyqtSignal(object, object)  # Send both image and cursor position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.capture_width = 300
        self.capture_height = 50
        
    def run(self):
        self.running = True
        while self.running:
            # Check for hotkey press
            if keyboard.is_pressed('f7'):  # Changed hotkey to F7
                # Get mouse position
                try:
                    import pyautogui
                    mouse_x, mouse_y = pyautogui.position()
                except ImportError:
                    # Fallback if pyautogui is not available
                    from ctypes import windll, Structure, c_long, byref
                    
                    class POINT(Structure):
                        _fields_ = [("x", c_long), ("y", c_long)]
                    
                    pt = POINT()
                    windll.user32.GetCursorPos(byref(pt))
                    mouse_x, mouse_y = pt.x, pt.y
                
                # Define the capture region (to the bottom right of cursor)
                region = {
                    'left': mouse_x,
                    'top': mouse_y,
                    'width': self.capture_width,
                    'height': self.capture_height
                }
                
                # Capture the screen
                with mss.mss() as sct:
                    screenshot = sct.grab(region)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    
                    # Emit the captured image along with cursor position for the tooltip
                    self.capture_complete.emit(img, (mouse_x, mouse_y))
                
                # Sleep to prevent multiple captures from a single press
                time.sleep(0.5)
            
            # Small sleep to reduce CPU usage
            time.sleep(0.01)
    
    def stop(self):
        self.running = False


class OCRThread(QThread):
    """Thread for running OCR processing in the background"""
    processing_complete = pyqtSignal(object, object)  # Results, stats
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ocr_processor = OCRProcessor(use_gpu=False, check_models=True)  # CPU-only mode with model check
        self.image = None
        self.preprocess = True  # Default to use preprocessing
        self.item_db = None  # Reference to the item database
        self.match_threshold = 70  # Minimum score for matching
    
    def set_image(self, image):
        """Set the image to process"""
        self.image = image
    
    def set_preprocess(self, enabled):
        """Enable or disable preprocessing"""
        self.preprocess = enabled
    
    def set_item_database(self, item_db):
        """Set the item database reference"""
        self.item_db = item_db
    
    def set_match_threshold(self, threshold):
        """Set the minimum match threshold"""
        self.match_threshold = threshold
    
    def run(self):
        """Run OCR processing on the image"""
        if self.image is None:
            return
            
        # Process the image with or without preprocessing
        results = self.ocr_processor.process_image(self.image, preprocess=self.preprocess)
        stats = self.ocr_processor.get_processing_stats()
        
        # Convert results to the expected format if needed
        formatted_results = []
        for result in results:
            # Format depends on the OCR processor's output
            # Make sure we use consistent field names
            formatted_result = {
                'ocr_text': result.get('text', ''),
                'confidence': result.get('confidence', 0)
            }
            
            # Try to match the OCR text against the database
            if self.item_db:
                match_result = self.item_db.match_item(formatted_result['ocr_text'], min_score=self.match_threshold)
                if match_result:
                    formatted_result['matched_item'] = match_result['name']
                    formatted_result['price'] = match_result.get('price', 0)
                    formatted_result['match_score'] = match_result.get('match_score', 0)
                    
                    # Log the successful match
                    self.item_db.add_to_log(
                        formatted_result['ocr_text'], 
                        match_result['name'], 
                        match_result.get('price', 0), 
                        match_result.get('match_score', 0)
                    )
            
            formatted_results.append(formatted_result)
        
        # Emit the results
        self.processing_complete.emit(formatted_results, stats)


class ModelDownloadThread(QThread):
    """Thread for downloading OCR models in the background"""
    progress_update = pyqtSignal(str)
    download_complete = pyqtSignal(bool)
    
    def __init__(self, ocr_processor, parent=None):
        super().__init__(parent)
        self.ocr_processor = ocr_processor
    
    def run(self):
        """Run the model download process"""
        try:
            # Send initial progress update
            self.progress_update.emit("Initializing download...")
            
            # Process events to ensure UI updates
            QApplication.processEvents()
            
            # Start the download process
            success = self.ocr_processor.download_models(callback=self.progress_update.emit)
            
            # Check for MKL dependencies if on Windows
            if success and sys.platform == 'win32':
                self.progress_update.emit("Checking for required dependencies...")
                self.check_mkl_dependencies()
            
            # Emit completion signal
            self.download_complete.emit(success)
        except Exception as e:
            print(f"Download thread error: {str(e)}")
            self.progress_update.emit(f"Error: {str(e)}")
            self.download_complete.emit(False)
    
    def check_mkl_dependencies(self):
        """Check for MKL dependencies and provide guidance if missing"""
        try:
            # Try to import paddle to check dependencies
            import paddle
            self.progress_update.emit("PaddlePaddle dependencies verified.")
        except ImportError:
            self.progress_update.emit("PaddlePaddle not found. Please install it manually.")
        except RuntimeError as e:
            error_msg = str(e)
            if "mklml.dll" in error_msg or "libmklml.so" in error_msg:
                self.progress_update.emit("MKL dependency missing. Adding search paths...")
                
                # Try to locate MKL libraries in common locations
                current_dir = os.path.dirname(os.path.abspath(__file__))
                lib_dirs = [
                    os.path.join(current_dir, 'paddle', 'libs'),
                    os.path.join(current_dir, 'paddle'),
                    os.path.join(current_dir, 'libs'),
                    os.path.join(os.path.dirname(current_dir), 'paddle', 'libs'),
                    os.path.join(os.path.dirname(current_dir), 'libs')
                ]
                
                for lib_dir in lib_dirs:
                    if os.path.exists(lib_dir):
                        os.environ['PATH'] = lib_dir + os.pathsep + os.environ.get('PATH', '')
                        self.progress_update.emit(f"Added {lib_dir} to PATH")
            else:
                self.progress_update.emit(f"PaddlePaddle error: {error_msg}")


class ModelDownloadDialog(QDialog):
    """Dialog for downloading OCR models"""
    
    def __init__(self, ocr_processor, parent=None):
        super().__init__(parent)
        self.ocr_processor = ocr_processor
        self.setWindowTitle("Download OCR Models")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add information label
        info_label = QLabel(
            "The OCR models required for text recognition are not found.\n"
            "Would you like to download them now?\n\n"
            "This is a one-time download of approximately 20MB."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Add progress label
        self.progress_label = QLabel("Ready to download")
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.progress_label)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Add log text area
        log_label = QLabel("Download Log:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        
        layout.addWidget(self.log_text)
        
        # Add buttons
        button_layout = QHBoxLayout()
        self.download_button = QPushButton("Download Models")
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Create download thread
        self.download_thread = ModelDownloadThread(self.ocr_processor, self)
        self.download_thread.progress_update.connect(self.update_progress)
        self.download_thread.download_complete.connect(self.download_finished)
        
        # Log entries
        self.log_entries = []
    
    def start_download(self):
        """Start the download process"""
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.progress_label.setText("Starting download...")
        self.progress_bar.setVisible(True)
        
        # Clear log entries
        self.log_entries = []
        self.add_log_entry("Starting download process...")
        
        # Process events to ensure UI updates before starting the thread
        QApplication.processEvents()
        
        # Start the download thread
        self.download_thread.start()
    
    def add_log_entry(self, message):
        """Add a log entry to the log text area"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[{timestamp}] {message}"
        self.log_entries.append(log_entry)
        
        # Keep only the last 100 log entries to prevent memory issues
        if len(self.log_entries) > 100:
            self.log_entries = self.log_entries[-100:]
        
        # Update the log text
        self.log_text.setText("\n".join(self.log_entries))
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
        # Process events to ensure UI updates
        QApplication.processEvents()
    
    def update_progress(self, message):
        """Update the progress label with download status"""
        self.progress_label.setText(message)
        self.add_log_entry(message)
        # Process events to ensure UI updates
        QApplication.processEvents()
    
    def download_finished(self, success):
        """Handle download completion"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.progress_label.setText("Download completed successfully!")
            self.add_log_entry("Download completed successfully!")
            
            # Check if there was an initialization error
            if self.ocr_processor.initialization_error:
                self.add_log_entry(f"Warning: {self.ocr_processor.initialization_error}")
                self.add_log_entry("The models were downloaded but there might be missing dependencies.")
                self.add_log_entry("Please check the console for more details.")
                
                # Show dependency help
                self.add_log_entry("\nPossible solutions for dependency issues:")
                self.add_log_entry("1. Make sure you have Visual C++ Redistributable installed")
                self.add_log_entry("2. Try reinstalling PaddlePaddle with: pip install paddlepaddle==2.4.2")
                self.add_log_entry("3. For MKL errors, ensure Intel MKL libraries are in your PATH")
                
                # Enable buttons to allow user to close the dialog
                self.download_button.setEnabled(False)
                self.cancel_button.setEnabled(True)
                self.cancel_button.setText("Close")
            else:
                # Process events to ensure UI updates
                QApplication.processEvents()
                # Short delay to show success message before closing
                QTimer.singleShot(1500, self.accept)
        else:
            self.progress_label.setText("Download failed. Please try again.")
            self.add_log_entry("Download failed. Please check the log for errors.")
            self.download_button.setEnabled(True)
            self.cancel_button.setEnabled(True)


class MainWindow(QMainWindow):
    """Main application window for MapleLegends ShopHelper"""
    
    def __init__(self):
        super().__init__()
        
        # Set up the main window
        self.setWindowTitle("MapleLegends ShopHelper")
        self.setMinimumSize(800, 600)
        
        # Set the window icon
        app_icon = QPixmap("app_icon.png")
        self.setWindowIcon(QIcon(app_icon))
        
        # Initialize instance variables
        self.current_image = None
        self.always_on_top = True
        self.copy_price_to_clipboard = True
        self.show_tooltips = True  # Enable tooltips by default
        self.tooltip_size = 1.0  # Default tooltip size factor
        self.match_threshold = 0  # Default match threshold - 0% to allow new matches
        self.logs = []
        
        # Initialize OCR processor to check for models
        self.ocr_processor = OCRProcessor(use_gpu=False, check_models=True)
        
        # Check if models exist and show download dialog if needed
        if not self.ocr_processor.models_exist:
            self.show_model_download_dialog()
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)
        
        # Create matched item display frame in the top left
        self.create_matched_item_display()
        
        # Create the tab widget - only Database and Logs tabs
        self.tab_widget = QTabWidget()
        
        # Create item database before creating tabs
        self.item_database = ItemDatabase()
        
        # Create Database and Logs tabs (removed Capture and OCR tabs)
        self.create_database_tab()
        self.create_log_tab()
        self.create_inventory_tab()
        self.create_ledger_tab()
        
        # Add tab widget to main layout
        self.main_layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Press F7 to capture and identify items")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create tooltip overlay
        self.tooltip_overlay = TooltipOverlay()
        
        # Create screen capture thread
        self.capture_thread = ScreenCaptureThread()
        self.capture_thread.capture_complete.connect(self.process_screen_capture)
        self.capture_thread.start()
        
        # Create OCR processing thread
        self.ocr_thread = OCRThread()
        self.ocr_thread.processing_complete.connect(self.handle_ocr_results)
        
        # Connect item database to OCR thread
        self.ocr_thread.set_item_database(self.item_database)
        
        # Set the match threshold
        self.ocr_thread.set_match_threshold(self.match_threshold)
        
        # Update database UI
        self.update_database_ui()
    
    def create_matched_item_display(self):
        """Create the matched item display frame"""
        # Create a horizontal layout for the header section that will contain both
        # the matched item display and the app title/instructions
        self.header_container = QHBoxLayout()
        
        # Create the matched item frame with dark mode styling but no borders
        self.matched_item_frame = QFrame()
        self.matched_item_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        # Set fixed dimensions for the frame to ensure consistent layout
        self.matched_item_frame.setFixedWidth(320)
        self.matched_item_frame.setFixedHeight(80)
        
        # Use a more compact layout for the matched item display
        self.matched_item_layout = QVBoxLayout(self.matched_item_frame)
        self.matched_item_layout.setContentsMargins(8, 8, 8, 8)
        self.matched_item_layout.setSpacing(4)
        
        # Header label with no border
        self.matched_item_label = QLabel("Last Matched Item")
        self.matched_item_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.matched_item_label.setStyleSheet("color: #AAAAAA; border: none;")
        self.matched_item_layout.addWidget(self.matched_item_label)
        
        # Combined item name and price label with no border
        self.matched_item_info = QLabel("No item matched")
        self.matched_item_info.setFont(QFont("Arial", 10))
        self.matched_item_info.setStyleSheet("color: #FFFFFF; border: none;")
        self.matched_item_info.setWordWrap(True)
        self.matched_item_info.setMinimumHeight(40)
        self.matched_item_layout.addWidget(self.matched_item_info)
        
        # Add the frame to the left side of the header container
        self.header_container.addWidget(self.matched_item_frame)
        
        # Add a stretch to push the title section to the right
        self.header_container.addStretch(1)
        
        # Create the title and instructions section
        self.title_section = QVBoxLayout()
        
        # Create a horizontal layout for the title and icon
        title_row = QHBoxLayout()
        
        # Add app icon next to the title
        self.app_icon_label = QLabel()
        app_icon = QPixmap("app_icon.png")
        scaled_icon = app_icon.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.app_icon_label.setPixmap(scaled_icon)
        title_row.addWidget(self.app_icon_label)
        
        # App title
        self.title_label = QLabel("MapleLegends ShopHelper")
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(self.title_label)
        
        # Add the title row to the title section
        self.title_section.addLayout(title_row)
        
        # Instructions
        self.instructions = QLabel("Press F7 while hovering over item text to capture and identify items")
        self.instructions.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.title_section.addWidget(self.instructions)
        
        # Add the title section to the header container
        self.header_container.addLayout(self.title_section)
        
        # Add the header container to the main layout
        self.main_layout.addLayout(self.header_container)
        
        # Start with the placeholder state
        self.set_placeholder_state()
    
    def clear_matched_item_display(self):
        """Clear the matched item display and set to placeholder state"""
        self.set_placeholder_state()
        
    def set_placeholder_state(self):
        """Set the matched item display to its placeholder state"""
        self.matched_item_info.setText("No item matched\nPress F7 to capture")
        self.matched_item_info.setStyleSheet("color: #AAAAAA; border: none;") # Gray for placeholder
    
    def create_database_tab(self):
        """Create the database tab"""
        self.db_tab = QWidget()
        self.db_layout = QVBoxLayout(self.db_tab)
        
        # Create item database widget
        self.database_widget = ItemDatabaseWidget()
        self.database_widget.item_added.connect(self.handle_item_added)
        self.database_widget.item_edited.connect(self.handle_item_edited)
        self.database_widget.item_deleted.connect(self.handle_item_deleted)
        self.database_widget.search_requested.connect(self.handle_search_request)
        self.database_widget.stock_updated.connect(self.handle_stock_updated)
        self.db_layout.addWidget(self.database_widget)
        
        # Add to tabs
        self.tab_widget.addTab(self.db_tab, "Database")
        
    def create_log_tab(self):
        """Create the recently logged items tab"""
        self.log_tab = QWidget()
        self.log_layout = QVBoxLayout(self.log_tab)
        
        # Create recently logged widget
        self.log_widget = RecentlyLoggedWidget()
        self.log_widget.item_corrected.connect(self.handle_log_correction)
        self.log_widget.stock_updated.connect(self.handle_stock_updated)
        self.log_layout.addWidget(self.log_widget)
        
        # Add to tabs
        self.tab_widget.addTab(self.log_tab, "Recent Logs")
        
    def create_inventory_tab(self):
        """Create the inventory tab"""
        self.inventory_tab = QWidget()
        self.inventory_layout = QVBoxLayout(self.inventory_tab)
        
        # Create inventory widget
        self.inventory_widget = InventoryWidget()
        self.inventory_widget.stock_updated.connect(self.handle_stock_updated)
        self.inventory_widget.item_sold.connect(self.handle_item_sold)
        self.inventory_widget.price_updated.connect(self.handle_price_updated)
        self.inventory_layout.addWidget(self.inventory_widget)
        
        # Add to tabs
        self.tab_widget.addTab(self.inventory_tab, "Inventory")
        
    def create_ledger_tab(self):
        """Create the ledger tab"""
        self.ledger_tab = QWidget()
        self.ledger_layout = QVBoxLayout(self.ledger_tab)
        
        # Create ledger widget with item database reference
        self.ledger_widget = LedgerWidget(self, self.item_database)
        self.ledger_layout.addWidget(self.ledger_widget)
        
        # Connect cash balance changes to ledger refresh
        self.ledger_widget.cash_balance_changed.connect(self.refresh_ledger)
        
        # Add to tabs
        self.tab_widget.addTab(self.ledger_tab, "Ledger")
        
    def create_menu_bar(self):
        """Create the main menu bar"""
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        
        # File menu
        self.file_menu = self.menu_bar.addMenu("File")
        
        # Export database action
        export_action = QAction("Export Database", self)
        export_action.triggered.connect(self.export_database)
        self.file_menu.addAction(export_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        
        # Options menu
        self.options_menu = self.menu_bar.addMenu("Options")
        
        # Always on top action
        self.always_on_top_action = QAction("Always On Top", self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.setChecked(self.always_on_top)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        self.options_menu.addAction(self.always_on_top_action)
        
        # Copy price to clipboard action
        self.copy_price_action = QAction("Copy Price to Clipboard", self)
        self.copy_price_action.setCheckable(True)
        self.copy_price_action.setChecked(self.copy_price_to_clipboard)
        self.copy_price_action.triggered.connect(self.toggle_copy_price)
        self.options_menu.addAction(self.copy_price_action)
        
        # Preprocessing toggle
        self.preprocess_action = QAction("Preprocess Game Text", self)
        self.preprocess_action.setCheckable(True)
        self.preprocess_action.setChecked(True)  # Default to enabled
        self.preprocess_action.triggered.connect(self.toggle_preprocessing)
        self.options_menu.addAction(self.preprocess_action)
        
        # Confidence threshold submenu
        self.confidence_menu = self.options_menu.addMenu("Match Confidence Threshold")
        
        # Add confidence threshold options
        thresholds = [0, 50, 60, 70, 80, 90]
        for threshold in thresholds:
            threshold_action = QAction(f"{threshold}%", self)
            threshold_action.setCheckable(True)
            threshold_action.setChecked(threshold == self.match_threshold)
            threshold_action.triggered.connect(lambda checked, t=threshold: self.set_match_threshold(t))
            self.confidence_menu.addAction(threshold_action)
        
        # Tooltip submenu
        self.tooltip_menu = self.options_menu.addMenu("Tooltip Options")
        
        # Show tooltips action
        self.show_tooltips_action = QAction("Show Tooltips", self)
        self.show_tooltips_action.setCheckable(True)
        self.show_tooltips_action.setChecked(self.show_tooltips)
        self.show_tooltips_action.triggered.connect(self.toggle_tooltips)
        self.tooltip_menu.addAction(self.show_tooltips_action)
        
        # Tooltip size actions
        self.tooltip_menu.addSeparator()
        self.tooltip_menu.addAction("Tooltip Size:")
        
        # Small tooltip size
        small_size_action = QAction("Small", self)
        small_size_action.triggered.connect(lambda: self.set_tooltip_size(0.7))
        self.tooltip_menu.addAction(small_size_action)
        
        # Medium tooltip size
        medium_size_action = QAction("Medium", self)
        medium_size_action.triggered.connect(lambda: self.set_tooltip_size(1.0))
        self.tooltip_menu.addAction(medium_size_action)
        
        # Large tooltip size
        large_size_action = QAction("Large", self)
        large_size_action.triggered.connect(lambda: self.set_tooltip_size(1.5))
        self.tooltip_menu.addAction(large_size_action)
        
        # Help menu
        self.help_menu = self.menu_bar.addMenu("Help")
        
        # Download OCR models action
        download_models_action = QAction("Download OCR Models", self)
        download_models_action.triggered.connect(self.show_model_download_dialog)
        self.help_menu.addAction(download_models_action)
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(about_action)
    
    def toggle_always_on_top(self, checked):
        """Toggle the always on top flag"""
        self.always_on_top = checked
        
        # Set the window flag
        if self.always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.status_bar.showMessage("Window will now stay on top")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.status_bar.showMessage("Window will no longer stay on top")
        
        # Show the window again to apply the flag
        self.show()
    
    def toggle_copy_price(self, checked):
        """Toggle the copy price to clipboard flag"""
        self.copy_price_to_clipboard = checked
        
        if checked:
            self.status_bar.showMessage("Prices will be copied to clipboard when scanning")
        else:
            self.status_bar.showMessage("Prices will not be copied to clipboard")
    
    def toggle_preprocessing(self, checked):
        """Toggle preprocessing for game text"""
        self.ocr_thread.set_preprocess(checked)
        if checked:
            self.status_bar.showMessage("Game text preprocessing enabled")
        else:
            self.status_bar.showMessage("Game text preprocessing disabled")
    
    def process_screen_capture(self, img, cursor_pos=None):
        """Process captured screen image by immediately running OCR
        
        Args:
            img: The captured image
            cursor_pos: The cursor position at time of capture (x, y)
        """
        # If we have a valid image
        if img:
            # Store the current image
            self.current_image = img
            
            # Process OCR directly (no UI needed anymore)
            self.ocr_thread.set_image(img)
            self.ocr_thread.item_db = self.item_database  # Ensure item database is connected
            
            # Store cursor position for tooltip
            self.last_cursor_pos = cursor_pos
            
            # Run OCR processing
            self.ocr_thread.run()
    
    def export_database(self):
        """Export the database to a JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Database", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.item_database.save_database_to(file_path)
                self.status_bar.showMessage(f"Database exported to {file_path}")
            except Exception as e:
                self.status_bar.showMessage(f"Error exporting database: {e}")
    
    def handle_item_added(self, item_name, price):
        """Handle added item from the database widget"""
        self.item_database.add_item(item_name, price)
        self.status_bar.showMessage(f"Added new item: {item_name} with price: {price:,}")
        self.update_database_ui()
    
    def handle_item_edited(self, original_name, new_name, price):
        """Handle edited item from the database widget"""
        self.item_database.update_item(original_name, price, new_name)
        
        # Show appropriate message based on what changed
        if original_name != new_name:
            self.status_bar.showMessage(f"Renamed '{original_name}' to '{new_name}' with price: {price:,}")
        else:
            self.status_bar.showMessage(f"Updated price for '{original_name}' to: {price:,}")
            
        self.update_database_ui()
    
    def handle_item_deleted(self, item_name):
        """Handle deleted item from the database widget"""
        self.item_database.delete_item(item_name)
        self.status_bar.showMessage(f"Deleted item: {item_name}")
        self.update_database_ui()
    
    def handle_search_request(self, query):
        """Handle fuzzy search request from the database widget"""
        # Perform the search using the item database
        results = self.item_database.search_items(query)
        
        # Update the UI with the results
        self.database_widget.update_search_results(results)
        
        # Update status bar
        if results:
            self.status_bar.showMessage(f"Found {len(results)} items matching '{query}'")
        else:
            self.status_bar.showMessage(f"No items found matching '{query}'")
    
    def handle_log_correction(self, log_index, new_values):
        """Handle correction of a log entry"""
        if not new_values:
            return
            
        # Get new item name and price
        item_name = new_values.get('item_name')
        price = new_values.get('price')
        
        if item_name:
            # Update the log entry
            success = self.item_database.correct_log_entry(log_index, item_name, price)
            
            if success:
                self.status_bar.showMessage(f"Corrected log entry: {item_name} with price: {price:,}")
                
                # Check if we need to add or update this item in the database
                if not self.item_database.get_item(item_name) and price is not None:
                    # Ask if user wants to add this item to the database
                    reply = QMessageBox.question(
                        self, "Add to Database?",
                        f"Would you like to add '{item_name}' to the database with price {price:,}?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.item_database.add_item(item_name, price)
                
                # Update the UI
                self.update_database_ui()
            else:
                self.status_bar.showMessage("Failed to correct log entry")
    
    def handle_stock_updated(self, item_name, new_stock):
        """Handle stock update from any widget"""
        # First check if the item exists in our database
        if item_name in self.item_database.items:
            # Get current stock for logging purposes
            current_stock = self.item_database.items[item_name].get('stock', 0)
            
            # Update the stock
            if self.item_database.update_stock(item_name, new_stock):
                # Update all UI components
                self.update_database_ui()
                
                # Show appropriate status message
                if new_stock > current_stock:
                    self.status_bar.showMessage(f"Added {new_stock - current_stock} to stock of '{item_name}' (now {new_stock})")
                elif new_stock < current_stock:
                    self.status_bar.showMessage(f"Removed {current_stock - new_stock} from stock of '{item_name}' (now {new_stock})")
                else:
                    self.status_bar.showMessage(f"Stock of '{item_name}' unchanged at {new_stock}")
                
                # Copy price to clipboard if enabled and stock was increased
                if self.copy_price_to_clipboard and new_stock > current_stock:
                    price = self.item_database.items[item_name].get('price', 0)
                    if price:
                        QApplication.clipboard().setText(str(price))
                        self.status_bar.showMessage(f"Added {new_stock - current_stock} to stock of '{item_name}' (now {new_stock}) - Price copied to clipboard")
            else:
                self.status_bar.showMessage(f"Failed to update stock of '{item_name}'")
        else:
            self.status_bar.showMessage(f"Item '{item_name}' not found in database")
    
    def handle_item_sold(self, item_name, quantity, selling_price=None):
        """Handle when an item is marked as sold"""
        # Get current stock
        if item_name in self.item_database.items:
            current_stock = self.item_database.items[item_name].get('stock', 0)
            default_price = self.item_database.items[item_name].get('price', 0)
            
            # Mark as sold
            if self.item_database.mark_as_sold(item_name, quantity, selling_price):
                # Update all UI components
                self.update_database_ui()
                
                # Show success message
                sale_value = quantity * (selling_price if selling_price is not None else default_price)
                price_info = f" at {selling_price:,} each" if selling_price is not None and selling_price != default_price else ""
                self.status_bar.showMessage(f"Sold {quantity} of '{item_name}'{price_info} for {sale_value:,} (stock now {current_stock - quantity})")
                
                # Update the ledger
                self.update_ledger()
            else:
                self.status_bar.showMessage(f"Failed to mark '{item_name}' as sold")
        else:
            self.status_bar.showMessage(f"Item '{item_name}' not found in database")
    
    def update_inventory_ui(self):
        """Update the inventory UI with current data"""
        if hasattr(self, 'inventory_widget'):
            # Get inventory data
            inventory_data = self.item_database.get_inventory_data()
            
            # Calculate statistics
            total_items = len(inventory_data)
            items_with_stock = sum(1 for item in inventory_data if item['stock'] > 0)
            total_value = sum(item['value'] for item in inventory_data)
            
            stats = {
                'total_items': total_items,
                'items_with_stock': items_with_stock,
                'total_value': total_value
            }
            
            # Update inventory widget
            self.inventory_widget.update_inventory(inventory_data, stats)
            
    def update_ledger(self):
        """Update the ledger display"""
        # Get ledger entries from the database
        entries = self.item_database.get_ledger_entries(limit=1000)  # Get more entries
        stats = self.item_database.get_ledger_stats()
        
        # Update the ledger widget
        self.ledger_widget.update_data(entries, stats)
        
    def refresh_ledger(self):
        """Refresh the ledger display - called when cash transactions are made"""
        # Update the ledger
        self.update_ledger()
        
        # Update inventory UI since cash affects total assets
        self.update_inventory_ui()
        
    def update_database_ui(self):
        """Update all database-related UI components"""
        # Update recently logged items
        recently_logged_data = self.item_database.get_recent_logs(limit=100)
        # Enhance log data with stock information
        for entry in recently_logged_data:
            matched_item = entry.get('matched_item')
            if matched_item and matched_item in self.item_database.items:
                entry['stock'] = self.item_database.items[matched_item].get('stock', 0)
                
        self.log_widget.update_log(recently_logged_data)
        
        # Update database view
        self.database_widget.update_items(self.item_database.items)
        
        # Update inventory
        self.update_inventory_ui()
        
        # Update ledger
        self.update_ledger()
    
    def handle_ocr_results(self, results, stats):
        """Handle OCR results from the OCR thread"""
        if stats.get('status') == 'error':
            self.status_bar.showMessage(f"OCR error: {stats.get('message', 'Unknown error')}")
            return
        
        # Store the OCR results
        self.ocr_results = results
        
        # Update matched item display immediately
        self.update_ui_with_ocr_results()
        
        # Show processing time in status bar
        proc_time = stats.get('processing_time', 0)
        self.status_bar.showMessage(f"OCR completed in {proc_time:.2f} seconds")
        
        # Check if we should copy a price to clipboard
        if self.copy_price_to_clipboard:
            for result in results:
                if result.get('matched_item') and result.get('price') is not None:
                    price = result.get('price')
                    item_name = result.get('matched_item')
                    
                    # Copy the raw price without commas
                    clipboard = QApplication.clipboard()
                    clipboard.setText(str(price))
                    
                    # Show tooltip at cursor position if available
                    if self.show_tooltips and hasattr(self, 'last_cursor_pos') and self.last_cursor_pos:
                        from PyQt6.QtCore import QPoint
                        cursor_point = QPoint(self.last_cursor_pos[0], self.last_cursor_pos[1])
                        self.tooltip_overlay.show_tooltip(item_name, price, cursor_point)
                    
                    # Show feedback (display with commas in the UI only)
                    formatted_price = f"{price:,}"
                    self.status_bar.showMessage(f"Copied price to clipboard: {price} for {item_name}")
                    break  # Only copy the first match
    
    def process_ocr_results(self, results):
        """Process OCR results and check for item matches"""
        # Handled by OCRThread directly now
        pass
    
    def update_ui_with_ocr_results(self):
        """Update UI elements with OCR results"""
        # Switch to Recent Logs tab to show the results
        self.tab_widget.setCurrentIndex(1)  # Recent Logs tab
        
        # Update database UI
        self.update_database_ui()
        
        # Update matched item display
        if self.ocr_results and len(self.ocr_results) > 0:
            # Find the best match (highest confidence)
            best_match = None
            best_score = 0
            
            for result in self.ocr_results:
                if result.get('matched_item') and result.get('match_score', 0) > best_score:
                    best_match = result
                    best_score = result.get('match_score', 0)
            
            if best_match:
                matched_item = best_match.get('matched_item', '')
                price = best_match.get('price', 0)
                match_score = best_match.get('match_score', 0)
                ocr_text = best_match.get('ocr_text', '')
                
                # Update the display with detailed information
                self.matched_item_info.setText(f"{matched_item}\nPrice: {price:,} mesos")
                self.matched_item_info.setStyleSheet("color: #50C878; border: none;") # Green for price
                
                # Set tooltip with additional information
                tooltip = f"OCR Text: {ocr_text}\nMatch Score: {match_score}%"
                self.matched_item_info.setToolTip(tooltip)
            else:
                # No match found but OCR detected something
                self.matched_item_info.setText("No match found\nTry again with F7")
                self.matched_item_info.setStyleSheet("color: #FF6B6B; border: none;") # Red for no match
        else:
            # No OCR results, reset to placeholder state
            self.set_placeholder_state()
    
    def show_about(self):
        QMessageBox.about(
            self, 
            "About MapleLegends ShopHelper",
            "MapleLegends ShopHelper v1.0\n\n"
            "A tool for capturing, identifying, and tracking item prices in MapleLegends.\n\n"
            "Press F7 while hovering over item text to automatically capture and identify items."
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop the capture thread
        self.capture_thread.stop()
        self.capture_thread.wait()
        
        # Accept the event
        event.accept()
    
    def toggle_tooltips(self, checked):
        """Toggle showing tooltips when items are matched"""
        self.show_tooltips = checked
        if checked:
            self.status_bar.showMessage("Tooltips enabled")
        else:
            self.status_bar.showMessage("Tooltips disabled")
    
    def set_tooltip_size(self, size_factor):
        """Set the size of tooltips"""
        self.tooltip_size = size_factor
        self.tooltip_overlay.set_size_factor(size_factor)
        
        size_name = "Small"
        if size_factor >= 1.3:
            size_name = "Large"
        elif size_factor >= 0.9:
            size_name = "Medium"
            
        self.status_bar.showMessage(f"Tooltip size set to {size_name}")
    
    def set_match_threshold(self, threshold):
        """Set the minimum confidence threshold for item matching"""
        # Update all checkable actions in the confidence menu
        for action in self.confidence_menu.actions():
            if action.isCheckable():
                action.setChecked(action.text() == f"{threshold}%")
        
        # Set the new threshold
        self.match_threshold = threshold
        self.ocr_thread.set_match_threshold(threshold)
        self.status_bar.showMessage(f"Match confidence threshold set to {threshold}%")
    
    def toggle_preprocessing(self, checked):
        """Toggle preprocessing for game text"""
        self.ocr_thread.set_preprocess(checked)
        if checked:
            self.status_bar.showMessage("Game text preprocessing enabled")
        else:
            self.status_bar.showMessage("Game text preprocessing disabled")
    
    def show_model_download_dialog(self):
        """Show dialog to download OCR models if they don't exist"""
        dialog = ModelDownloadDialog(self.ocr_processor, self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Models were downloaded successfully
            QMessageBox.information(
                self,
                "Download Complete",
                "OCR models were downloaded successfully. The application is ready to use."
            )
        else:
            # User cancelled or download failed
            QMessageBox.warning(
                self,
                "Models Not Available",
                "OCR functionality will not be available without the required models.\n"
                "You can download them later from the Help menu."
            )
    
    def handle_price_updated(self, item_name, new_price):
        """Handle price update from inventory widget"""
        # Update the price in the database
        if self.item_database.update_price(item_name, new_price):
            self.status_bar.showMessage(f"Updated price of {item_name} to {new_price:,}", 5000)
            
            # Refresh inventory display - use the same method as update_inventory_ui
            inventory_data = self.item_database.get_inventory_data()
            
            # Calculate statistics
            total_items = len(inventory_data)
            items_with_stock = sum(1 for item in inventory_data if item['stock'] > 0)
            total_value = sum(item['value'] for item in inventory_data)
            
            stats = {
                'total_items': total_items,
                'items_with_stock': items_with_stock,
                'total_value': total_value
            }
            
            # Update inventory widget
            self.inventory_widget.update_inventory(inventory_data, stats)
            
            # Refresh ledger if it exists
            if hasattr(self, 'ledger_widget'):
                self.update_ledger()
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
