"""
Item Database for MapleLegends ShopHelper
Manages a local database of items and their prices
Provides fuzzy matching capabilities for OCR results
"""

import os
import json
import time
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process

class ItemDatabase:
    """Manages a local database of items and provides fuzzy matching capabilities"""
    
    def __init__(self, db_path="items_database.json"):
        """Initialize the item database with the given path"""
        self.db_path = db_path
        self.items = {}
        self.recently_logged = []
        self.ledger_entries = []  # Track all stock changes
        self.load_database()
        self.load_logs()
        self.load_ledger()
    
    def load_database(self):
        """Load the database from the JSON file"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    items_data = data.get('items', {})
                    
                    # Handle both old and new database formats
                    self.items = {}
                    for key, value in items_data.items():
                        if isinstance(value, dict) and 'price' in value:
                            # Old format: {"item_name": {"price": 1000, "added_date": 123456789}}
                            self.items[key] = value
                            # Initialize stock property if not present
                            if 'stock' not in self.items[key]:
                                self.items[key]['stock'] = 0
                        else:
                            # New format: {"item_name": 1000}
                            self.items[key] = {
                                'price': value,
                                'added_date': time.time(),
                                'stock': 0
                            }
            except Exception as e:
                print(f"Error loading database: {e}")
                # Create empty database if loading fails
                self.items = {}
        else:
            # If main database doesn't exist, try to load from template
            template_path = "items_database_template.json"
            if os.path.exists(template_path):
                try:
                    print(f"Main database not found. Loading from template: {template_path}")
                    with open(template_path, 'r') as f:
                        data = json.load(f)
                        self.items = data.get('items', {})
                    # Save to the main database file
                    self.save_items()
                    print(f"Created new database from template.")
                except Exception as e:
                    print(f"Error loading template database: {e}")
                    # Create empty database if loading template fails
                    self.items = {}
                    self.save_items()
            else:
                # Create empty database if neither file exists
                print("Creating new empty database.")
                self.items = {}
                self.save_items()
    
    def save_items(self):
        """Save the database to the JSON file"""
        data = {
            'items': self.items,
            'last_updated': time.time()
        }
        try:
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def add_item(self, item_name, price, stock=0):
        """Add a new item to the database"""
        if not item_name:
            return None
            
        # Ensure price is a number
        try:
            price = int(price) if isinstance(price, str) and price.isdigit() else int(price)
        except (TypeError, ValueError):
            # Default to 0 if conversion fails
            price = 0
            
        # Ensure stock is a number
        try:
            stock = int(stock) if isinstance(stock, str) and stock.isdigit() else int(stock)
        except (TypeError, ValueError):
            # Default to 0 if conversion fails
            stock = 0
            
        # Add to the database with the original structure
        self.items[item_name] = {
            'price': price,
            'added_date': time.time(),
            'stock': stock
        }
        
        # Save the database
        self.save_items()
        
        return item_name
    
    def update_item(self, item_name, price, new_name=None, stock=None):
        """Update an existing item's price and optionally rename it
        
        Args:
            item_name: Current name of the item
            price: New price for the item
            new_name: New name for the item (if renaming)
            stock: New stock value (if updating stock)
            
        Returns:
            True if successful, False otherwise
        """
        if item_name in self.items:
            # Ensure price is a number
            try:
                price = int(price) if isinstance(price, str) and price.isdigit() else int(price)
            except (TypeError, ValueError):
                # Default to 0 if conversion fails
                price = 0
            
            # If we're renaming the item
            if new_name and new_name != item_name:
                # Create a new entry with the old item's data
                item_data = self.items[item_name].copy()
                item_data['price'] = price
                item_data['last_updated'] = time.time()
                
                # Update stock if provided
                if stock is not None:
                    try:
                        item_data['stock'] = int(stock)
                    except (TypeError, ValueError):
                        pass  # Keep existing stock value
                
                # Add the new item
                self.items[new_name] = item_data
                
                # Remove the old item
                del self.items[item_name]
            else:
                # Just update the price on the existing item
                self.items[item_name]['price'] = price
                self.items[item_name]['last_updated'] = time.time()
                
                # Update stock if provided
                if stock is not None:
                    try:
                        self.items[item_name]['stock'] = int(stock)
                    except (TypeError, ValueError):
                        pass  # Keep existing stock value
            
            # Save the database
            self.save_items()
            
            return True
        return False
    
    def delete_item(self, item_name):
        """Delete an item from the database"""
        if item_name in self.items:
            del self.items[item_name]
            self.save_items()
            return True
        return False
    
    def get_item(self, item_name):
        """Get an item by exact name"""
        return self.items.get(item_name, None)
    
    def match_item(self, text, min_score=70):
        """Match the given text against the database items"""
        if not text or not self.items:
            return None
            
        # Import fuzzywuzzy here to avoid circular imports
        from fuzzywuzzy import process, fuzz
            
        # Check for exact match first
        for item_name in self.items:
            if item_name.lower() == text.lower():
                item_data = self.items[item_name].copy()
                item_data['name'] = item_name
                item_data['match_score'] = 100
                return item_data
                
        # If no exact match, try fuzzy matching
        # Get list of item names
        item_names = list(self.items.keys())
        
        # Find best match
        match, score = process.extractOne(
            text, 
            item_names,
            scorer=fuzz.token_set_ratio  # Use token set ratio for better matching
        )
        
        # Only return if score is above threshold
        if score >= min_score:
            item_data = self.items[match].copy()
            item_data['name'] = match
            item_data['match_score'] = score
            return item_data
                    
        return None
    
    def search_items(self, query, limit=10):
        """Search items by name, returning top matches"""
        if not query or not self.items:
            return []
        
        # Import fuzzywuzzy here to avoid circular imports
        from fuzzywuzzy import process, fuzz
        
        # Get top matches
        item_names = list(self.items.keys())
        matches = process.extract(
            query, 
            item_names,
            scorer=fuzz.token_set_ratio,
            limit=limit
        )
        
        # Convert to list of dictionaries
        results = []
        for match, score in matches:
            item_data = self.items[match].copy()
            # Add additional info
            item_data['name'] = match
            item_data['match_score'] = score
            results.append(item_data)
            
        return results
    
    def process_ocr_results(self, ocr_results):
        """Process OCR results and match them against the database
        
        Args:
            ocr_results: List of OCR results from PaddleOCR
            
        Returns:
            List of processed results with matched items
        """
        processed_results = []
        
        for result in ocr_results:
            # Extract OCR text and confidence
            if isinstance(result, tuple) and len(result) >= 2:
                # Handle PaddleOCR format [([box], (text, confidence))]
                ocr_text = result[1][0]
                confidence = result[1][1]
            elif isinstance(result, dict):
                # Handle already processed dict format
                ocr_text = result.get('text', '')
                confidence = result.get('confidence', 0)
            else:
                # Skip invalid results
                continue
            
            # Create result entry
            entry = {
                'ocr_text': ocr_text,
                'confidence': confidence
            }
            
            # Try to match item in database
            match_result = self.match_item(ocr_text)
            if match_result:
                entry['matched_item'] = match_result['name']
                entry['price'] = match_result.get('price', 0)
                entry['match_score'] = match_result.get('match_score', 0)
                
                # Log it
                self.add_to_log(ocr_text, match_result['name'], match_result.get('price', 0), match_result.get('match_score', 0))
            else:
                entry['matched_item'] = None
                entry['price'] = None
                entry['match_score'] = None
            
            processed_results.append(entry)
        
        return processed_results
    
    def add_to_log(self, ocr_text, matched_item=None, price=None, match_score=None):
        """Add an item to the recent logs"""
        # Get stock information if we have a matched item
        stock = 0
        if matched_item and matched_item in self.items:
            stock = self.items[matched_item].get('stock', 0)
            
        log_entry = {
            'timestamp': time.time(),
            'ocr_text': ocr_text,
            'matched_item': matched_item,
            'price': price,
            'match_score': match_score,
            'stock': stock  # Include stock in the log entry
        }
        
        # Add to the beginning of the list
        self.recently_logged.insert(0, log_entry)
        
        # Limit the log to 100 entries
        if len(self.recently_logged) > 100:
            self.recently_logged = self.recently_logged[:100]
        
        # Save logs to file
        self.save_logs()
    
    def correct_log_entry(self, log_index, new_matched_item=None, new_price=None):
        """Correct a log entry with the right item and price"""
        if 0 <= log_index < len(self.recently_logged):
            if new_matched_item is not None:
                self.recently_logged[log_index]['matched_item'] = new_matched_item
                
            if new_price is not None:
                # Ensure price is a number
                try:
                    price = int(new_price) if isinstance(new_price, str) and new_price.isdigit() else int(new_price)
                except (TypeError, ValueError):
                    # Default to 0 if conversion fails
                    price = 0
                    
                self.recently_logged[log_index]['price'] = price
            
            # Save changes to logs file
            self.save_logs()
            return True
        return False
    
    def get_recent_logs(self, limit=10):
        """Get the most recent log entries with up-to-date stock information"""
        # Update stock information in log entries from the current database
        updated_logs = []
        
        for log in self.recently_logged[:limit]:
            # Create a copy of the log entry to avoid modifying the original
            updated_log = log.copy()
            
            # Update stock information if we have a matched item
            if 'matched_item' in log and log['matched_item'] in self.items:
                updated_log['stock'] = self.items[log['matched_item']].get('stock', 0)
            else:
                updated_log['stock'] = 0
                
            updated_logs.append(updated_log)
            
        return updated_logs
    
    def clear_logs(self):
        """Clear the recently logged items list"""
        self.recently_logged = []
        
    def get_item_count(self):
        """Get the number of items in the database"""
        return len(self.items)
    
    def get_stats(self):
        """Get statistics about the database"""
        total_items = len(self.items)
        avg_price = 0
        min_price = 0
        max_price = 0
        
        if total_items > 0:
            # Make sure we're only dealing with numeric price values
            prices = []
            for item_data in self.items.values():
                if isinstance(item_data, dict) and 'price' in item_data:
                    prices.append(item_data['price'])
                elif isinstance(item_data, (int, float)):
                    # Handle simple integer prices if they exist
                    prices.append(item_data)
            
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
        
        return {
            'total_items': total_items,
            'avg_price': int(avg_price),
            'min_price': min_price,
            'max_price': max_price
        }
    
    def save_logs(self):
        """Save the recent logs to a file"""
        log_path = "recent_logs.json"
        log_data = {
            'logs': self.recently_logged,
            'last_updated': time.time()
        }
        try:
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Error saving logs: {e}")
    
    def load_logs(self):
        """Load the recent logs from file"""
        log_path = "recent_logs.json"
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    data = json.load(f)
                    self.recently_logged = data.get('logs', [])
            except Exception as e:
                print(f"Error loading logs: {e}")
                # Create empty logs if loading fails
                self.recently_logged = []
        else:
            # Create empty logs if file doesn't exist
            self.recently_logged = []
    
    def update_stock(self, item_name, stock, transaction_type="adjustment", use_cash=False, cash_manager=None):
        """Update the stock of an item
        
        Args:
            item_name: Name of the item to update
            stock: New stock value
            transaction_type: Type of transaction (adjustment, sale, purchase, etc.)
            use_cash: Whether to use cash for purchases
            cash_manager: Cash manager instance for cash transactions
            
        Returns:
            True if successful, False otherwise
        """
        if item_name in self.items:
            try:
                stock = int(stock)
                old_stock = self.items[item_name].get('stock', 0)
                
                # Don't do anything if stock is unchanged
                if stock == old_stock:
                    return True
                
                # Update the stock
                self.items[item_name]['stock'] = stock
                self.items[item_name]['last_updated'] = time.time()
                
                # Add to ledger
                price = self.items[item_name].get('price', 0)
                
                # Handle cash transaction for purchases
                if transaction_type == "purchase" and use_cash and cash_manager:
                    # Calculate purchase value
                    quantity = stock - old_stock
                    purchase_value = quantity * price
                    
                    # Check if we have enough cash
                    current_cash = cash_manager.get_cash_balance()
                    if current_cash < purchase_value:
                        return False  # Not enough cash
                    
                    # Deduct cash for the purchase
                    cash_manager.add_transaction({
                        'timestamp': time.time(),
                        'description': f"Purchase: {item_name} x{quantity}",
                        'value': -purchase_value,
                        'new_balance': current_cash - purchase_value
                    })
                
                self.add_to_ledger(item_name, old_stock, stock, transaction_type, price)
                
                # Save the database
                self.save_items()
                return True
            except (TypeError, ValueError):
                return False
        return False
    
    def adjust_stock(self, item_name, adjustment, transaction_type="adjustment", use_cash=False, cash_manager=None):
        """Adjust the stock of an item by adding or subtracting
        
        Args:
            item_name: Name of the item to adjust
            adjustment: Amount to adjust (positive or negative)
            transaction_type: Type of transaction (adjustment, sale, purchase, etc.)
            use_cash: Whether to use cash for purchases
            cash_manager: Cash manager instance for cash transactions
            
        Returns:
            True if successful, False otherwise
        """
        if item_name in self.items:
            try:
                adjustment = int(adjustment)
                current_stock = self.items[item_name].get('stock', 0)
                new_stock = max(0, current_stock + adjustment)  # Prevent negative stock
                
                # Don't do anything if stock is unchanged
                if new_stock == current_stock:
                    return True
                
                # Update the stock
                self.items[item_name]['stock'] = new_stock
                self.items[item_name]['last_updated'] = time.time()
                
                # Add to ledger
                price = self.items[item_name].get('price', 0)
                
                # Handle cash transaction for purchases
                if transaction_type == "purchase" and adjustment > 0 and use_cash and cash_manager:
                    # Calculate purchase value
                    purchase_value = adjustment * price
                    
                    # Check if we have enough cash
                    current_cash = cash_manager.get_cash_balance()
                    if current_cash < purchase_value:
                        return False  # Not enough cash
                    
                    # Deduct cash for the purchase
                    cash_manager.add_transaction({
                        'timestamp': time.time(),
                        'description': f"Purchase: {item_name} x{adjustment}",
                        'value': -purchase_value,
                        'new_balance': current_cash - purchase_value
                    })
                
                self.add_to_ledger(item_name, current_stock, new_stock, transaction_type, price)
                
                # Save the database
                self.save_items()
                return True
            except (TypeError, ValueError):
                return False
        return False
        
    def mark_as_sold(self, item_name, quantity=1, selling_price=None):
        """Mark an item as sold, reducing its stock
        
        Args:
            item_name: Name of the item sold
            quantity: Quantity sold (default 1)
            selling_price: Price per unit at which the item was sold (default: item's price)
            
        Returns:
            True if successful, False otherwise
        """
        if item_name in self.items:
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    return False  # Cannot sell negative or zero quantity
                    
                current_stock = self.items[item_name].get('stock', 0)
                
                # Cannot sell more than we have
                if quantity > current_stock:
                    return False
                    
                new_stock = current_stock - quantity
                
                # Update the stock
                self.items[item_name]['stock'] = new_stock
                self.items[item_name]['last_updated'] = time.time()
                
                # Get default price if selling price is not specified
                default_price = self.items[item_name].get('price', 0)
                if selling_price is None:
                    selling_price = default_price
                
                # Add to ledger
                sale_value = selling_price * quantity
                transaction_type = "sale"
                self.add_to_ledger(item_name, current_stock, new_stock, transaction_type, 
                                  default_price, quantity=quantity, value=sale_value, 
                                  selling_price=selling_price)
                
                # Save the database
                self.save_items()
                return True
            except (TypeError, ValueError):
                return False
        return False
        
    def add_to_ledger(self, item_name, old_stock, new_stock, transaction_type, price, 
                     quantity=None, value=None, selling_price=None):
        """Add an entry to the transaction ledger
        
        Args:
            item_name: Name of the item
            old_stock: Previous stock level
            new_stock: New stock level
            transaction_type: Type of transaction (adjustment, sale, purchase, etc.)
            price: Default price per item
            quantity: Quantity changed (optional)
            value: Total value of transaction (optional)
            selling_price: Price per unit at which the item was sold (optional)
        """
        # Calculate quantity if not provided
        if quantity is None:
            quantity = abs(new_stock - old_stock)
            
        # Use selling price if provided, otherwise use default price
        actual_price = selling_price if selling_price is not None else price
            
        # Calculate value if not provided
        if value is None:
            value = quantity * actual_price
            
        ledger_entry = {
            'timestamp': time.time(),
            'item_name': item_name,
            'old_stock': old_stock,
            'new_stock': new_stock,
            'quantity': quantity,
            'price': price,  # Store the default price
            'selling_price': selling_price,  # Store the actual selling price if different
            'value': value,
            'transaction_type': transaction_type
        }
        
        # Add to the beginning of the list
        self.ledger_entries.insert(0, ledger_entry)
        
        # Limit the ledger to 1000 entries
        if len(self.ledger_entries) > 1000:
            self.ledger_entries = self.ledger_entries[:1000]
            
        # Save the ledger
        self.save_ledger()
        
    def get_ledger_entries(self, limit=100, transaction_type=None, item_name=None):
        """Get ledger entries with optional filtering
        
        Args:
            limit: Maximum number of entries to return
            transaction_type: Filter by transaction type (optional)
            item_name: Filter by item name (optional)
            
        Returns:
            List of ledger entries
        """
        # Start with all entries
        filtered_entries = list(self.ledger_entries)
        
        # Apply transaction type filter
        if transaction_type:
            filtered_entries = [entry for entry in filtered_entries 
                              if entry.get('transaction_type') == transaction_type]
                              
        # Apply item name filter
        if item_name:
            filtered_entries = [entry for entry in filtered_entries 
                              if entry.get('item_name') == item_name]
                              
        # Return limited results
        return filtered_entries[:limit]
        
    def delete_ledger_entry(self, timestamp, item_name, reverse_transaction=True):
        """Delete a ledger entry and optionally reverse its effects
        
        Args:
            timestamp: Timestamp of the entry to delete
            item_name: Item name of the entry to delete
            reverse_transaction: Whether to reverse the transaction effects
            
        Returns:
            True if entry was found and deleted, False otherwise
        """
        # Find the entry to delete
        entry_to_delete = None
        for i, entry in enumerate(self.ledger_entries):
            if (abs(entry.get('timestamp', 0) - timestamp) < 0.001 and 
                entry.get('item_name') == item_name):
                entry_to_delete = entry
                entry_index = i
                break
                
        if not entry_to_delete:
            return False
            
        # Reverse the transaction if requested
        if reverse_transaction:
            transaction_type = entry_to_delete.get('transaction_type')
            
            if transaction_type == 'sale':
                # Reverse sale: add items back to inventory
                quantity = entry_to_delete.get('quantity', 0)
                price = entry_to_delete.get('price', 0)
                
                # Get current stock
                current_stock = 0
                if item_name in self.items:
                    current_stock = self.items[item_name].get('stock', 0)
                    
                # Add items back to inventory
                if item_name in self.items:
                    self.items[item_name]['stock'] = current_stock + quantity
                else:
                    # Item was removed from inventory, add it back
                    self.items[item_name] = {
                        'name': item_name,
                        'price': price,
                        'stock': quantity
                    }
                    
            elif transaction_type == 'adjustment':
                # Reverse adjustment: restore previous stock
                old_stock = entry_to_delete.get('old_stock', 0)
                
                # Restore previous stock
                if item_name in self.items:
                    self.items[item_name]['stock'] = old_stock
                    
            elif transaction_type == 'price_update':
                # Reverse price update: restore previous price
                old_price = entry_to_delete.get('old_price', 0)
                
                # Restore previous price
                if item_name in self.items:
                    self.items[item_name]['price'] = old_price
        
        # Remove the entry
        self.ledger_entries.pop(entry_index)
        
        # Save changes
        self.save_ledger()
        self.save_items()
        
        return True
    
    def get_ledger_stats(self):
        """Get statistics from the ledger
        
        Returns:
            Dictionary with ledger statistics
        """
        total_entries = len(self.ledger_entries)
        
        # Count by transaction type
        transaction_counts = {}
        
        # Total values
        total_sales_value = 0
        total_purchase_value = 0
        
        for entry in self.ledger_entries:
            # Count by type
            tx_type = entry.get('transaction_type', 'unknown')
            transaction_counts[tx_type] = transaction_counts.get(tx_type, 0) + 1
            
            # Calculate sales value
            if tx_type == 'sale':
                total_sales_value += entry.get('value', 0)
                
            # Calculate purchase value
            if tx_type == 'purchase':
                total_purchase_value += entry.get('value', 0)
                
        return {
            'total_entries': total_entries,
            'transaction_counts': transaction_counts,
            'total_sales_value': total_sales_value,
            'total_purchase_value': total_purchase_value
        }
        
    def save_ledger(self):
        """Save the ledger to a file"""
        ledger_path = "ledger.json"
        ledger_data = {
            'ledger': self.ledger_entries,
            'last_updated': time.time()
        }
        try:
            with open(ledger_path, 'w') as f:
                json.dump(ledger_data, f, indent=2)
        except Exception as e:
            print(f"Error saving ledger: {e}")
            
    def load_ledger(self):
        """Load the ledger from file"""
        ledger_path = "ledger.json"
        if os.path.exists(ledger_path):
            try:
                with open(ledger_path, 'r') as f:
                    data = json.load(f)
                    self.ledger_entries = data.get('ledger', [])
            except Exception as e:
                print(f"Error loading ledger: {e}")
                # Create empty ledger if loading fails
                self.ledger_entries = []
        else:
            # Create empty ledger if file doesn't exist
            self.ledger_entries = []
    
    def get_inventory_value(self):
        """Calculate the total value of all items in inventory
        
        Returns:
            Dictionary with inventory statistics
        """
        total_items = 0
        total_value = 0
        items_with_stock = 0
        
        for item_name, item_data in self.items.items():
            stock = item_data.get('stock', 0)
            price = item_data.get('price', 0)
            
            total_items += 1
            if stock > 0:
                items_with_stock += 1
                total_value += stock * price
        
        return {
            'total_items': total_items,
            'items_with_stock': items_with_stock,
            'total_value': total_value
        }
        
    def get_inventory_items(self):
        """Get all items with their inventory information
        
        Returns:
            List of dictionaries with item name, price, stock, and value
        """
        inventory = []
        
        for item_name, item_data in self.items.items():
            stock = item_data.get('stock', 0)
            price = item_data.get('price', 0)
            value = stock * price
            
            inventory.append({
                'name': item_name,
                'price': price,
                'stock': stock,
                'value': value
            })
        
        # Sort by value (highest first)
        inventory.sort(key=lambda x: x['value'], reverse=True)
        
        return inventory
    
    def get_inventory_data(self):
        """Get all inventory data
        
        Returns:
            List of dictionaries with inventory data
        """
        inventory_data = []
        
        for name, item in self.items.items():
            # Get item data
            price = item.get('price', 0)
            stock = item.get('stock', 0)
            value = price * stock
            
            # Create inventory item
            inventory_item = {
                'name': name,
                'price': price,
                'stock': stock,
                'value': value,
                'last_sold': self.get_last_sold_date(name),
                'price_adjustment': self.calculate_price_adjustment(name)
            }
            
            inventory_data.append(inventory_item)
            
        return inventory_data
    
    def get_last_sold_date(self, item_name):
        """Get the last sold date for an item
        
        Args:
            item_name: Name of the item
            
        Returns:
            Formatted date string or empty string if never sold
        """
        # Get sales history for this item
        sales = [entry for entry in self.ledger_entries 
                if entry.get('item_name') == item_name and 
                   entry.get('transaction_type') == 'sale']
        
        if not sales:
            return ""
            
        # Find the most recent sale time
        last_sale_timestamp = max(entry.get('timestamp', 0) for entry in sales)
        
        # Format the date
        from datetime import datetime
        date_str = datetime.fromtimestamp(last_sale_timestamp).strftime('%Y-%m-%d')
        return date_str
    
    def calculate_price_adjustment(self, item_name):
        """Calculate whether an item needs visual highlighting
        
        Args:
            item_name: Name of the item
            
        Returns:
            Dictionary with item highlighting data:
            {
                'recommended': True/False,
                'reason': str,
                'last_sale_days': float,
                'suggested_price': int
            }
        """
        if item_name not in self.items:
            return {'recommended': False}
            
        # Get item data
        item = self.items[item_name]
        current_price = item.get('price', 0)
        current_stock = item.get('stock', 0)
        
        # If no stock, no need for highlighting
        if current_stock == 0:
            return {'recommended': False}
            
        # Get sales history for this item
        sales = [entry for entry in self.ledger_entries 
                if entry.get('item_name') == item_name and 
                   entry.get('transaction_type') == 'sale']
        
        # Check when the last sale was
        now = time.time()
        last_sale_timestamp = None  # Start with None to detect if there have been no sales
        
        if sales:
            # Find the most recent sale time
            last_sale_timestamp = max(entry.get('timestamp', 0) for entry in sales)
            
        # Calculate days since last sale (or a very large number if never sold)
        days_since_last_sale = 999  # Default to a large number if never sold
        if last_sale_timestamp:
            days_since_last_sale = (now - last_sale_timestamp) / (60 * 60 * 24)
        
        result = {
            'recommended': False,
            'reason': '',
            'last_sale_days': days_since_last_sale,
            'suggested_price': current_price
        }
        
        # Only highlight if the item has stock and has never been sold
        if current_stock > 0 and not last_sale_timestamp:
            result['recommended'] = True
            result['reason'] = 'Never been sold'
            # No price suggestion - removed 10% discount heuristic
            result['suggested_price'] = current_price
                
        return result

    def update_price(self, item_name, new_price):
        """Update the price of an item in the database"""
        if item_name in self.items:
            # Get current price for logging
            old_price = self.items[item_name]['price']
            
            # Update the price
            self.items[item_name]['price'] = new_price
            
            # Add to ledger
            entry = {
                'timestamp': time.time(),
                'item_name': item_name,
                'old_price': old_price,
                'new_price': new_price,
                'transaction_type': 'price_update'
            }
            self.ledger_entries.append(entry)
            self.save_ledger()
            
            # Save the database
            self.save_items()
            
            return True
        return False
