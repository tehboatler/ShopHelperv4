"""
Cash balance tracking for MapleLegends ShopHelper
Handles persistence of cash transactions and balance
"""

import json
import time
from datetime import datetime
from pathlib import Path

class CashManager:
    """Manages cash balance and transactions with persistence"""
    
    def __init__(self, cash_file_path='cash_data.json'):
        """Initialize the cash manager
        
        Args:
            cash_file_path: Path to the cash data JSON file
        """
        self.cash_path = Path(cash_file_path)
        self.cash_balance = 0
        self.cash_transactions = []
        
        # Load cash data if file exists
        self.load_cash_data()
            
    def load_cash_data(self):
        """Load cash data from the cash file"""
        if self.cash_path.exists():
            try:
                with open(self.cash_path, 'r') as f:
                    cash_data = json.load(f)
                self.cash_balance = cash_data.get('cash_balance', 0)
                self.cash_transactions = cash_data.get('transactions', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading cash file: {e}")
                # Initialize with default values if file can't be read
                self.reset_cash_data()
        else:
            # Create a new cash file with default values
            self.reset_cash_data()
            self.save_cash_data()
    
    def reset_cash_data(self):
        """Reset cash data to default values"""
        self.cash_balance = 0
        self.cash_transactions = []
    
    def save_cash_data(self):
        """Save cash data to the cash file"""
        cash_data = {
            'cash_balance': self.cash_balance,
            'transactions': self.cash_transactions,
            'last_updated': time.time()
        }
        
        try:
            with open(self.cash_path, 'w') as f:
                json.dump(cash_data, f, indent=2)
        except IOError as e:
            print(f"Error saving cash file: {e}")
    
    def add_transaction(self, transaction_data):
        """Add a cash transaction
        
        Args:
            transaction_data: Dictionary with transaction details
        
        Returns:
            Ledger entry dictionary for the transaction
        """
        # Update cash balance
        self.cash_balance = transaction_data.get('new_balance', self.cash_balance)
        
        # Create ledger entry for the transaction
        ledger_entry = {
            "timestamp": transaction_data.get('timestamp', time.time()),
            "item_name": transaction_data.get('description', 'Cash transaction'),
            "old_stock": 0,
            "new_stock": 0,
            "quantity": 0,
            "price": 0,
            "selling_price": None,
            "value": transaction_data.get('value', 0),
            "transaction_type": "cash"
        }
        
        # Add to cash transactions
        self.cash_transactions.append(ledger_entry)
        
        # Save changes
        self.save_cash_data()
        
        return ledger_entry
    
    def get_cash_balance(self):
        """Get the current cash balance
        
        Returns:
            Current cash balance
        """
        return self.cash_balance
    
    def set_cash_balance(self, balance):
        """Set the cash balance directly
        
        Args:
            balance: New cash balance
        """
        old_balance = self.cash_balance
        self.cash_balance = balance
        
        # Create a transaction record for the change
        transaction_data = {
            'timestamp': time.time(),
            'description': 'Set cash balance',
            'value': balance - old_balance,
            'new_balance': balance
        }
        
        # Add the transaction
        self.add_transaction(transaction_data)
    
    def get_transactions(self):
        """Get all cash transactions
        
        Returns:
            List of cash transaction ledger entries
        """
        return self.cash_transactions
        
    def delete_transaction(self, timestamp, description, reverse_transaction=True):
        """Delete a cash transaction and optionally reverse its effects
        
        Args:
            timestamp: Timestamp of the transaction to delete
            description: Description of the transaction to delete
            reverse_transaction: Whether to reverse the transaction effects
            
        Returns:
            True if transaction was found and deleted, False otherwise
        """
        # Find the transaction to delete
        transaction_to_delete = None
        for i, transaction in enumerate(self.cash_transactions):
            if (abs(transaction.get('timestamp', 0) - timestamp) < 0.001 and 
                transaction.get('item_name') == description):
                transaction_to_delete = transaction
                transaction_index = i
                break
                
        if not transaction_to_delete:
            return False
            
        # Reverse the transaction if requested
        if reverse_transaction:
            # Get the value of the transaction
            value = transaction_to_delete.get('value', 0)
            
            # Reverse the effect on cash balance
            self.cash_balance -= value
        
        # Remove the transaction
        self.cash_transactions.pop(transaction_index)
        
        # Save changes
        self.save_cash_data()
        
        return True
