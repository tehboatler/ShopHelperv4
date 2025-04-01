from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QComboBox, QLabel,
                             QPushButton, QSpinBox, QDateEdit, QMenu, QSplitter,
                             QLineEdit, QGroupBox, QFormLayout, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QColor, QBrush, QFont, QAction, QIntValidator
import time
from datetime import datetime, timedelta
from ledger_charts import LedgerChartWidget
from cash_balance import CashManager

class CashEntryDialog(QDialog):
    """Dialog for entering cash transactions"""
    
    def __init__(self, current_balance=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cash Transaction")
        self.setMinimumWidth(300)
        self.setStyleSheet("background-color: #2D2D2D; color: #E0E0E0;")
        
        # Store current balance
        self.current_balance = current_balance
        
        # Set up the UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout(self)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        
        # Transaction type
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.type_combo.addItem("Add Cash", "add")
        self.type_combo.addItem("Withdraw Cash", "withdraw")
        self.type_combo.addItem("Set Balance", "set")
        self.type_combo.currentIndexChanged.connect(self.update_description)
        form_layout.addRow("Transaction Type:", self.type_combo)
        
        # Amount input
        self.amount_input = QLineEdit()
        self.amount_input.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.amount_input.setValidator(QIntValidator(0, 999999999))  # Only allow positive integers
        form_layout.addRow("Amount:", self.amount_input)
        
        # Description input
        self.description_input = QLineEdit()
        self.description_input.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        form_layout.addRow("Description:", self.description_input)
        
        # Current balance display
        self.balance_label = QLabel(f"Current Balance: {self.current_balance:,}")
        self.balance_label.setStyleSheet("font-weight: bold; color: #FFD700;")
        
        # New balance preview
        self.new_balance_label = QLabel(f"New Balance: {self.current_balance:,}")
        self.new_balance_label.setStyleSheet("font-weight: bold; color: #50C878;")
        
        # Connect amount input to update new balance preview
        self.amount_input.textChanged.connect(self.update_balance_preview)
        
        # Add form to layout
        layout.addLayout(form_layout)
        layout.addWidget(self.balance_label)
        layout.addWidget(self.new_balance_label)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: #FFFFFF;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
        """)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set default description
        self.update_description()
        
    def update_description(self):
        """Update description based on transaction type"""
        tx_type = self.type_combo.currentData()
        
        if tx_type == "add":
            self.description_input.setText("Added cash")
        elif tx_type == "withdraw":
            self.description_input.setText("Withdrew cash")
        else:  # set
            self.description_input.setText("Set cash balance")
            
    def update_balance_preview(self):
        """Update the new balance preview based on amount and transaction type"""
        try:
            amount = int(self.amount_input.text() or "0")
            tx_type = self.type_combo.currentData()
            
            if tx_type == "add":
                new_balance = self.current_balance + amount
            elif tx_type == "withdraw":
                new_balance = self.current_balance - amount
            else:  # set
                new_balance = amount
                
            self.new_balance_label.setText(f"New Balance: {new_balance:,}")
        except ValueError:
            self.new_balance_label.setText(f"New Balance: {self.current_balance:,}")
            
    def get_transaction_data(self):
        """Get the transaction data from the dialog
        
        Returns:
            Dictionary with transaction data or None if invalid
        """
        try:
            amount = int(self.amount_input.text() or "0")
            if amount <= 0:
                return None
                
            tx_type = self.type_combo.currentData()
            description = self.description_input.text()
            
            if tx_type == "add":
                new_balance = self.current_balance + amount
                value = amount
            elif tx_type == "withdraw":
                new_balance = self.current_balance - amount
                value = -amount
            else:  # set
                new_balance = amount
                value = new_balance - self.current_balance
                
            return {
                "type": tx_type,
                "amount": amount,
                "description": description,
                "new_balance": new_balance,
                "value": value,
                "timestamp": time.time()
            }
        except ValueError:
            return None

class PurchaseDialog(QDialog):
    """Dialog for purchasing items with cash"""
    
    def __init__(self, item_name, price, current_cash, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Purchase Item")
        self.setMinimumWidth(350)
        self.setStyleSheet("background-color: #2D2D2D; color: #E0E0E0;")
        
        # Store item details
        self.item_name = item_name
        self.price = price
        self.current_cash = current_cash
        
        # Set up the UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        
        # Item name (non-editable)
        self.name_label = QLineEdit(self.item_name)
        self.name_label.setReadOnly(True)
        self.name_label.setStyleSheet("background-color: #3D3D3D;")
        form_layout.addRow("Item:", self.name_label)
        
        # Price (non-editable)
        self.price_label = QLineEdit(f"{self.price:,}")
        self.price_label.setReadOnly(True)
        self.price_label.setStyleSheet("background-color: #3D3D3D;")
        form_layout.addRow("Price:", self.price_label)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setStyleSheet("background-color: #3D3D3D;")
        self.quantity_spin.valueChanged.connect(self.update_total)
        form_layout.addRow("Quantity:", self.quantity_spin)
        
        # Total cost
        self.total_label = QLabel(f"Total Cost: {self.price:,}")
        self.total_label.setStyleSheet("font-weight: bold; color: #4B9CD3;")
        form_layout.addRow("", self.total_label)
        
        # Current cash balance
        self.cash_label = QLabel(f"Current Cash: {self.current_cash:,}")
        self.cash_label.setStyleSheet("font-weight: bold; color: #FFD700;")
        form_layout.addRow("", self.cash_label)
        
        # Remaining cash preview
        self.remaining_label = QLabel(f"Remaining Cash: {self.current_cash - self.price:,}")
        self.remaining_label.setStyleSheet("font-weight: bold; color: #FFD700;")
        form_layout.addRow("", self.remaining_label)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Purchase")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet(
            "background-color: #4B9CD3; color: white;")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(
            "background-color: #3D3D3D;")
        layout.addWidget(button_box)
        
        # Update the UI
        self.update_total()
        
    def update_total(self):
        """Update the total cost and remaining cash preview"""
        quantity = self.quantity_spin.value()
        total_cost = self.price * quantity
        remaining_cash = self.current_cash - total_cost
        
        self.total_label.setText(f"Total Cost: {total_cost:,}")
        self.remaining_label.setText(f"Remaining Cash: {remaining_cash:,}")
        
        # Disable OK button if not enough cash
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
        if remaining_cash < 0:
            ok_button.setEnabled(False)
            self.remaining_label.setStyleSheet("font-weight: bold; color: #FF6B6B;")
        else:
            ok_button.setEnabled(True)
            self.remaining_label.setStyleSheet("font-weight: bold; color: #FFD700;")
        
    def get_purchase_data(self):
        """Get the purchase data from the dialog
        
        Returns:
            Dictionary with purchase data
        """
        quantity = self.quantity_spin.value()
        total_cost = self.price * quantity
        
        return {
            'item_name': self.item_name,
            'quantity': quantity,
            'price': self.price,
            'total_cost': total_cost
        }

class LedgerWidget(QWidget):
    """Widget for displaying and filtering transaction ledger entries"""
    
    # Signal to notify when cash balance changes
    cash_balance_changed = pyqtSignal(int)
    
    def __init__(self, parent=None, item_database=None):
        super().__init__(parent)
        
        # Initialize cash manager for persistence
        self.cash_manager = CashManager()
        
        # Store reference to item database
        self.item_database = item_database
        
        # Set up the UI
        self.setup_ui()
        
        # Initialize data
        self.filtered_data = []
        self.all_ledger_data = []  # Store all entries before filtering
        self.cash_balance = self.cash_manager.get_cash_balance()  # Get saved cash balance
        self.cash_transactions = self.cash_manager.get_transactions()  # Get saved transactions
        
        # Update cash balance display
        self.cash_balance_label.setText(f"Cash Balance: {self.cash_balance:,}")

    def setup_ui(self):
        """Set up the UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Set dark mode background for the widget
        self.setStyleSheet("background-color: #2D2D2D; color: #E0E0E0;")
        
        # Filter controls layout
        filter_layout = QHBoxLayout()
        
        # Transaction type filter
        self.type_label = QLabel("Transaction Type:")
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0; selection-background-color: #505050;")
        self.type_combo.addItem("All Transactions", None)
        self.type_combo.addItem("Sales", "sale")
        self.type_combo.addItem("Purchases", "purchase")
        self.type_combo.addItem("Adjustments", "adjustment")
        self.type_combo.addItem("Cash", "cash")  # Add cash transaction type
        self.type_combo.addItem("Price Updates", "price_update")  # Add price update transaction type
        self.type_combo.currentIndexChanged.connect(self.filter_changed)
        
        # Date range filter
        self.date_from_label = QLabel("From:")
        self.date_from = QDateEdit()
        self.date_from.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))  # Default to last 30 days
        self.date_from.dateChanged.connect(self.filter_changed)
        
        self.date_to_label = QLabel("To:")
        self.date_to = QDateEdit()
        self.date_to.setStyleSheet("background-color: #3D3D3D; color: #E0E0E0;")
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())  # Default to today
        self.date_to.dateChanged.connect(self.filter_changed)
        
        # Reset filters button
        self.reset_button = QPushButton("Reset Filters")
        self.reset_button.setStyleSheet("background-color: #505050; color: #FFFFFF; padding: 5px;")
        self.reset_button.clicked.connect(self.reset_filters)
        
        # Add filter controls to layout
        filter_layout.addWidget(self.type_label)
        filter_layout.addWidget(self.type_combo)
        filter_layout.addWidget(self.date_from_label)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(self.date_to_label)
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(self.reset_button)
        filter_layout.addStretch()
        
        # Cash balance section
        cash_layout = QHBoxLayout()
        
        # Cash balance display
        self.cash_balance_label = QLabel("Cash Balance: 0")
        self.cash_balance_label.setStyleSheet("font-weight: bold; color: #FFD700; font-size: 14px;")
        
        # Cash transaction buttons
        self.add_cash_button = QPushButton("Add Cash")
        self.add_cash_button.setStyleSheet("background-color: #50C878; color: #FFFFFF; padding: 5px;")
        self.add_cash_button.clicked.connect(lambda: self.show_cash_dialog("add"))
        
        self.withdraw_cash_button = QPushButton("Withdraw Cash")
        self.withdraw_cash_button.setStyleSheet("background-color: #FF6B6B; color: #FFFFFF; padding: 5px;")
        self.withdraw_cash_button.clicked.connect(lambda: self.show_cash_dialog("withdraw"))
        
        # Add cash controls to layout
        cash_layout.addWidget(self.cash_balance_label)
        cash_layout.addWidget(self.add_cash_button)
        cash_layout.addWidget(self.withdraw_cash_button)
        cash_layout.addStretch()
        
        # Statistics layout
        stats_layout = QHBoxLayout()
        
        # Total entries
        self.total_entries_label = QLabel("Total Entries: 0")
        
        # Sales value
        self.sales_value_label = QLabel("Total Sales: 0")
        self.sales_value_label.setStyleSheet("font-weight: bold; color: #50C878;")
        
        # Incoming capital value
        self.capital_value_label = QLabel("Incoming Capital: 0")
        self.capital_value_label.setStyleSheet("font-weight: bold; color: #4B9CD3;")
        
        # Net value (total assets)
        self.net_value_label = QLabel("Total Assets: 0")
        self.net_value_label.setStyleSheet("font-weight: bold; color: #FFD700; font-size: 13px;")
        
        # Add statistics to layout
        stats_layout.addWidget(self.total_entries_label)
        stats_layout.addWidget(self.sales_value_label)
        stats_layout.addWidget(self.capital_value_label)
        stats_layout.addWidget(self.net_value_label)
        stats_layout.addStretch()
        
        # Create splitter for table and chart
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #555555; }")
        
        # Create table for ledger entries
        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(9)
        self.ledger_table.setHorizontalHeaderLabels([
            "Date & Time", "Item", "Type", "Old Stock", "New Stock", 
            "Quantity", "Default Price", "Selling Price", "Value"
        ])
        
        # Set dark mode style for table
        self.ledger_table.setStyleSheet("""
            QTableWidget {
                background-color: #2D2D2D;
                color: #E0E0E0;
                gridline-color: #555555;
                selection-background-color: #505050;
            }
            QHeaderView::section {
                background-color: #3D3D3D;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #505050;
            }
        """)
        
        # Set table properties
        self.ledger_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Item column stretches
        self.ledger_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.ledger_table.verticalHeader().setVisible(False)
        self.ledger_table.setAlternatingRowColors(True)
        self.ledger_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
        self.ledger_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ledger_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ledger_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Create chart widget
        self.chart_widget = LedgerChartWidget()
        
        # Add table and chart to splitter
        self.splitter.addWidget(self.ledger_table)
        self.splitter.addWidget(self.chart_widget)
        
        # Set initial sizes (table gets more space)
        self.splitter.setSizes([600, 400])
        
        # Add components to main layout
        layout.addLayout(filter_layout)
        layout.addLayout(cash_layout)
        layout.addLayout(stats_layout)
        layout.addWidget(self.splitter)
        
        # Set stretch factor to make splitter expand
        layout.setStretchFactor(self.splitter, 1)
    
    def show_cash_dialog(self, action_type="add"):
        """Show dialog for cash transactions
        
        Args:
            action_type: Type of action ('add', 'withdraw', or 'set')
        """
        dialog = CashEntryDialog(self.cash_balance, self)
        
        # Set the appropriate transaction type
        if action_type == "add":
            dialog.type_combo.setCurrentIndex(0)
        elif action_type == "withdraw":
            dialog.type_combo.setCurrentIndex(1)
        else:  # set
            dialog.type_combo.setCurrentIndex(2)
        
        # Show the dialog
        if dialog.exec():
            # Get transaction data
            tx_data = dialog.get_transaction_data()
            if tx_data:
                # Use cash manager to add transaction and update balance
                ledger_entry = self.cash_manager.add_transaction(tx_data)
                
                # Update local cash balance
                self.cash_balance = self.cash_manager.get_cash_balance()
                self.cash_balance_label.setText(f"Cash Balance: {self.cash_balance:,}")
                
                # Add to all ledger data and refresh
                self.all_ledger_data.append(ledger_entry)
                self.filter_changed()
                
                # Emit signal that cash balance changed
                self.cash_balance_changed.emit(self.cash_balance)
                
    def set_cash_balance(self, balance):
        """Set the cash balance
        
        Args:
            balance: New cash balance
        """
        # Use cash manager to update balance with persistence
        self.cash_manager.set_cash_balance(balance)
        
        # Update local cash balance
        self.cash_balance = balance
        self.cash_balance_label.setText(f"Cash Balance: {self.cash_balance:,}")
        
        # Emit signal that cash balance changed
        self.cash_balance_changed.emit(self.cash_balance)
        
    def reset_filters(self):
        """Reset all filters to default values"""
        self.type_combo.setCurrentIndex(0)  # All transactions
        self.date_from.setDate(QDate.currentDate().addDays(-30))  # Last 30 days
        self.date_to.setDate(QDate.currentDate())  # Today
        
        # Apply the reset filters
        self.filter_changed()
        
    def filter_changed(self):
        """Called when any filter changes - applies filtering to the data"""
        # Get filter criteria
        selected_type = self.type_combo.currentData()  # Gets 'sale', 'purchase', None etc.
        start_date = self.date_from.date().startOfDay().toSecsSinceEpoch()
        end_date = self.date_to.date().endOfDay().toSecsSinceEpoch()
        
        # Filter the data
        self.filtered_data = []
        for entry in self.all_ledger_data:
            timestamp = entry.get('timestamp', 0)
            tx_type = entry.get('transaction_type')
            
            # Check type filter (None means 'All')
            type_match = (selected_type is None) or (tx_type == selected_type)
            
            # Check date filter
            date_match = (start_date <= timestamp <= end_date)
            
            if type_match and date_match:
                self.filtered_data.append(entry)
        
        # Update the table display
        self.update_table()
        
        # Calculate and update statistics based on filtered data
        self.calculate_stats()
        
        # Update the chart with filtered data
        self.update_chart_data()
        
    def update_data(self, ledger_entries, stats=None):
        """Update the ledger data with the given entries
        
        Args:
            ledger_entries: List of ledger entry dictionaries
            stats: Dictionary of statistics (optional)
        """
        # Store all entries
        self.all_ledger_data = ledger_entries
        
        # Get cash transactions and merge with ledger entries
        cash_transactions = self.cash_manager.get_transactions()
        
        # Combine ledger entries with cash transactions
        combined_entries = ledger_entries + cash_transactions
        
        # Sort by timestamp (newest first)
        combined_entries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Store combined entries
        self.all_ledger_data = combined_entries
        
        # Apply filters
        self.filter_changed()
        
        # Update statistics if provided
        if stats:
            self.update_stats(stats)
        else:
            self.calculate_stats()
            
        # Update chart data
        self.update_chart_data()
            
    def update_table(self):
        """Update the table with current filtered data"""
        # Clear existing rows
        self.ledger_table.setRowCount(0)
        
        # Add data rows
        for i, entry in enumerate(self.filtered_data):
            self.ledger_table.insertRow(i)
            
            # Format timestamp
            timestamp = entry.get('timestamp', 0)
            dt = datetime.fromtimestamp(timestamp)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            date_item = QTableWidgetItem(date_str)
            self.ledger_table.setItem(i, 0, date_item)
            
            # Item name
            item_name = entry.get('item_name', '')
            name_item = QTableWidgetItem(item_name)
            # Make item name bold for readability
            font = name_item.font()
            font.setBold(True)
            name_item.setFont(font)
            self.ledger_table.setItem(i, 1, name_item)
            
            # Transaction type
            tx_type = entry.get('transaction_type', '')
            type_item = QTableWidgetItem(tx_type.capitalize())
            
            # Dark mode colors for transaction types
            if tx_type == 'sale':
                # Bright green for sales
                type_item.setForeground(QColor(80, 200, 120))  # Bright green
                font = QFont("", -1, QFont.Weight.Bold)
                type_item.setFont(font)
            elif tx_type == 'purchase':
                # Bright blue for purchases
                type_item.setForeground(QColor(100, 150, 255))  # Bright blue
                font = QFont("", -1, QFont.Weight.Bold)
                type_item.setFont(font)
            elif tx_type == 'adjustment':
                # Yellow/gold for adjustments
                type_item.setForeground(QColor(255, 215, 0))  # Gold
            elif tx_type == 'cash':
                # Orange for cash transactions
                type_item.setForeground(QColor(255, 165, 0))  # Orange
                
            self.ledger_table.setItem(i, 2, type_item)
            
            # Old stock
            old_stock = entry.get('old_stock', 0)
            old_stock_item = QTableWidgetItem(str(old_stock))
            old_stock_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ledger_table.setItem(i, 3, old_stock_item)
            
            # New stock
            new_stock = entry.get('new_stock', 0)
            new_stock_item = QTableWidgetItem(str(new_stock))
            new_stock_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Highlight stock changes with dark mode colors
            if new_stock > old_stock:
                # Stock increased - blue
                new_stock_item.setForeground(QColor(100, 150, 255))
            elif new_stock < old_stock:
                # Stock decreased - red
                new_stock_item.setForeground(QColor(255, 100, 100))
                
            self.ledger_table.setItem(i, 4, new_stock_item)
            
            # Quantity
            quantity = entry.get('quantity', 0)
            quantity_item = QTableWidgetItem(str(quantity))
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Make quantity bold for better visibility
            font = quantity_item.font()
            font.setBold(True)
            quantity_item.setFont(font)
            quantity_item.setForeground(QColor(255, 220, 100))  # Gold/yellow for quantity
            self.ledger_table.setItem(i, 5, quantity_item)
            
            # Default Price
            default_price = entry.get('price', 0)
            price_text = format(default_price, ",")  # Format with commas
            price_item = QTableWidgetItem(price_text)
            price_item.setData(Qt.ItemDataRole.UserRole, default_price)  # Store raw value for sorting
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            price_item.setForeground(QColor(150, 200, 255))  # Light blue for prices
            self.ledger_table.setItem(i, 6, price_item)
            
            # Selling Price (if different from default)
            selling_price = entry.get('selling_price')
            
            if selling_price is not None and selling_price != default_price:
                # Different selling price
                selling_price_text = format(selling_price, ",")
                selling_price_item = QTableWidgetItem(selling_price_text)
                selling_price_item.setData(Qt.ItemDataRole.UserRole, selling_price)
                selling_price_item.setForeground(QColor(255, 130, 130))  # Bright red/pink
                font = QFont()
                font.setBold(True)
                selling_price_item.setFont(font)
            elif selling_price is not None:
                # Same as default price
                selling_price_text = format(selling_price, ",")
                selling_price_item = QTableWidgetItem(selling_price_text)
                selling_price_item.setData(Qt.ItemDataRole.UserRole, selling_price)
            else:
                # No selling price (not a sale)
                selling_price_item = QTableWidgetItem("-")
                selling_price_item.setData(Qt.ItemDataRole.UserRole, 0)
            
            selling_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ledger_table.setItem(i, 7, selling_price_item)
            
            # Value
            value = entry.get('value', 0)
            value_text = format(value, ",")  # Format with commas
            value_item = QTableWidgetItem(value_text)
            value_item.setData(Qt.ItemDataRole.UserRole, value)  # Store raw value for sorting
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Bold values with bright color for better readability
            font = value_item.font()
            font.setBold(True)
            value_item.setFont(font)
            
            # Color value based on transaction type
            if tx_type == 'sale':
                value_item.setForeground(QColor(80, 200, 120))  # Green for sales
            elif tx_type == 'purchase':
                value_item.setForeground(QColor(100, 150, 255))  # Blue for purchases
            elif tx_type == 'adjustment':
                value_item.setForeground(QColor(255, 215, 0))  # Gold for adjustments
            elif tx_type == 'cash':
                value_item.setForeground(QColor(255, 165, 0))  # Orange for cash transactions
                
            self.ledger_table.setItem(i, 8, value_item)
            
            # Set row background color
            row_color = QColor(45, 45, 45) if i % 2 == 0 else QColor(50, 50, 50)
            for col in range(self.ledger_table.columnCount()):
                item = self.ledger_table.item(i, col)
                if item:
                    item.setBackground(row_color)
        
        # Resize columns to content
        self.ledger_table.resizeColumnsToContents()
        # Keep the item name column stretched
        self.ledger_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                    
    def calculate_stats(self):
        """Calculate statistics from filtered data"""
        total_entries = len(self.filtered_data)
        total_sales_value = 0
        total_capital_value = 0
        
        for entry in self.filtered_data:
            tx_type = entry.get('transaction_type')
            value = entry.get('value', 0)
            
            if tx_type == 'sale':
                total_sales_value += value
            elif tx_type == 'purchase' or (tx_type == 'adjustment' and entry.get('new_stock', 0) > entry.get('old_stock', 0)):
                # Count purchases and positive adjustments as incoming capital
                total_capital_value += value
        
        # Calculate total assets (cash balance + incoming capital)
        total_assets = self.cash_balance + total_capital_value
        
        # Update the UI
        self.total_entries_label.setText(f"Total Entries: {total_entries}")
        self.sales_value_label.setText(f"Total Sales: {total_sales_value:,}")
        self.capital_value_label.setText(f"Incoming Capital: {total_capital_value:,}")
        self.net_value_label.setText(f"Total Assets: {total_assets:,}")
    
    def update_stats(self, stats):
        """Update statistics display from external stats
        
        Args:
            stats: Dictionary of statistics
        """
        # Update total entries
        total_entries = stats.get('total_entries', 0)
        self.total_entries_label.setText(f"Total Entries: {total_entries}")
        
        # Update sales value
        total_sales_value = stats.get('total_sales_value', 0)
        self.sales_value_label.setText(f"Total Sales: {total_sales_value:,}")
        
        # Update capital value if provided
        if 'total_capital_value' in stats:
            total_capital_value = stats.get('total_capital_value', 0)
            self.capital_value_label.setText(f"Incoming Capital: {total_capital_value:,}")
            
            # Calculate total assets
            total_assets = self.cash_balance + total_capital_value
            self.net_value_label.setText(f"Total Assets: {total_assets:,}")
    
    def update_chart_data(self):
        """Update chart data based on filtered ledger entries"""
        # Group data by day for the chart
        daily_data = {}
        
        for entry in self.filtered_data:
            timestamp = entry.get('timestamp', 0)
            tx_type = entry.get('transaction_type')
            value = entry.get('value', 0)
            
            # Convert timestamp to datetime and get date only (no time)
            dt = datetime.fromtimestamp(timestamp)
            date_key = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Initialize if this date doesn't exist yet
            if date_key not in daily_data:
                daily_data[date_key] = {'sales': 0, 'capital': 0, 'cash': 0}
            
            # Add value to appropriate category
            if tx_type == 'sale':
                daily_data[date_key]['sales'] += value
            elif tx_type == 'purchase' or (tx_type == 'adjustment' and entry.get('new_stock', 0) > entry.get('old_stock', 0)):
                daily_data[date_key]['capital'] += value
            elif tx_type == 'cash':
                daily_data[date_key]['cash'] += value
        
        # Sort dates
        sorted_dates = sorted(daily_data.keys())
        
        # Prepare data for chart
        timestamps = []
        sales_values = []
        capital_values = []
        cash_values = []
        
        for date in sorted_dates:
            timestamps.append(date)
            sales_values.append(daily_data[date]['sales'])
            capital_values.append(daily_data[date]['capital'])
            cash_values.append(daily_data[date]['cash'])
        
        # If we have no data, add a placeholder
        if not timestamps:
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            timestamps = [now - timedelta(days=1), now]
            sales_values = [0, 0]
            capital_values = [0, 0]
            cash_values = [0, 0]
        
        # Update the chart with the new data
        chart_data = {
            'timestamps': timestamps,
            'sales_values': sales_values,
            'capital_values': capital_values,
            'cash_values': cash_values
        }
        
        self.chart_widget.set_data(chart_data)
        
    def show_context_menu(self, position):
        """Show context menu for the ledger table"""
        menu = QMenu()
        
        # Get the row
        row = self.ledger_table.indexAt(position).row()
        
        # Only show context menu if a valid row is clicked
        if row >= 0 and row < len(self.filtered_data):
            entry = self.filtered_data[row]
            item_name = entry.get('item_name', '')
            timestamp = entry.get('timestamp', 0)
            tx_type = entry.get('transaction_type', '')
            
            # Add actions
            view_action = QAction(f"View Details for '{item_name}'", self)
            # view_action.triggered.connect(lambda: self.view_item_details(item_name))
            menu.addAction(view_action)
            
            # Add purchase action if item database is available
            if self.item_database and item_name in self.item_database.items:
                purchase_action = QAction(f"Purchase '{item_name}' with Cash", self)
                purchase_action.triggered.connect(lambda: self.purchase_item_with_cash(item_name))
                menu.addAction(purchase_action)
            
            # Add separator
            menu.addSeparator()
            
            # Delete action
            delete_action = QAction(f"Delete Entry and Reverse Effects", self)
            delete_action.triggered.connect(lambda: self.delete_ledger_entry(timestamp, item_name, tx_type))
            menu.addAction(delete_action)
            
            # Add separator
            menu.addSeparator()
            
            # Copy actions
            copy_name_action = QAction("Copy Item Name", self)
            copy_name_action.triggered.connect(lambda: self.copy_to_clipboard(item_name))
            menu.addAction(copy_name_action)
            
            # Execute menu
            menu.exec(self.ledger_table.mapToGlobal(position))
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

    def purchase_item_with_cash(self, item_name):
        """Purchase an item using cash
        
        Args:
            item_name: Name of the item to purchase
        """
        if not self.item_database or item_name not in self.item_database.items:
            return
        
        # Get item details
        item = self.item_database.items[item_name]
        price = item.get('price', 0)
        
        # Show purchase dialog
        dialog = PurchaseDialog(item_name, price, self.cash_balance, self)
        
        if dialog.exec():
            # Get purchase data
            purchase_data = dialog.get_purchase_data()
            quantity = purchase_data['quantity']
            
            # Use item database to update stock with cash
            current_stock = item.get('stock', 0)
            new_stock = current_stock + quantity
            
            # Update stock with cash integration
            success = self.item_database.update_stock(
                item_name, 
                new_stock, 
                transaction_type="purchase",
                use_cash=True,
                cash_manager=self.cash_manager
            )
            
            if success:
                # Update cash balance
                self.cash_balance = self.cash_manager.get_cash_balance()
                self.cash_balance_label.setText(f"Cash Balance: {self.cash_balance:,}")
                
                # Emit signal that cash balance changed
                self.cash_balance_changed.emit(self.cash_balance)
                
                # Refresh the ledger
                if hasattr(self.parent(), 'refresh_ledger'):
                    self.parent().refresh_ledger()
                
                # Update the chart
                self.update_chart_data()

    def delete_ledger_entry(self, timestamp, item_name, tx_type):
        """Delete a ledger entry and reverse its effects
        
        Args:
            timestamp: Timestamp of the entry to delete
            item_name: Item name of the entry to delete
            tx_type: Transaction type
        """
        from PyQt6.QtWidgets import QMessageBox, QApplication
        
        # Confirm deletion
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setText(f"Are you sure you want to delete this {tx_type} entry for '{item_name}'?")
        msg_box.setInformativeText("This will remove the entry from the ledger and reverse its effects.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        # Apply dark theme styling
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #505050;
                color: #FFFFFF;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
        """)
        
        # Show the dialog
        result = msg_box.exec()
        
        # If user confirmed deletion
        if result == QMessageBox.StandardButton.Yes:
            success = False
            
            # Handle different transaction types
            if tx_type == 'cash':
                # Delete cash transaction
                success = self.cash_manager.delete_transaction(timestamp, item_name)
                if success:
                    # Update cash balance display
                    self.cash_balance = self.cash_manager.get_cash_balance()
                    self.cash_balance_label.setText(f"Cash Balance: {self.cash_balance:,}")
                    # Emit signal that cash balance changed
                    self.cash_balance_changed.emit(self.cash_balance)
            else:
                # Delete ledger entry in item database
                if self.item_database:
                    success = self.item_database.delete_ledger_entry(timestamp, item_name)
            
            # Refresh the ledger display
            if success:
                # Get updated ledger entries
                if self.item_database:
                    entries = self.item_database.get_ledger_entries(limit=1000)
                    stats = self.item_database.get_ledger_stats()
                    self.update_data(entries, stats)
                
                # Show success message - use QApplication.activeWindow() to find main window
                main_window = QApplication.activeWindow()
                if hasattr(main_window, 'status_bar'):
                    main_window.status_bar.showMessage(f"Successfully deleted {tx_type} entry for '{item_name}'", 5000)
                else:
                    # Use a temporary message box if status bar not available
                    temp_msg = QMessageBox()
                    temp_msg.setWindowTitle("Success")
                    temp_msg.setText(f"Successfully deleted {tx_type} entry for '{item_name}'")
                    temp_msg.setIcon(QMessageBox.Icon.Information)
                    temp_msg.setStyleSheet("""
                        QMessageBox {
                            background-color: #2D2D2D;
                            color: #E0E0E0;
                        }
                        QPushButton {
                            background-color: #505050;
                            color: #FFFFFF;
                            padding: 5px;
                            min-width: 80px;
                        }
                    """)
                    temp_msg.exec()
            else:
                # Show error message
                error_msg = QMessageBox()
                error_msg.setWindowTitle("Error")
                error_msg.setText(f"Failed to delete entry. It may have been modified or removed.")
                error_msg.setIcon(QMessageBox.Icon.Warning)
                error_msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #2D2D2D;
                        color: #E0E0E0;
                    }
                    QPushButton {
                        background-color: #505050;
                        color: #FFFFFF;
                        padding: 5px;
                        min-width: 80px;
                    }
                """)
                error_msg.exec()
