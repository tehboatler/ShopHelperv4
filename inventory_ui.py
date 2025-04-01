"""
Inventory UI Components for MapleLegends ShopHelper
Provides UI elements for inventory management and value tracking
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLineEdit, QDialog, QFormLayout,
    QMessageBox, QSpinBox, QFrame, QSplitter,
    QDialogButtonBox, QMenu, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont, QIntValidator, QAction


class NumericSortItem(QTableWidgetItem):
    """Custom table widget item that sorts correctly for large numeric values"""
    
    def __init__(self, text_value='', sort_value=0):
        super().__init__(text_value)
        self.sort_value = sort_value
        
    def __lt__(self, other):
        """Override less than operator for correct numeric sorting"""
        if isinstance(other, NumericSortItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


class SetStockDialog(QDialog):
    """Dialog for setting or adjusting stock levels"""
    
    def __init__(self, item_name, current_stock=0, item_price=0, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Set Stock Level")
        self.setMinimumWidth(300)
        
        # Apply dark mode to the dialog
        self.setStyleSheet("""
            background-color: #2D2D2D;
            color: #E0E0E0;
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Item name (read-only)
        self.item_label = QLabel(item_name)
        self.item_label.setFont(QFont("Arial", 10))
        form_layout.addRow("Item:", self.item_label)
        
        # Current stock info
        self.current_stock_label = QLabel(f"{current_stock}")
        form_layout.addRow("Current Stock:", self.current_stock_label)
        
        # Item price info
        self.price_label = QLabel(f"{item_price:,}")
        form_layout.addRow("Price per Item:", self.price_label)
        
        # Total value
        total_value = current_stock * item_price
        self.value_label = QLabel(f"{total_value:,}")
        form_layout.addRow("Current Value:", self.value_label)
        
        # New stock value
        self.stock_spinbox = QSpinBox()
        self.stock_spinbox.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.stock_spinbox.setRange(0, 99999)  # Large max value
        self.stock_spinbox.setValue(current_stock)
        self.stock_spinbox.valueChanged.connect(self.update_new_value)
        form_layout.addRow("New Stock:", self.stock_spinbox)
        
        # New total value (updates as stock is changed)
        self.new_value_label = QLabel(f"{total_value:,}")
        self.new_value_label.setStyleSheet("color: #50C878; font-weight: bold;")  # Bright green for value
        form_layout.addRow("New Value:", self.new_value_label)
        
        layout.addLayout(form_layout)
        
        # Adjustment buttons for quick changes
        adjust_layout = QHBoxLayout()
        
        # Add buttons for common adjustments
        adjust_minus_10 = QPushButton("-10")
        adjust_minus_10.setStyleSheet("background-color: #505050; color: #FFFFFF; padding: 3px;")
        adjust_minus_10.clicked.connect(lambda: self.adjust_stock(-10))
        adjust_layout.addWidget(adjust_minus_10)
        
        adjust_minus_1 = QPushButton("-1")
        adjust_minus_1.setStyleSheet("background-color: #505050; color: #FFFFFF; padding: 3px;")
        adjust_minus_1.clicked.connect(lambda: self.adjust_stock(-1))
        adjust_layout.addWidget(adjust_minus_1)
        
        adjust_plus_1 = QPushButton("+1")
        adjust_plus_1.setStyleSheet("background-color: #505050; color: #FFFFFF; padding: 3px;")
        adjust_plus_1.clicked.connect(lambda: self.adjust_stock(1))
        adjust_layout.addWidget(adjust_plus_1)
        
        adjust_plus_10 = QPushButton("+10")
        adjust_plus_10.setStyleSheet("background-color: #505050; color: #FFFFFF; padding: 3px;")
        adjust_plus_10.clicked.connect(lambda: self.adjust_stock(10))
        adjust_layout.addWidget(adjust_plus_10)
        
        layout.addLayout(adjust_layout)
        
        # Store price for calculations
        self.price = item_price
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: #FFFFFF;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
        """)
        
        # Style the OK button with green
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setStyleSheet("""
                background-color: #006600;
                color: #FFFFFF;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            """)
            
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def adjust_stock(self, amount):
        """Adjust the stock by the given amount"""
        current = self.stock_spinbox.value()
        new_value = max(0, current + amount)  # Ensure it doesn't go below 0
        self.stock_spinbox.setValue(new_value)
    
    def update_new_value(self):
        """Update the new value label based on the current stock input"""
        new_stock = self.stock_spinbox.value()
        new_value = new_stock * self.price
        self.new_value_label.setText(f"{new_value:,}")
    
    def get_new_stock(self):
        """Get the new stock value from the dialog"""
        return self.stock_spinbox.value()


class DecrementPriceDialog(QDialog):
    """Dialog for decreasing an item's price by a percentage"""
    
    def __init__(self, item_name, current_price=0, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Decrease Price")
        self.setMinimumWidth(300)
        
        # Apply dark mode to the dialog
        self.setStyleSheet("""
            background-color: #2D2D2D;
            color: #E0E0E0;
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Item name (read-only)
        self.item_label = QLabel(item_name)
        self.item_label.setFont(QFont("Arial", 10))
        form_layout.addRow("Item:", self.item_label)
        
        # Current price info
        self.current_price_label = QLabel(f"{current_price:,}")
        form_layout.addRow("Current Price:", self.current_price_label)
        
        # Percentage to decrease
        self.percentage_spinbox = QSpinBox()
        self.percentage_spinbox.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.percentage_spinbox.setRange(1, 50)  # Allow 1-50% decrease
        self.percentage_spinbox.setValue(1)  # Default to 1%
        self.percentage_spinbox.setSuffix("%")
        self.percentage_spinbox.valueChanged.connect(self.update_new_price)
        form_layout.addRow("Decrease by:", self.percentage_spinbox)
        
        # New price (updates as percentage is changed)
        self.new_price = self.calculate_new_price(current_price, 1)
        self.new_price_label = QLabel(f"{self.new_price:,}")
        self.new_price_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")  # Red for decreased price
        form_layout.addRow("New Price:", self.new_price_label)
        
        # Price difference
        self.price_diff = current_price - self.new_price
        self.diff_label = QLabel(f"-{self.price_diff:,}")
        self.diff_label.setStyleSheet("color: #FF6B6B;")  # Red for decrease
        form_layout.addRow("Difference:", self.diff_label)
        
        layout.addLayout(form_layout)
        
        # Store current price for calculations
        self.current_price = current_price
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: #FFFFFF;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
        """)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def calculate_new_price(self, price, percentage):
        """Calculate new price after percentage decrease"""
        return int(price * (100 - percentage) / 100)
    
    def update_new_price(self):
        """Update the new price label based on the percentage input"""
        percentage = self.percentage_spinbox.value()
        self.new_price = self.calculate_new_price(self.current_price, percentage)
        self.new_price_label.setText(f"{self.new_price:,}")
        
        # Update difference
        self.price_diff = self.current_price - self.new_price
        self.diff_label.setText(f"-{self.price_diff:,}")
    
    def get_new_price(self):
        """Get the new price value from the dialog"""
        return self.new_price


class InventoryWidget(QWidget):
    """Widget for displaying and managing inventory"""
    
    stock_updated = pyqtSignal(str, int)  # Signal when stock is updated (item_name, new_stock)
    item_sold = pyqtSignal(str, int, int)  # Signal when an item is sold (item_name, quantity, selling_price)
    price_updated = pyqtSignal(str, int)  # Signal when price is updated (item_name, new_price)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Apply dark mode to the widget
        self.setStyleSheet("""
            background-color: #2D2D2D;
            color: #E0E0E0;
        """)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Header
        self.header_layout = QHBoxLayout()
        
        # Title
        self.header_label = QLabel("Inventory")
        self.header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.header_layout.addWidget(self.header_label)
        
        # Stats section
        self.stats_layout = QHBoxLayout()
        
        # Inventory stats
        self.total_items_label = QLabel("Total Items: 0")
        self.stats_layout.addWidget(self.total_items_label)
        
        self.items_with_stock_label = QLabel("Items with Stock: 0")
        self.stats_layout.addWidget(self.items_with_stock_label)
        
        self.total_value_label = QLabel("Total Value: 0")
        self.total_value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.total_value_label.setStyleSheet("color: #50C878;")  # Bright green for value
        self.stats_layout.addWidget(self.total_value_label)
        
        # Add stats to header
        self.header_layout.addLayout(self.stats_layout)
        self.header_layout.addStretch()
        
        self.layout.addLayout(self.header_layout)
        
        # Setup the UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Filter layout
        filter_layout = QHBoxLayout()
        
        # Filter label
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)
        
        # Filter field
        self.filter_edit = QLineEdit()
        self.filter_edit.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0; selection-background-color: #505050; padding: 4px;")
        self.filter_edit.setPlaceholderText("Enter item name to filter")
        self.filter_edit.textChanged.connect(self.filter_changed)
        filter_layout.addWidget(self.filter_edit)
        
        # Add filter layout to main layout
        self.layout.addLayout(filter_layout)
        
        # Create inventory table with dark mode styling
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)  # Increased from 5 to 6 for Last Sold column
        self.inventory_table.setHorizontalHeaderLabels(["Item Name", "Price", "Stock", "Value", "Last Sold", "Actions"])
        
        # Dark mode styling for the table
        self.inventory_table.setStyleSheet("""
            QTableWidget {
                background-color: #2D2D2D;
                color: #E0E0E0;
                gridline-color: #555555;
                alternate-background-color: #353535;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3D3D3D;
            }
            QTableWidget::item:selected {
                background-color: #505050;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #3D3D3D;
                color: #E0E0E0;
                padding: 5px;
                border: 1px solid #555555;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #505050;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Set column widths
        self.inventory_table.setColumnWidth(0, 250)  # Item name
        self.inventory_table.setColumnWidth(1, 120)  # Price
        self.inventory_table.setColumnWidth(2, 70)   # Stock
        self.inventory_table.setColumnWidth(3, 120)  # Value
        self.inventory_table.setColumnWidth(4, 100)  # Last Sold
        self.inventory_table.setColumnWidth(5, 100)  # Actions
        
        # Set table properties
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.inventory_table.setAlternatingRowColors(True)
        # Initially disable sorting - will be enabled after data is loaded
        self.inventory_table.setSortingEnabled(False)
        self.inventory_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.inventory_table.horizontalHeader().setSortIndicatorShown(True)
        
        # Connect double-click handler
        self.inventory_table.doubleClicked.connect(self.on_table_double_clicked)
        
        # Set up context menu
        self.inventory_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.inventory_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Add table to layout
        self.layout.addWidget(self.inventory_table)
        
        # Store data
        self.all_data = []
        self.filtered_data = []
    
    def update_inventory(self, inventory_data, stats):
        """Update the inventory table with new data"""
        # Store the original data
        self.all_data = inventory_data
        self.filtered_data = list(inventory_data)  # Make a copy for filtering
        
        # Update stats
        self.update_stats(stats)
        
        # Reapply any current filter
        self.filter_changed()
    
    def filter_changed(self):
        """Filter items based on the search text"""
        filter_text = self.filter_edit.text().lower()
        
        # First filter by text
        if filter_text:
            self.filtered_data = [
                item for item in self.all_data
                if filter_text in item['name'].lower()
            ]
        else:
            self.filtered_data = list(self.all_data)
        
        # Update display
        self.update_table()
    
    def update_table(self):
        """Update the table with filtered data"""
        self.inventory_table.setSortingEnabled(False)  # Disable sorting while updating
        self.inventory_table.setRowCount(len(self.filtered_data))
        
        total_value = 0
        items_with_stock = 0
        
        for i, item in enumerate(self.filtered_data):
            name = item.get('name', '')
            price = item.get('price', 0)
            stock = item.get('stock', 0)
            value = price * stock
            total_value += value
            
            if stock > 0:
                items_with_stock += 1
                
            # Check if price reduction is recommended
            price_adjustment = item.get('price_adjustment', {})
            price_reduction_recommended = price_adjustment.get('recommended', False)
            
            # Item name column
            name_item = QTableWidgetItem(name)
            
            # Store the original index in the filtered_data list as user data
            name_item.setData(Qt.ItemDataRole.UserRole, i)
            
            # Mark item name if price adjustment is recommended
            if price_reduction_recommended:
                name_item.setForeground(QColor(255, 200, 0))  # Amber color for items that need price adjustment
                # Add a small indicator
                name_with_indicator = f"⚠ {name}"  
                name_item.setText(name_with_indicator)
                
                # Set tooltip with recommendation details
                reason = price_adjustment.get('reason', '')
                suggested_price = price_adjustment.get('suggested_price', price)
                days = int(price_adjustment.get('last_sale_days', 0))
                
                tooltip = (f"Price reduction recommended: {reason}\n"
                          f"Current price: {format(price, ',')}\n"
                          f"Suggested price: {format(suggested_price, ',')}\n"
                          f"Days since last sale: {days}")
                name_item.setToolTip(tooltip)
            
            self.inventory_table.setItem(i, 0, name_item)
            
            # Price column with number formatting using custom sorting item
            price_text = format(price, ",")
            if price_reduction_recommended:
                # Display just the current price, but keep the yellow highlighting
                price_item = NumericSortItem(price_text, price)
                price_item.setForeground(QColor(255, 200, 0))  # Amber color
                font = QFont()
                font.setBold(True)
                price_item.setFont(font)
            else:
                price_item = NumericSortItem(price_text, price)
                price_item.setForeground(QColor(150, 200, 255))  # Light blue for prices
                
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.inventory_table.setItem(i, 1, price_item)
            
            # Stock column using custom sorting item
            stock_text = str(stock)
            stock_item = NumericSortItem(stock_text, stock)
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Color code stock values
            if stock > 0:
                if price_reduction_recommended:
                    stock_item.setForeground(QColor(255, 200, 0))  # Amber
                else:
                    stock_item.setForeground(QColor(80, 200, 120))  # Bright green
                
                font = QFont()
                font.setBold(True)
                stock_item.setFont(font)
            
            self.inventory_table.setItem(i, 2, stock_item)
            
            # Value column with number formatting using custom sorting item
            value_text = format(value, ",")
            value_item = NumericSortItem(value_text, value)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Style based on stock
            if stock > 0:
                if price_reduction_recommended:
                    # Show value in amber for price reduction items
                    value_item.setForeground(QColor(255, 200, 0))  # Amber
                else:
                    value_item.setForeground(QColor(150, 255, 150))  # Light green for normal value
                
                font = QFont()
                font.setBold(True)
                value_item.setFont(font)
            
            self.inventory_table.setItem(i, 3, value_item)
            
            # Last Sold column
            last_sold_text = item.get('last_sold', '')
            last_sold_item = QTableWidgetItem(last_sold_text)
            last_sold_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.inventory_table.setItem(i, 4, last_sold_item)
            
            # Add sell button to Actions column
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(2, 2, 2, 2)
            
            # Create sell button with dark mode styling
            sell_button = QPushButton("Sell")
            sell_button.setStyleSheet("""
                background-color: #006600; 
                color: white; 
                font-weight: bold; 
                padding: 3px;
                border: none;
                border-radius: 3px;
            """)
            sell_button.setFixedSize(60, 25)
            
            # Connect button to function with row information
            sell_button.clicked.connect(lambda checked=False, row=i: self.show_mark_as_sold_dialog(row))
            
            # Add button to layout and layout to widget
            layout.addWidget(sell_button)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widget.setLayout(layout)
            
            # Set the widget in the table
            self.inventory_table.setCellWidget(i, 5, widget)
        
        # Update stats
        stats = {
            'total_items': len(self.filtered_data),
            'items_with_stock': items_with_stock,
            'total_value': total_value
        }
        self.update_stats(stats)
        
        # Re-enable sorting and set default sort to value column (descending)
        self.inventory_table.setSortingEnabled(True)
        self.inventory_table.horizontalHeader().setSortIndicator(3, Qt.SortOrder.DescendingOrder)
    
    def update_stats(self, stats):
        """Update the inventory statistics display"""
        total_items = stats.get('total_items', 0)
        items_with_stock = stats.get('items_with_stock', 0)
        total_value = stats.get('total_value', 0)
        
        self.total_items_label.setText(f"Total Items: {total_items}")
        self.items_with_stock_label.setText(f"Items with Stock: {items_with_stock}")
        self.total_value_label.setText(f"Total Value: {total_value:,}")
    
    def show_context_menu(self, position):
        """Show context menu for the inventory table"""
        # Get the row at the position
        index = self.inventory_table.indexAt(position)
        if not index.isValid():
            return
            
        # Get the row index in the table
        row = index.row()
        
        # Get the original index from the UserRole data in the first column
        item = self.inventory_table.item(row, 0)
        if not item:
            return
            
        # Get the original index in filtered_data that we stored in UserRole
        original_index = item.data(Qt.ItemDataRole.UserRole)
        
        # Create menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #3D3D3D;
                color: #E0E0E0;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
        """)
        
        # Add actions if we have a valid row
        if original_index is not None and original_index >= 0 and original_index < len(self.filtered_data):
            # Get stock
            stock = self.filtered_data[original_index].get('stock', 0)
            
            # Set stock action
            set_stock_action = QAction("Set Stock Level...", self)
            set_stock_action.triggered.connect(lambda: self.open_set_stock_dialog(original_index))
            menu.addAction(set_stock_action)
            
            # Mark as sold action (only if there's stock)
            if stock > 0:
                mark_sold_action = QAction("Mark as Sold...", self)
                mark_sold_action.triggered.connect(lambda: self.show_mark_as_sold_dialog(original_index))
                menu.addAction(mark_sold_action)
            
            # Add separator
            menu.addSeparator()
            
            # Decrease price action
            decrease_price_action = QAction("Decrease Price by %...", self)
            decrease_price_action.triggered.connect(lambda: self.show_decrease_price_dialog(original_index))
            menu.addAction(decrease_price_action)
            
        # Show the menu
        menu.exec(self.inventory_table.mapToGlobal(position))
    
    def open_set_stock_dialog(self, row):
        """Open dialog to set stock for an item"""
        if row >= 0 and row < len(self.filtered_data):
            item = self.filtered_data[row]
            item_name = item.get('name', '')
            current_stock = item.get('stock', 0)
            price = item.get('price', 0)
            
            # Open dialog
            dialog = SetStockDialog(item_name, current_stock, price, self)
            if dialog.exec():
                new_stock = dialog.get_new_stock()
                if new_stock != current_stock:
                    # Emit signal to update stock
                    self.stock_updated.emit(item_name, new_stock)
    
    def show_mark_as_sold_dialog(self, row):
        """Show dialog to mark item as sold"""
        if row >= 0 and row < len(self.filtered_data):
            item = self.filtered_data[row]
            item_name = item.get('name', '')
            current_stock = item.get('stock', 0)
            price = item.get('price', 0)
            
            # Only show dialog if there's stock to sell
            if current_stock <= 0:
                return
                
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Mark Item as Sold")
            dialog.setMinimumWidth(350)
            
            # Apply dark mode to dialog
            dialog.setStyleSheet("""
                background-color: #2D2D2D;
                color: #E0E0E0;
            """)
            
            # Create layout
            layout = QVBoxLayout(dialog)
            
            # Add information labels
            layout.addWidget(QLabel(f"<b>{item_name}</b>"))
            layout.addWidget(QLabel(f"Current Stock: {current_stock}"))
            layout.addWidget(QLabel(f"Default Price per Unit: {price:,}"))
            
            # Quantity selector
            quantity_layout = QHBoxLayout()
            quantity_layout.addWidget(QLabel("Quantity to Sell:"))
            quantity_spinner = QSpinBox()
            quantity_spinner.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
            quantity_spinner.setMinimum(1)
            quantity_spinner.setMaximum(current_stock)  # Cannot sell more than current stock
            quantity_spinner.setValue(1)  # Default to 1
            quantity_layout.addWidget(quantity_spinner)
            layout.addLayout(quantity_layout)
            
            # Price selector
            price_layout = QHBoxLayout()
            price_layout.addWidget(QLabel("Selling Price per Unit:"))
            price_edit = QLineEdit()
            price_edit.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
            price_edit.setText(str(price))  # Default to item's price
            # Only allow integers or empty field
            price_validator = QIntValidator()
            price_validator.setBottom(0)  # Only allow positive prices
            price_edit.setValidator(price_validator)
            price_layout.addWidget(price_edit)
            layout.addLayout(price_layout)
            
            # Show total value
            value_label = QLabel(f"Total Sale Value: {price:,}")
            value_label.setStyleSheet("color: #50C878; font-weight: bold;")  # Bright green for value
            layout.addWidget(value_label)
            
            # Update total value when quantity or price changes
            def update_value():
                quantity = quantity_spinner.value()
                try:
                    selling_price = int(price_edit.text()) if price_edit.text() else 0
                    value = quantity * selling_price
                    value_label.setText(f"Total Sale Value: {value:,}")
                except ValueError:
                    value_label.setText("Total Sale Value: Invalid price")
            
            quantity_spinner.valueChanged.connect(update_value)
            price_edit.textChanged.connect(update_value)
            
            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                         QDialogButtonBox.StandardButton.Cancel)
            button_box.setStyleSheet("""
                QPushButton {
                    background-color: #505050;
                    color: #FFFFFF;
                    padding: 5px 15px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #606060;
                }
                QPushButton:pressed {
                    background-color: #404040;
                }
            """)
            
            # Style the OK button with green
            ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button:
                ok_button.setStyleSheet("""
                    background-color: #006600;
                    color: #FFFFFF;
                    padding: 5px 15px;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                """)
                
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # Show dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                quantity = quantity_spinner.value()
                try:
                    selling_price = int(price_edit.text()) if price_edit.text() else price
                    self.mark_as_sold(row, quantity, selling_price)
                except ValueError:
                    # If price is invalid, use the default price
                    self.mark_as_sold(row, quantity, price)
                
    def mark_as_sold(self, row, quantity, selling_price=None):
        """Mark item as sold, reducing stock by the given quantity"""
        if row >= 0 and row < len(self.filtered_data):
            item = self.filtered_data[row]
            item_name = item.get('name', '')
            current_stock = item.get('stock', 0)
            default_price = item.get('price', 0)
            
            # If no selling price specified, use the default price
            if selling_price is None:
                selling_price = default_price
                
            # Ensure quantity is valid
            quantity = min(current_stock, max(1, quantity))
            
            if quantity > 0 and quantity <= current_stock:
                # Calculate new stock
                new_stock = current_stock - quantity
                
                # Update the filtered data
                self.filtered_data[row]['stock'] = new_stock
                
                # Emit signal with item name, quantity and selling price
                self.item_sold.emit(item_name, quantity, selling_price)
                
                # Refresh the table to ensure correct display
                self.update_table()

    def show_decrease_price_dialog(self, row):
        """Show dialog to decrease item price by percentage"""
        if row >= 0 and row < len(self.filtered_data):
            item = self.filtered_data[row]
            item_name = item.get('name', '')
            current_price = item.get('price', 0)
            
            # Open dialog
            dialog = DecrementPriceDialog(item_name, current_price, self)
            if dialog.exec():
                new_price = dialog.get_new_price()
                if new_price != current_price:
                    # Emit signal to update price
                    self.price_updated.emit(item_name, new_price)

    def on_table_double_clicked(self, index):
        """Handle double-click on an inventory item"""
        row = index.row()
        
        # Get the original index from the UserRole data in the first column
        item = self.inventory_table.item(row, 0)
        if not item:
            return
            
        # Get the original index in filtered_data that we stored in UserRole
        original_index = item.data(Qt.ItemDataRole.UserRole)
        
        if original_index is not None and original_index >= 0 and original_index < len(self.filtered_data):
            self.open_set_stock_dialog(original_index)
