"""
OCR UI Components for MapleLegends ShopHelper
Provides UI elements for displaying OCR results
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPen, QColor, QImage

class OCRResultsWidget(QWidget):
    """Widget for displaying OCR results with text and confidence"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Header
        self.header_label = QLabel("OCR Results")
        self.header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.header_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(separator)
        
        # Results table - now with 4 columns to include match information
        self.results_table = QTableWidget(0, 4)  # 0 rows, 4 columns
        self.results_table.setHorizontalHeaderLabels(["OCR Text", "Confidence", "Matched Item", "Price"])
        
        # Configure column sizes
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # OCR Text
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Confidence
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Matched Item
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Price
        
        self.layout.addWidget(self.results_table)
        
        # Stats label
        self.stats_label = QLabel("No processing stats available")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.stats_label)
    
    def set_results(self, ocr_results):
        """Set OCR results with potential item matches"""
        # Clear existing results
        self.results_table.setRowCount(0)
        
        # Add new results
        if not ocr_results:
            return
            
        for i, result in enumerate(ocr_results):
            self.results_table.insertRow(i)
            
            # OCR Text column
            text_item = QTableWidgetItem(result['text'])
            self.results_table.setItem(i, 0, text_item)
            
            # Confidence column
            confidence = result.get('confidence', 0)
            confidence_item = QTableWidgetItem(f"{confidence:.2f}%")
            self.results_table.setItem(i, 1, confidence_item)
            
            # Matched Item column (if available)
            match = result.get('match')
            if match:
                name_item = QTableWidgetItem(match['name'])
                self.results_table.setItem(i, 2, name_item)
                
                # Price column
                price_text = f"{match['price']:,}" if 'price' in match else ""
                price_item = QTableWidgetItem(price_text)
                self.results_table.setItem(i, 3, price_item)
            else:
                # No match found
                self.results_table.setItem(i, 2, QTableWidgetItem("No match"))
                self.results_table.setItem(i, 3, QTableWidgetItem(""))
    
    def update_stats(self, stats):
        """Update the stats label with processing information"""
        if not stats:
            self.stats_label.setText("No processing stats available")
            return
            
        # Format processing time
        proc_time = stats.get('processing_time', 0)
        proc_text = f"Processing time: {proc_time:.2f}s"
        
        # Get preprocessing status
        preproc = stats.get('preprocessing', False)
        preproc_text = "Preprocessing: Enabled" if preproc else "Preprocessing: Disabled"
        
        # Display stats
        self.stats_label.setText(f"{proc_text} | {preproc_text}")
    
    def clear(self):
        """Clear all results"""
        self.results_table.setRowCount(0)
        self.stats_label.setText("No processing stats available")


class OCRImageViewer(QWidget):
    """Widget for displaying image with OCR results overlaid"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        self.layout.addWidget(self.image_label)
        
        # Current image and results
        self.current_image = None
        self.current_results = None
        
        # Set minimum size
        self.setMinimumSize(320, 100)
    
    def set_image(self, image, results=None):
        """Set the image and optionally overlay OCR results"""
        if image is None:
            self.clear()
            return
            
        # Store current image and results
        self.current_image = image
        self.current_results = results
        
        # Create a copy of the image to draw on
        if image.mode != "RGBA":
            img_copy = image.convert("RGBA")
        else:
            img_copy = image.copy()
        
        # Draw OCR results on the image if available
        if results:
            # Create a painter to draw on the image
            img_data = img_copy.tobytes("raw", "RGBA")
            qimg = QImage(img_data, img_copy.width, img_copy.height, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            for result in results:
                # Get bounding box coordinates
                box = result.get('box', [])
                if not box or len(box) != 4:
                    continue
                    
                # Draw bounding box
                pen = QPen(QColor(255, 0, 0, 180), 2)  # Semi-transparent red
                painter.setPen(pen)
                
                # Box is [top-left, top-right, bottom-right, bottom-left]
                points = [
                    (int(box[0][0]), int(box[0][1])),  # top-left
                    (int(box[1][0]), int(box[1][1])),  # top-right
                    (int(box[2][0]), int(box[2][1])),  # bottom-right
                    (int(box[3][0]), int(box[3][1]))   # bottom-left
                ]
                
                # Draw the box
                for i in range(4):
                    painter.drawLine(
                        points[i][0], points[i][1],
                        points[(i+1)%4][0], points[(i+1)%4][1]
                    )
            
            painter.end()
            
            # Display the pixmap
            self.image_label.setPixmap(pixmap)
            self.image_label.setMinimumSize(pixmap.size())
        else:
            # Display original image without overlay
            # Convert PIL Image to QPixmap
            img_data = img_copy.tobytes("raw", "RGBA")
            qimg = QImage(img_data, img_copy.width, img_copy.height, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.image_label.setPixmap(pixmap)
            self.image_label.setMinimumSize(pixmap.size())
    
    def clear(self):
        """Clear the image and results"""
        self.image_label.clear()
        self.current_image = None
        self.current_results = None
