"""
Storage system for the Python console RPG
Handles storing items in the cave home with category organization
"""

from typing import Dict, Any, List, Optional, Tuple
from inventory_system import ItemType, Item, InventorySystem

class StorageSystem:
    """Manages the cave home storage for items"""
    
    def __init__(self):
        self.storage: Dict[str, int] = {}  # item_name -> quantity
        self.max_storage_size = 500  # More generous storage capacity
        
    def add_item(self, inventory_system: InventorySystem, item_name: str, quantity: int = 1) -> bool:
        """Add item from inventory to storage"""
        if not inventory_system.has_item(item_name, quantity):
            return False
            
        # Check if storage has space
        if len(self.storage) >= self.max_storage_size and item_name not in self.storage:
            return False
            
        # Get item info to check stackability
        item = inventory_system.get_item_info(item_name)
        if not item:
            return False
            
        # Remove from inventory first
        if not inventory_system.remove_item(item_name, quantity):
            return False
            
        # Add to storage
        if item.stackable:
            current_quantity = self.storage.get(item_name, 0)
            new_quantity = min(current_quantity + quantity, item.max_stack)
            self.storage[item_name] = new_quantity
        else:
            # Non-stackable items
            if item_name not in self.storage:
                self.storage[item_name] = 1
            else:
                # Already have this unique item - should not happen normally
                # but we'll handle it by adding to inventory and returning False
                inventory_system.add_item(item_name, quantity)
                return False
                
        return True
        
    def withdraw_item(self, inventory_system: InventorySystem, item_name: str, quantity: int = 1) -> bool:
        """Move item from storage to inventory"""
        if item_name not in self.storage:
            return False
            
        current_quantity = self.storage[item_name]
        if current_quantity < quantity:
            return False
            
        # Try to add to inventory first
        if not inventory_system.add_item(item_name, quantity):
            return False
            
        # Remove from storage
        new_quantity = current_quantity - quantity
        if new_quantity <= 0:
            del self.storage[item_name]
        else:
            self.storage[item_name] = new_quantity
            
        return True
        
    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if storage has specified quantity of item"""
        return self.storage.get(item_name, 0) >= quantity
        
    def get_item_quantity(self, item_name: str) -> int:
        """Get quantity of specific item in storage"""
        return self.storage.get(item_name, 0)
        
    def get_items_by_type(self, inventory_system: InventorySystem, item_type: ItemType) -> Dict[str, int]:
        """Get all stored items of specific type"""
        result = {}
        for item_name, quantity in self.storage.items():
            item = inventory_system.get_item_info(item_name)
            if item and item.item_type == item_type:
                result[item_name] = quantity
        return result

        
    def get_storage_weight(self) -> int:
        """Calculate storage 'weight' (number of unique items)"""
        return len(self.storage)
        
    def is_storage_full(self) -> bool:
        """Check if storage is full"""
        return len(self.storage) >= self.max_storage_size
        
    def sort_storage(self, inventory_system: InventorySystem) -> Dict[str, Dict[str, int]]:
        """Get storage sorted by item type"""
        sorted_items = {}
        
        # Create categories for each item type
        for item_type in ItemType:
            sorted_items[item_type.value] = {}
        
        # Group items by type
        for item_name, quantity in self.storage.items():
            item = inventory_system.get_item_info(item_name)
            if item:
                sorted_items[item.item_type.value][item_name] = quantity
                
        return sorted_items
        
    def show_storage_menu(self, ui, player, inventory_system: InventorySystem):
        """Show storage management menu"""
        from main import GamePhase  # Import here to avoid circular import
        
        while True:
            ui.clear_screen()
            ui.display_header("Cave Storage")
            ui.show_storage_art()
            
            # Show storage summary
            ui.show_message(f"Storage Items: {len(self.storage)}/{self.max_storage_size}")
            
            if not self.storage:
                ui.show_message("Your storage is empty.")
                options = [
                    "1. Deposit Items",
                    "2. Back to Cave Home"
                ]
                choice = ui.show_menu("Storage Actions", options)
                
                if choice == "1":
                    self._handle_deposit_item(ui, player, inventory_system)
                elif choice == "2" or choice == "ESC":
                    return GamePhase.CAVE_HOME
                continue
                
            # Show categorized storage
            sorted_storage = self.sort_storage(inventory_system)
            self._display_categorized_storage(ui, sorted_storage)
            
            options = [
                "1. Deposit Item from Inventory",
                "2. Deposit All Unequipped Items",
                "3. Withdraw Item to Inventory",
                "4. View Item Details",
                "5. Back to Cave Home"
            ]
            
            choice = ui.show_menu("Storage Actions", options)
            
            if choice == "1":
                self._handle_deposit_item(ui, player, inventory_system)
            elif choice == "2":
                self._handle_deposit_all_unequipped(ui, player, inventory_system)
            elif choice == "3":
                self._handle_withdraw_item(ui, player, inventory_system)
            elif choice == "4":
                self._handle_view_item(ui, inventory_system)
            elif choice == "5" or choice == "ESC":
                return GamePhase.CAVE_HOME
                
    def _display_categorized_storage(self, ui, sorted_storage):
        """Display storage items organized by category"""
        ui.display_header("Storage Contents")
        
        category_names = {
            "weapon": "Weapons",
            "armor": "Armor",
            "accessory": "Accessories",
            "shield": "Shields",
            "consumable": "Consumables",
            "material": "Materials",
            "quest": "Key Items",
            "misc": "Miscellaneous"
        }
        
        empty_categories = True
        
        for category, items in sorted_storage.items():
            if items:
                empty_categories = False
                ui.show_message(f"\n{category_names.get(category, category.title())}:")
                for item_name, quantity in items.items():
                    # Get item info to determine rarity color
                    item = self.inventory_system.get_item_info(item_name)
                    if item:
                        # Get color code based on rarity
                        if item.rarity.value == "common":
                            ui.show_message(f"  {item_name}: {quantity}")
                        elif item.rarity.value == "uncommon":
                            ui.show_message(f"  {ui.Colors.GREEN}{item_name}{ui.Colors.RESET}: {quantity}")
                        elif item.rarity.value == "rare":
                            ui.show_message(f"  {ui.Colors.BLUE}{item_name}{ui.Colors.RESET}: {quantity}")
                        elif item.rarity.value == "epic":
                            ui.show_message(f"  {ui.Colors.MAGENTA}{item_name}{ui.Colors.RESET}: {quantity}")
                        elif item.rarity.value == "legendary":
                            ui.show_message(f"  {ui.Colors.YELLOW}{item_name}{ui.Colors.RESET}: {quantity}")
                        elif item.rarity.value == "mythical":
                            ui.show_message(f"  {ui.Colors.RED}{item_name}{ui.Colors.RESET}: {quantity}")
                        else:
                            ui.show_message(f"  {item_name}: {quantity}")
                    else:
                        ui.show_message(f"  {item_name}: {quantity}")
        
        if empty_categories:
            ui.show_message("No items stored.")
            
    def _handle_deposit_item(self, ui, player, inventory_system: InventorySystem):
        """Handle depositing an item to storage"""
        if not inventory_system.items:
            ui.show_message("Your inventory is empty!")
            ui.wait_for_input("Press Enter to continue...")
            return
            
        item_name = ui.show_item_selection(inventory_system.items)
        if item_name:
            quantity = inventory_system.get_item_quantity(item_name)
            if quantity > 1:
                try:
                    deposit_amount = int(ui.get_input(f"How many to deposit? (1-{quantity}): "))
                    if 1 <= deposit_amount <= quantity:
                        if self.add_item(inventory_system, item_name, deposit_amount):
                            ui.show_success(f"Deposited {deposit_amount}x {item_name} to storage")
                        else:
                            ui.show_error("Failed to deposit items!")
                    else:
                        ui.show_error("Invalid amount!")
                except ValueError:
                    ui.show_error("Please enter a valid number!")
            else:
                if self.add_item(inventory_system, item_name, 1):
                    ui.show_success(f"Deposited {item_name} to storage")
                else:
                    ui.show_error("Failed to deposit item!")
                    
            ui.wait_for_input("Press Enter to continue...")
            
    def _handle_withdraw_item(self, ui, player, inventory_system: InventorySystem):
        """Handle withdrawing an item from storage"""
        if not self.storage:
            ui.show_message("Your storage is empty!")
            ui.wait_for_input("Press Enter to continue...")
            return
            
        # Create a temporary dictionary for selection
        storage_items = {}
        for item_name, quantity in self.storage.items():
            storage_items[item_name] = quantity
            
        item_name = ui.show_item_selection(storage_items)
        if item_name:
            quantity = self.get_item_quantity(item_name)
            if quantity > 1:
                try:
                    withdraw_amount = int(ui.get_input(f"How many to withdraw? (1-{quantity}): "))
                    if 1 <= withdraw_amount <= quantity:
                        if self.withdraw_item(inventory_system, item_name, withdraw_amount):
                            ui.show_success(f"Withdrew {withdraw_amount}x {item_name} to inventory")
                        else:
                            ui.show_error("Failed to withdraw items! Inventory might be full.")
                    else:
                        ui.show_error("Invalid amount!")
                except ValueError:
                    ui.show_error("Please enter a valid number!")
            else:
                if self.withdraw_item(inventory_system, item_name, 1):
                    ui.show_success(f"Withdrew {item_name} to inventory")
                else:
                    ui.show_error("Failed to withdraw item! Inventory might be full.")
                    
            ui.wait_for_input("Press Enter to continue...")
            
    def _handle_view_item(self, ui, inventory_system: InventorySystem):
        """Handle viewing item details"""
        if not self.storage:
            return
            
        # Create a temporary dictionary for selection
        storage_items = {}
        for item_name, quantity in self.storage.items():
            storage_items[item_name] = quantity
            
        item_name = ui.show_item_selection(storage_items)
        if item_name:
            item = inventory_system.get_item_info(item_name)
            if item:
                ui.clear_screen()
                ui.display_header(f"Item Details: {item.name}")
                ui.show_message(f"Type: {item.item_type.value.title()}")
                ui.show_message(f"Rarity: {item.rarity.value.title()}")
                ui.show_message(f"Description: {item.description}")
                ui.show_message(f"Quantity in Storage: {self.storage[item_name]}")
                
                if item.stats and any(getattr(item.stats, attr) != 0 for attr in ['attack', 'defense', 'm_attack', 'm_defense', 'hp_bonus', 'mp_bonus']):
                    ui.show_message("\nStat Bonuses:")
                    if item.stats.attack > 0:
                        ui.show_message(f"  Attack: +{item.stats.attack}")
                    if item.stats.defense > 0:
                        ui.show_message(f"  Defense: +{item.stats.defense}")
                    if item.stats.m_attack > 0:
                        ui.show_message(f"  Magic Attack: +{item.stats.m_attack}")
                    if item.stats.m_defense > 0:
                        ui.show_message(f"  Magic Defense: +{item.stats.m_defense}")
                    if item.stats.hp_bonus > 0:
                        ui.show_message(f"  HP Bonus: +{item.stats.hp_bonus}")
                    if item.stats.mp_bonus > 0:
                        ui.show_message(f"  MP Bonus: +{item.stats.mp_bonus}")
                        
                ui.wait_for_input("Press Enter to continue...")
                
    def _handle_deposit_all_unequipped(self, ui, player, inventory_system: InventorySystem):
        """Handle depositing all unequipped items to storage"""
        if not inventory_system.items:
            ui.show_message("Your inventory is empty!")
            ui.wait_for_input("Press Enter to continue...")
            return
            
        # Get a list of equipped item names
        equipped_items = [item_name for item_name in player.equipment.values() if item_name]
        
        # Process each inventory item
        deposited_count = 0
        skipped_count = 0
        
        # Create a copy of the items dictionary to avoid modifying during iteration
        items_to_process = dict(inventory_system.items)
        
        for item_name, quantity in items_to_process.items():
            # Skip if item is equipped
            if item_name in equipped_items:
                skipped_count += 1
                continue
                
            # Try to deposit the item
            if self.add_item(inventory_system, item_name, quantity):
                deposited_count += 1
            else:
                skipped_count += 1
                
        if deposited_count > 0:
            ui.show_success(f"Deposited {deposited_count} types of items to storage")
        
        if skipped_count > 0:
            ui.show_message(f"Skipped {skipped_count} types of items (equipped or failed to deposit)")
            
        ui.wait_for_input("Press Enter to continue...")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert storage to dictionary for saving"""
        return {
            'storage': self.storage,
            'max_storage_size': self.max_storage_size
        }
        
    def load_from_dict(self, data: Dict[str, Any]):
        """Load storage from dictionary"""
        self.storage = data.get('storage', {})
        self.max_storage_size = data.get('max_storage_size', 500)