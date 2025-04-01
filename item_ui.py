"""
Item UI Components for MapleLegends ShopHelper
Provides UI elements for item management and logging
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction, QFont, QIntValidator

import time
from datetime import datetime

class CorrectMatchDialog(QDialog):
    """Dialog for correcting a mismatched item"""
    
    def __init__(self, ocr_text, original_match=None, original_price=None, item_list=None, parent=None):
        super().__init__(parent)
        
        self.item_list = item_list or []
        self.setWindowTitle("Correct Item Match")
        self.setMinimumWidth(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # OCR Text (read-only)
        self.ocr_label = QLabel(ocr_text)
        self.ocr_label.setFont(QFont("Arial", 10))
        form_layout.addRow("OCR Text:", self.ocr_label)
        
        # Original match (read-only)
        match_text = original_match or "No match"
        self.original_match_label = QLabel(match_text)
        form_layout.addRow("Original Match:", self.original_match_label)
        
        # Correct item field - initialize with OCR text instead of original match for convenience
        self.item_edit = QLineEdit()
        self.item_edit.setText(ocr_text)  # Use OCR text as default for easier editing
        form_layout.addRow("Correct Item:", self.item_edit)
        
        # Price field - use QLineEdit instead of QSpinBox for unlimited range
        self.price_edit = QLineEdit()
        # Set validator to only accept integers
        self.price_edit.setValidator(QIntValidator(0, 2147483647))
        if original_price:
            self.price_edit.setText(str(original_price))
        else:
            self.price_edit.setText("0")
        form_layout.addRow("Price:", self.price_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_values(self):
        """Get the values from the dialog"""
        # Convert price to int, default to 0 if conversion fails
        try:
            price = int(self.price_edit.text())
        except ValueError:
            price = 0
            
        return {
            'item_name': self.item_edit.text(),
            'price': price
        }


class RecentlyLoggedWidget(QWidget):
    """Widget for displaying recently logged items"""
    
    item_corrected = pyqtSignal(int, object)  # Signal when item is corrected
    stock_updated = pyqtSignal(str, int)  # Signal when stock is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Header
        self.header_label = QLabel("Recently Logged Items")
        self.header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.header_label)
        
        # Log table
        self.log_table = QTableWidget(0, 6)  # 0 rows, 6 columns
        self.log_table.setHorizontalHeaderLabels(["OCR Text", "Matched Item", "Price", "Stock", "Confidence", "Time"])
        
        # Configure column sizes
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # OCR Text
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Matched Item
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Price
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Stock
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Confidence
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Time
        
        # Connect double-click and context menu
        self.log_table.doubleClicked.connect(self.on_table_double_clicked)
        self.log_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.log_table.customContextMenuRequested.connect(self.show_context_menu)
        
        self.layout.addWidget(self.log_table)
        
        # Store original log data
        self.log_data = []
    
    def update_log(self, log_data):
        """Update the log table with new data"""
        # Store the original data
        self.log_data = log_data
        
        # Clear existing log
        self.log_table.setRowCount(0)
        
        # Add new log data
        for i, entry in enumerate(log_data):
            self.log_table.insertRow(i)
            
            # OCR Text column
            ocr_text = entry.get('ocr_text', '')
            if ocr_text:
                ocr_item = QTableWidgetItem(ocr_text)
                self.log_table.setItem(i, 0, ocr_item)
            
            # Matched Item column
            matched_item = entry.get('matched_item')
            if matched_item:
                match_item = QTableWidgetItem(matched_item)
                self.log_table.setItem(i, 1, match_item)
            else:
                not_found_item = QTableWidgetItem("Not found")
                not_found_item.setForeground(QColor(150, 150, 150))  # Gray text
                self.log_table.setItem(i, 1, not_found_item)
            
            # Price column
            price = entry.get('price')
            if price is not None:
                # Ensure price is an integer or float before formatting
                if isinstance(price, (int, float)):
                    price_item = QTableWidgetItem(f"{price:,}")
                else:
                    # If it's not a number, convert to string
                    price_item = QTableWidgetItem(str(price))
                self.log_table.setItem(i, 2, price_item)
            else:
                price_item = QTableWidgetItem("")
                self.log_table.setItem(i, 2, price_item)
                
            # Stock column (getting from item_database via additional data in entry)
            stock = entry.get('stock', 0)
            if stock > 0:
                stock_item = QTableWidgetItem(str(stock))
                # Improved contrast: darker green background with black text for better readability
                stock_item.setBackground(QColor(150, 215, 150))
                stock_item.setForeground(QColor(0, 0, 0))  # Black text for better contrast
                # Make text bold for emphasis
                font = stock_item.font()
                font.setBold(True)
                stock_item.setFont(font)
            else:
                stock_item = QTableWidgetItem("0")
                # Improved contrast: lighter gray with darker gray text
                stock_item.setBackground(QColor(240, 240, 240))
                stock_item.setForeground(QColor(80, 80, 80))  # Dark gray text for better contrast
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(i, 3, stock_item)
            
            # Confidence column
            match_score = entry.get('match_score')
            if match_score is not None:
                conf_item = QTableWidgetItem(f"{match_score:.1f}%")
                
                # Color-code confidence levels with improved contrast
                if match_score > 90:
                    # Darker green for high confidence
                    conf_item.setBackground(QColor(150, 220, 150))
                    conf_item.setForeground(QColor(0, 80, 0))  # Dark green text
                elif match_score > 75:
                    # Darker yellow for medium confidence
                    conf_item.setBackground(QColor(240, 230, 140))
                    conf_item.setForeground(QColor(100, 80, 0))  # Dark yellow text
                else:
                    # Darker red for low confidence
                    conf_item.setBackground(QColor(255, 160, 160))
                    conf_item.setForeground(QColor(140, 0, 0))  # Dark red text
                
                self.log_table.setItem(i, 4, conf_item)
            else:
                self.log_table.setItem(i, 4, QTableWidgetItem(""))
            
            # Time column
            timestamp = entry.get('timestamp')
            if timestamp:
                time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                time_item = QTableWidgetItem(time_str)
                self.log_table.setItem(i, 5, time_item)
    
    def on_table_double_clicked(self, index):
        """Handle double-click on a log entry"""
        row = index.row()
        column = index.column()
        
        if row >= 0 and row < len(self.log_data):
            log_entry = self.log_data[row]
            
            # If clicked on the stock column (column 3), open stock dialog
            if column == 3 and log_entry.get('matched_item'):
                self.open_stock_dialog(row)
            # Otherwise open correction dialog
            elif log_entry.get('matched_item'):
                self.open_correction_dialog(row)
    
    def show_context_menu(self, position):
        """Show context menu for the table"""
        menu = QMenu()
        
        # Get the row under the cursor
        row = self.log_table.rowAt(position.y())
        
        if row >= 0 and row < len(self.log_data):
            log_entry = self.log_data[row]
            
            # Only show appropriate options if there's a matched item
            if log_entry.get('matched_item'):
                # Correct match action
                correct_action = QAction("Correct Match...", self)
                correct_action.triggered.connect(lambda: self.open_correction_dialog(row))
                menu.addAction(correct_action)
                
                # Add action to update stock
                menu.addSeparator()
                set_stock_action = QAction("Set Stock...", self)
                set_stock_action.triggered.connect(lambda: self.open_stock_dialog(row))
                menu.addAction(set_stock_action)
                
                # Quick stock actions
                add_stock_action = QAction("Add 1 to Stock", self)
                add_stock_action.triggered.connect(lambda: self.quick_adjust_stock(row, 1))
                menu.addAction(add_stock_action)
                
                remove_stock_action = QAction("Remove 1 from Stock", self)
                remove_stock_action.triggered.connect(lambda: self.quick_adjust_stock(row, -1))
                menu.addAction(remove_stock_action)
            
            # Show the menu
            menu.exec(self.log_table.mapToGlobal(position))
            
    def open_stock_dialog(self, row):
        """Open dialog to set stock for the matched item in a log entry"""
        if row >= 0 and row < len(self.log_data):
            log_entry = self.log_data[row]
            matched_item = log_entry.get('matched_item')
            
            if matched_item:
                # Import the dialog here to avoid circular imports
                from inventory_ui import SetStockDialog
                
                # Get price from log entry
                price = log_entry.get('price', 0)
                
                # Get current stock from log entry
                current_stock = log_entry.get('stock', 0)
                
                # Show dialog with current stock
                dialog = SetStockDialog(matched_item, current_stock, price, self)
                if dialog.exec():
                    new_stock = dialog.get_new_stock()
                    # Emit signal to update stock
                    self.stock_updated.emit(matched_item, new_stock)
    
    def quick_adjust_stock(self, row, adjustment):
        """Quickly adjust stock without opening dialog"""
        if row >= 0 and row < len(self.log_data):
            log_entry = self.log_data[row]
            matched_item = log_entry.get('matched_item')
            
            if matched_item:
                # Get current stock from log entry
                current_stock = log_entry.get('stock', 0)
                
                # Calculate new stock (ensure it doesn't go below 0)
                new_stock = max(0, current_stock + adjustment)
                
                # Only emit if there's a change
                if new_stock != current_stock:
                    # Emit signal to update stock
                    self.stock_updated.emit(matched_item, new_stock)
                    
                    # Update the stock in the table UI directly for immediate feedback
                    stock_item = self.log_table.item(row, 3)  # Stock is in column 3
                    if stock_item:
                        stock_item.setText(str(new_stock))
                        if new_stock > 0:
                            # Improved contrast: darker green background with black text
                            stock_item.setBackground(QColor(150, 215, 150))
                            stock_item.setForeground(QColor(0, 0, 0))  # Black text
                            # Make text bold
                            font = stock_item.font()
                            font.setBold(True)
                            stock_item.setFont(font)
                        else:
                            # Improved contrast: lighter gray with darker gray text
                            stock_item.setBackground(QColor(240, 240, 240))
                            stock_item.setForeground(QColor(80, 80, 80))  # Dark gray text
                            # Remove bold
                            font = stock_item.font()
                            font.setBold(False)
                            stock_item.setFont(font)
    
    def open_correction_dialog(self, row_index):
        """Open a dialog to correct a mismatched item"""
        if 0 <= row_index < len(self.log_data):
            entry = self.log_data[row_index]
            ocr_text = entry.get('ocr_text', '')
            matched_item = entry.get('matched_item')
            price = entry.get('price')
            
            # Create and show correction dialog
            dialog = CorrectMatchDialog(ocr_text, matched_item, price, parent=self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get new values
                values = dialog.get_values()
                
                # Emit signal with the row index and new values
                self.item_corrected.emit(row_index, values)


class AddItemDialog(QDialog):
    """Dialog for adding a new item to the database"""
    
    def __init__(self, ocr_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Item")
        self.setMinimumWidth(400)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Ensure ocr_text is a string
        if ocr_text is None or not isinstance(ocr_text, str):
            ocr_text = ""
            
        # Item name field
        self.name_edit = QLineEdit(ocr_text)
        form_layout.addRow("Item Name:", self.name_edit)
        
        # Price field - use QLineEdit instead of QSpinBox for unlimited range
        self.price_edit = QLineEdit("0")
        # Set validator to only accept integers (up to max 32-bit int, but can be modified for large values)
        self.price_edit.setValidator(QIntValidator(0, 2147483647))
        form_layout.addRow("Price:", self.price_edit)
        
        self.layout.addLayout(form_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        self.layout.addLayout(buttons_layout)
    
    def get_item_data(self):
        """Get the item data from the dialog"""
        # Convert price to int, default to 0 if conversion fails
        try:
            price = int(self.price_edit.text())
        except ValueError:
            price = 0
            
        return {
            'name': self.name_edit.text(),
            'price': price
        }


class ItemDatabaseWidget(QWidget):
    """Widget for managing the item database"""
    
    item_added = pyqtSignal(str, int)  # name, price
    item_edited = pyqtSignal(str, str, int)  # original_name, new_name, price
    item_deleted = pyqtSignal(str)  # name
    search_requested = pyqtSignal(str)  # search query
    stock_updated = pyqtSignal(str, int)  # Signal when stock is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Header
        self.header_label = QLabel("Item Database")
        self.header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.header_label)
        
        # Search layout
        search_layout = QHBoxLayout()
        
        # Search label
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)
        
        # Search field
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter item name to search")
        self.search_edit.textChanged.connect(self.search_items)
        search_layout.addWidget(self.search_edit)
        
        self.layout.addLayout(search_layout)
        
        # Table for items
        self.table = QTableWidget(0, 3)  # rows, columns
        self.table.setHorizontalHeaderLabels(["Item Name", "Price", "Last Updated"])
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Item Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Price
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Last Updated
        
        self.layout.addWidget(self.table)
        
        # Store the complete dataset and fuzzy search results
        self.all_items = {}
        self.filtered_items = {}
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add item button
        self.add_button = QPushButton("Add Item")
        self.add_button.clicked.connect(self.add_item)
        buttons_layout.addWidget(self.add_button)
        
        # Edit item button
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_item)
        buttons_layout.addWidget(self.edit_button)
        
        # Delete item button
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_item)
        buttons_layout.addWidget(self.delete_button)
        
        # Add to layout
        self.layout.addLayout(buttons_layout)
        
        # Stats label
        self.stats_label = QLabel("Database Statistics")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.stats_label)
    
    def update_items(self, items):
        """Update the items table with the provided items"""
        # Store the complete dataset
        self.all_items = items
        
        # Apply any active search filter
        if self.search_edit.text().strip():
            self.search_items()
        else:
            # No active search, show all items
            self.filtered_items = self.all_items
            self.display_items(self.filtered_items)
    
    def display_items(self, items_to_display):
        """Display the specified items in the table"""
        # Clear the table
        self.table.setRowCount(0)
        
        # Add items
        for i, (name, data) in enumerate(items_to_display.items()):
            self.table.insertRow(i)
            
            # Item Name
            name_item = QTableWidgetItem(name)
            self.table.setItem(i, 0, name_item)
            
            # Price - handle both dictionary and direct integer formats
            if isinstance(data, dict):
                price = data.get('price', 0)
            else:
                # Handle case where data is directly a price (integer)
                price = data
                
            price_item = QTableWidgetItem(f"{price:,}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, price_item)
            
            # Last Updated
            if isinstance(data, dict):
                last_updated = data.get('last_updated', data.get('added_date', 0))
                if last_updated:
                    date_str = datetime.fromtimestamp(last_updated).strftime('%Y-%m-%d %H:%M')
                    date_item = QTableWidgetItem(date_str)
                else:
                    date_item = QTableWidgetItem("Unknown")
            else:
                # No timestamp for direct integer price
                date_item = QTableWidgetItem("Unknown")
            
            self.table.setItem(i, 2, date_item)
    
    def update_stats(self, stats):
        """Update the database statistics"""
        stats_text = f"Total Items: {stats['total_items']} | "
        stats_text += f"Avg Price: {stats['avg_price']:,.0f} | "
        stats_text += f"Range: {stats['min_price']:,} - {stats['max_price']:,}"
        
        self.stats_label.setText(stats_text)
    
    def search_items(self):
        """Search items in the database"""
        query = self.search_edit.text().strip()
        
        if not query:
            # Empty query, show all items
            self.filtered_items = self.all_items
        else:
            # Emit signal for the search (will be connected to the actual search method)
            self.search_requested.emit(query)
        
        # Show the filtered items
        self.display_items(self.filtered_items)
    
    def update_search_results(self, search_results):
        """Update the table with search results"""
        # Convert search results to the format needed for display
        self.filtered_items = {}
        for result in search_results:
            name = result.get('name')
            if name:
                # Use the original item data from all_items
                self.filtered_items[name] = self.all_items.get(name, {})
        
        # Display the filtered items
        self.display_items(self.filtered_items)
    
    def add_item(self, ocr_text=None):
        """Add a new item to the database"""
        # Ensure ocr_text is a string
        if ocr_text is None:
            ocr_text = ""
        elif not isinstance(ocr_text, str):
            ocr_text = str(ocr_text)
            
        dialog = AddItemDialog(ocr_text, self)
        if dialog.exec():
            item_data = dialog.get_item_data()
            self.item_added.emit(item_data['name'], item_data['price'])
    
    def edit_item(self):
        """Edit the selected item"""
        # Get selected row
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select an item to edit.")
            return
        
        # Get item name and price from the selected row
        row = selected_rows[0].row()
        original_name = self.table.item(row, 0).text()
        price_text = self.table.item(row, 1).text().replace(',', '')
        
        # Create dialog with item data
        dialog = AddItemDialog(original_name, self)
        dialog.setWindowTitle("Edit Item")
        try:
            dialog.price_edit.setText(price_text)
        except ValueError:
            dialog.price_edit.setText("0")
        
        # Show dialog
        if dialog.exec():
            item_data = dialog.get_item_data()
            self.item_edited.emit(original_name, item_data['name'], item_data['price'])
    
    def delete_item(self):
        """Delete the selected item"""
        # Get selected row
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select an item to delete.")
            return
        
        # Get item name from the selected row
        row = selected_rows[0].row()
        item_name = self.table.item(row, 0).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Signal deletion
            self.item_deleted.emit(item_name)
    
    def show_context_menu(self, position):
        """Show a context menu for the table"""
        menu = QMenu()
        
        # Get the row under the cursor
        row = self.table.rowAt(position.y())
        
        if row >= 0:
            # Get the item name from the first column
            item_name = self.table.item(row, 0).text()
            
            # Edit action
            edit_action = QAction("Edit Item", self)
            edit_action.triggered.connect(lambda: self.edit_specific_item(item_name))
            menu.addAction(edit_action)
            
            # Delete action
            delete_action = QAction("Delete Item", self)
            delete_action.triggered.connect(lambda: self.delete_specific_item(item_name))
            menu.addAction(delete_action)
            
            # Add stock management actions
            menu.addSeparator()
            
            # Set stock action
            set_stock_action = QAction("Set Stock...", self)
            set_stock_action.triggered.connect(lambda: self.open_stock_dialog(item_name))
            menu.addAction(set_stock_action)
            
            # Quick stock actions
            add_stock_action = QAction("Add 1 to Stock", self)
            add_stock_action.triggered.connect(lambda: self.quick_adjust_stock(item_name, 1))
            menu.addAction(add_stock_action)
            
            remove_stock_action = QAction("Remove 1 from Stock", self)
            remove_stock_action.triggered.connect(lambda: self.quick_adjust_stock(item_name, -1))
            menu.addAction(remove_stock_action)
            
            # Show the context menu
            menu.exec(self.table.mapToGlobal(position))
            
    def open_stock_dialog(self, item_name):
        """Open dialog to set stock for an item"""
        if item_name in self.all_items:
            # Import the dialog here to avoid circular imports
            from inventory_ui import SetStockDialog
            
            # Get current item data
            item_data = self.all_items[item_name]
            current_stock = item_data.get('stock', 0)
            price = item_data.get('price', 0)
            
            # Show dialog
            dialog = SetStockDialog(item_name, current_stock, price, self)
            if dialog.exec():
                new_stock = dialog.get_new_stock()
                # Emit signal to update stock
                self.stock_updated.emit(item_name, new_stock)
    
    def quick_adjust_stock(self, item_name, adjustment):
        """Quickly adjust stock without opening dialog"""
        if item_name in self.all_items:
            # Get current stock
            current_stock = self.all_items[item_name].get('stock', 0)
            
            # Calculate new stock (prevent negative)
            new_stock = max(0, current_stock + adjustment)
            
            # Only emit if there's a real change
            if new_stock != current_stock:
                self.stock_updated.emit(item_name, new_stock)
