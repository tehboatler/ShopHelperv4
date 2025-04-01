"""
Tooltip Overlay for MapleLegends ShopHelper
Provides a floating tooltip that appears near the cursor when an item is matched
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt6.QtGui import QFont, QColor, QPalette


class TooltipOverlay(QWidget):
    """A floating tooltip that appears near the cursor"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the widget to be frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Make the background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border-radius: 10px;
                padding: 5px;
            }
            QLabel {
                color: white;
                padding: 5px;
            }
        """)
        
        # Create the layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        
        # Create labels for item name and price
        self.item_name_label = QLabel()
        self.item_name_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.item_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.price_label = QLabel()
        self.price_label.setFont(QFont("Arial", 10))
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add labels to layout
        self.layout.addWidget(self.item_name_label)
        self.layout.addWidget(self.price_label)
        
        # Set up fade timer
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.hide)
        
        # Set up display duration
        self.display_duration = 3000  # 3 seconds
        
        # Animation for fading in and out
        self.opacity_effect = None
        self.animations = []
        
        # Size factor (1.0 = 100% of default size)
        self.size_factor = 1.0
        
        # Hide by default
        self.hide()
    
    def set_size_factor(self, factor):
        """Set the size factor for the tooltip (1.0 = 100%)
        
        Args:
            factor (float): Size factor between 0.5 and 2.0
        """
        # Keep factor within reasonable bounds
        factor = max(0.5, min(2.0, factor))
        self.size_factor = factor
        
        # Update font sizes
        name_font = self.item_name_label.font()
        name_font.setPointSize(int(11 * factor))
        self.item_name_label.setFont(name_font)
        
        price_font = self.price_label.font()
        price_font.setPointSize(int(10 * factor))
        self.price_label.setFont(price_font)
        
        # Adjust layout margins
        base_margin = 10
        self.layout.setContentsMargins(
            int(base_margin * factor), 
            int(5 * factor), 
            int(base_margin * factor), 
            int(5 * factor)
        )
    
    def show_tooltip(self, item_name, price, position):
        """Show the tooltip at the specified position
        
        Args:
            item_name (str): Name of the matched item
            price (int): Price of the matched item
            position (QPoint): Position near which to display the tooltip
        """
        # Update the labels
        self.item_name_label.setText(item_name)
        self.price_label.setText(f"Price: {price:,}")
        
        # Size the widget based on contents
        self.adjustSize()
        
        # Calculate position - show above the cursor
        x = position.x() - self.width() // 2
        y = position.y() - self.height() - 20  # 20px above cursor
        
        # Make sure the tooltip doesn't go off screen
        screen_geometry = QApplication.primaryScreen().geometry()
        if x < 0:
            x = 0
        elif x + self.width() > screen_geometry.width():
            x = screen_geometry.width() - self.width()
        
        if y < 0:
            y = position.y() + 20  # Show below cursor if not enough room above
        
        # Set the position
        self.move(x, y)
        
        # Show the tooltip
        self.show()
        
        # Start the fade timer
        self.fade_timer.start(self.display_duration)
