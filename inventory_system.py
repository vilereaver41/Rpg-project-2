"""
Inventory system for the Python console RPG
Handles item management, equipment, and consumables
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
from ui_manager import Colors # Added import for Colors

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    SHIELD = "shield"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST = "quest"
    MISC = "misc"

class ItemRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHICAL = "mythical"

@dataclass
class ItemStats:
    """Item stat bonuses"""
    attack: int = 0
    defense: int = 0
    m_attack: int = 0
    m_defense: int = 0
    hp_bonus: int = 0
    mp_bonus: int = 0
    agility_bonus: int = 0
    luck_bonus: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'attack': self.attack,
            'defense': self.defense,
            'm_attack': self.m_attack,
            'm_defense': self.m_defense,
            'hp_bonus': self.hp_bonus,
            'mp_bonus': self.mp_bonus,
            'agility_bonus': self.agility_bonus,
            'luck_bonus': self.luck_bonus
        }

@dataclass
class Item:
    """Represents an item in the game"""
    name: str
    item_type: ItemType
    rarity: ItemRarity
    description: str
    buy_price: int = 0
    sell_price: int = 0
    stats: Optional[ItemStats] = None
    consumable_effect: Optional[Dict[str, Any]] = None
    equipable_slot: Optional[str] = None
    stackable: bool = True
    max_stack: int = 99
    image_path: Optional[str] = None
    
    def __post_init__(self):
        if self.stats is None:
            self.stats = ItemStats()
        
        self._effect_handlers = {
            "heal_hp": self._apply_heal_hp,
            "restore_mp": self._apply_restore_mp,
            "unlock_crafting": self._apply_unlock_crafting_profession, # Renamed from unlock_profession for consistency
            "temp_stats": self._apply_temp_stats,
            "status_effect": self._apply_status_effect
        }
            
    def get_rarity_color(self) -> str:
        """Get ANSI color code for rarity"""
        rarity_colors = {
            ItemRarity.COMMON: Colors.WHITE,
            ItemRarity.UNCOMMON: Colors.GREEN,
            ItemRarity.RARE: Colors.BLUE,
            ItemRarity.EPIC: Colors.MAGENTA, # Changed from purple to magenta for consistency with ANSI
            ItemRarity.LEGENDARY: Colors.YELLOW, # Changed from orange to yellow
            ItemRarity.MYTHICAL: Colors.RED
        }
        return rarity_colors.get(self.rarity, Colors.WHITE)

    def get_formatted_details(self, quantity: int) -> List[str]:
        """Return a list of strings representing formatted item details."""
        details = []
        rarity_color = self.get_rarity_color()
        reset_color = Colors.RESET

        details.append(f"Type: {self.item_type.value.title()}")
        details.append(f"Rarity: {rarity_color}{self.rarity.value.title()}{reset_color}")
        details.append(f"Description: {self.description}")
        details.append(f"Quantity: {quantity}")

        if self.buy_price > 0:
            details.append(f"Buy Price: {self.buy_price} Gold")
        if self.sell_price > 0:
            details.append(f"Sell Price: {self.sell_price} Gold")

        if self.stats and any(
            getattr(self.stats, attr) != 0 for attr in ItemStats.__annotations__
        ):
            details.append("\nStat Bonuses:")
            if self.stats.attack != 0:
                details.append(f"  Attack: {self.stats.attack:+.0f}")
            if self.stats.defense != 0:
                details.append(f"  Defense: {self.stats.defense:+.0f}")
            if self.stats.m_attack != 0:
                details.append(f"  Magic Attack: {self.stats.m_attack:+.0f}")
            if self.stats.m_defense != 0:
                details.append(f"  Magic Defense: {self.stats.m_defense:+.0f}")
            if self.stats.hp_bonus != 0:
                details.append(f"  HP Bonus: {self.stats.hp_bonus:+.0f}")
            if self.stats.mp_bonus != 0:
                details.append(f"  MP Bonus: {self.stats.mp_bonus:+.0f}")
            if self.stats.agility_bonus != 0:
                details.append(f"  Agility Bonus: {self.stats.agility_bonus:+.0f}")
            if self.stats.luck_bonus != 0:
                details.append(f"  Luck Bonus: {self.stats.luck_bonus:+.0f}")
        
        if self.consumable_effect:
            details.append("\nConsumable Effects:")
            for effect, value in self.consumable_effect.items():
                details.append(f"  {effect.replace('_', ' ').title()}: {value}")

        if self.equipable_slot:
            details.append(f"Equipable Slot: {self.equipable_slot.title()}")
            
        return details

    def can_equip(self) -> bool:
        """Check if item can be equipped"""
        return self.item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY, ItemType.SHIELD]

    def _apply_heal_hp(self, player, amount: int) -> Tuple[bool, str]:
        healed = player.heal(amount)
        return True, f"Restored {healed} HP."

    def _apply_restore_mp(self, player, amount: int) -> Tuple[bool, str]:
        restored = player.restore_mp(amount)
        return True, f"Restored {restored} MP."

    def _apply_unlock_crafting_profession(self, player, profession_name: str) -> Tuple[bool, str]:
        # Assuming player.unlock_crafting_profession returns True on new unlock, False if already known
        if player.unlock_crafting_profession(profession_name):
            return True, f"You now understand the basics of {profession_name}."
        else:
            return True, f"You already know the basics of {profession_name}." # Still counts as successful use

    def _apply_temp_stats(self, player, stats_boost: Dict[str, Any]) -> Tuple[bool, str]:
        # Placeholder: Actual implementation would be in Player class
        # For now, just acknowledge the effect.
        # Example: player.apply_temporary_buff(stats_boost)
        print(f"Debug: Applying temporary stats: {stats_boost} to {player.name if hasattr(player, 'name') else 'player'}")
        # In a real scenario, this might involve adding a buff to the player that expires.
        # For now, we'll assume it's always "successful" in terms of dispatch.
        return True, "Temporary stat boost applied (not fully implemented)."

    def _apply_status_effect(self, player, effect_details: Dict[str, Any]) -> Tuple[bool, str]:
        # Assuming player.add_status_effect exists and handles the logic
        # The effect_details might be a dictionary like {"name": "Poison", "duration": 5, "potency": 2}
        player.add_status_effect(effect_details) # This was the old call
        effect_name = effect_details.get("name", "Unknown Effect")
        return True, f"Applied status effect: {effect_name}."

    def use_item(self, player) -> Tuple[bool, List[str]]:
        """
        Use a consumable item.
        Returns a tuple: (bool_success, list_of_messages)
        """
        if self.item_type != ItemType.CONSUMABLE or not self.consumable_effect:
            return False, ["Item cannot be used or has no effect."]

        effects_applied_count = 0
        messages = []

        for effect_key, effect_value in self.consumable_effect.items():
            handler = self._effect_handlers.get(effect_key)
            if handler:
                try:
                    applied, message = handler(player, effect_value)
                    if applied:
                        effects_applied_count += 1
                        messages.append(message)
                except Exception as e:
                    messages.append(f"Error applying effect '{effect_key}': {e}")
                    print(f"Warning: Error during effect '{effect_key}' for item '{self.name}': {e}") # Log for dev
            else:
                messages.append(f"Warning: No handler for effect '{effect_key}' on item '{self.name}'.")
                print(f"Warning: No handler for effect '{effect_key}' on item '{self.name}'")
        
        return effects_applied_count > 0, messages
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary"""
        return {
            'name': self.name,
            'item_type': self.item_type.value,
            'rarity': self.rarity.value,
            'description': self.description,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'stats': self.stats.to_dict() if self.stats else {},
            'consumable_effect': self.consumable_effect,
            'equipable_slot': self.equipable_slot,
            'stackable': self.stackable,
            'max_stack': self.max_stack,
            'image_path': self.image_path
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Create item from dictionary"""
        stats_data = data.get('stats', {})
        stats = ItemStats(**stats_data) if stats_data else ItemStats() # Ensure ItemStats is always created
        
        return cls(
            name=data['name'],
            item_type=ItemType(data['item_type']),
            rarity=ItemRarity(data['rarity']),
            description=data['description'],
            buy_price=data.get('buy_price', 0),
            sell_price=data.get('sell_price', 0),
            stats=stats,
            consumable_effect=data.get('consumable_effect'),
            equipable_slot=data.get('equipable_slot'),
            stackable=data.get('stackable', True),
            max_stack=data.get('max_stack', 99),
            image_path=data.get('image_path')
        )

class InventorySystem:
    """Manages player inventory and equipment"""
    
    def __init__(self):
        self.items: Dict[str, int] = {}  # item_name -> quantity
        self.item_database = self._create_item_database()
        self.max_inventory_size = 100
        
        # We'll add books from the Dropped.csv instead of directly here
        
    def _create_item_database(self) -> Dict[str, Item]:
        """Create database of all available items by loading from JSON file."""
        items_db = {}
        file_path = "data/game_data/items.json"
        try:
            with open(file_path, 'r') as f:
                items_data = json.load(f)
            
            if not isinstance(items_data, list):
                print(
                    f"Error: Expected a list of items in {file_path}, "
                    f"but got {type(items_data)}"
                )
                return items_db

            for item_data in items_data:
                try:
                    item = Item.from_dict(item_data)
                    items_db[item.name] = item
                except KeyError as e:
                    error_message = (
                        f"Error: Missing key '{e}' in item data in {file_path}.\n"
                        f"Problematic item data (first 200 chars): {str(item_data)[:200]}"
                    )
                    print(error_message)
                except ValueError as e: # Handles incorrect enum values
                    error_message = (
                        f"Error: Invalid value for enum in item data in {file_path}.\n"
                        f"Details: {e}\n"
                        f"Problematic item data (first 200 chars): {str(item_data)[:200]}"
                    )
                    print(error_message)
                except Exception as e:
                    error_message = (
                        f"Error: Could not parse item data in {file_path}.\n"
                        f"Details: {e}\n"
                        f"Problematic item data (first 200 chars): {str(item_data)[:200]}"
                    )
                    print(error_message)

        except FileNotFoundError:
            print(
                f"Error: Item database file not found at {file_path}. "
                "No items loaded."
            )
            # Potentially, load some default items or raise an error
        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from {file_path}. "
                "Check file for syntax errors."
            )
        except Exception as e:
            error_message = (
                f"An unexpected error occurred while loading items from {file_path}:\n"
                f"Details: {e}"
            )
            print(error_message)

        return items_db

    def add_item(self, item_name: str, quantity: int = 1) -> bool:
        """Add item to inventory"""
        # Allow adding unknown items (not in item_database) as generic items
        if item_name not in self.item_database:
            # Add as unknown if not present
            if item_name not in self.items:
                self.items[item_name] = 0
            self.items[item_name] += quantity
            return True
            
        item = self.item_database[item_name]
        
        # Check if inventory has space
        if len(self.items) >= self.max_inventory_size and item_name not in self.items:
            return False
            
        if item.stackable:
            current_quantity = self.items.get(item_name, 0)
            new_quantity = min(current_quantity + quantity, item.max_stack)
            self.items[item_name] = new_quantity
        else:
            # Non-stackable items
            if item_name not in self.items:
                self.items[item_name] = 1
            else:
                # Already have this unique item
                return False
                
        return True
        
    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item from inventory"""
        if item_name not in self.items:
            return False
            
        current_quantity = self.items[item_name]
        if current_quantity < quantity:
            return False
            
        new_quantity = current_quantity - quantity
        if new_quantity <= 0:
            del self.items[item_name]
        else:
            self.items[item_name] = new_quantity
            
        return True
        
    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if inventory has specified quantity of item"""
        return self.items.get(item_name, 0) >= quantity
        
    def get_item_quantity(self, item_name: str) -> int:
        """Get quantity of specific item"""
        return self.items.get(item_name, 0)
        
    def get_item_info(self, item_name: str) -> Optional[Item]:
        """Get item information, or a generic item for unknowns"""
        if item_name in self.item_database:
            return self.item_database[item_name]
        # Return a generic item for unknowns so UI and use_item still work
        return Item(
            name=item_name,
            item_type=ItemType.CONSUMABLE,  # treat unknowns as consumable for menu
            rarity=ItemRarity.COMMON,
            description="Unknown item",
            stackable=True,
            max_stack=99
        )
        
    def get_items_by_type(self, item_type: ItemType) -> Dict[str, int]:
        """Get all items of specific type"""
        result = {}
        for item_name, quantity in self.items.items():
            item = self.item_database.get(item_name)
            if item and item.item_type == item_type:
                result[item_name] = quantity
        return result
        
    def get_consumable_items(self) -> Dict[str, int]:
        """Get all consumable items, including unknowns"""
        result = self.get_items_by_type(ItemType.CONSUMABLE)
        # Add unknowns as consumables so they show up in the menu
        for item_name, quantity in self.items.items():
            if item_name not in self.item_database:
                result[item_name] = quantity
        return result
        
    def get_equipment_items(self) -> Dict[str, int]:
        """Get all equipment items"""
        equipment = {}
        for item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY, ItemType.SHIELD]:
            equipment.update(self.get_items_by_type(item_type))
        return equipment
        
    def use_consumable(self, item_name: str, player) -> Dict[str, Any]:
        """Use a consumable item. Returns a dict for UI feedback."""
        if not self.has_item(item_name):
            return {'success': False, 'message': 'Item not in inventory'}
            
        item = self.get_item_info(item_name)
        if not item or item.item_type != ItemType.CONSUMABLE:
            return {'success': False, 'message': 'Item is not consumable'}
            
        # Use the item
        # Item.use_item now returns (bool_success, list_of_messages)
        success, messages = item.use_item(player)
        
        # Construct the result dictionary for UI
        # The main message can be a summary or the first message.
        # For simplicity, let's join messages if multiple, or use a generic one.
        if success:
            self.remove_item(item_name, 1)
            display_message = f"Used {item_name}."
            if messages:
                display_message += " " + " ".join(messages)
            return {'success': True, 'message': display_message}
        else:
            # If use_item returned False, messages might contain reasons or warnings
            error_message = f"Could not use {item_name}."
            if messages:
                error_message += " " + " ".join(messages)
            return {'success': False, 'message': error_message}
        
    def add_all_profession_books(self):
        """Add all profession books to inventory (for testing)"""
        profession_books = [
            "Introduction to Alchemy",
            "Introduction to Blacksmithing",
            "Introduction to Cloth Work",
            "Introduction to Cooking",
            "Introduction to Lapidary",
            "Introduction to Leatherwork",
            "Introduction to Woodworking"
        ]
        
        for book in profession_books:
            if not self.has_item(book):
                self.add_item(book, 1)
    
        
    def get_inventory_weight(self) -> int:
        """Calculate inventory 'weight' (number of unique items)"""
        return len(self.items)
        
    def is_inventory_full(self) -> bool:
        """Check if inventory is full"""
        return len(self.items) >= self.max_inventory_size
        
    def sort_inventory(self) -> Dict[str, int]:
        """Get inventory sorted by item type and name, including unknown items"""
        sorted_items = {}
        type_priority = {
            ItemType.WEAPON: 1,
            ItemType.ARMOR: 2,
            ItemType.SHIELD: 3,
            ItemType.ACCESSORY: 4,
            ItemType.CONSUMABLE: 5,
            ItemType.MATERIAL: 6,
            ItemType.QUEST: 7,
            ItemType.MISC: 8
        }
        grouped = {}
        unknown_items = {}
        for item_name, quantity in self.items.items():
            item = self.get_item_info(item_name)
            if item:
                item_type = item.item_type
                if item_type not in grouped:
                    grouped[item_type] = {}
                grouped[item_type][item_name] = quantity
            else:
                unknown_items[item_name] = quantity
        for item_type in sorted(grouped.keys(), key=lambda x: type_priority.get(x, 99)):
            for item_name in sorted(grouped[item_type].keys()):
                sorted_items[item_name] = grouped[item_type][item_name]
        # Add unknown items at the end
        for item_name in sorted(unknown_items.keys()):
            sorted_items[item_name] = unknown_items[item_name]
        return sorted_items
        
    def show_inventory_menu(self, ui, player):
        """Show inventory management menu"""
        from main import GamePhase  # Import here to avoid circular import
        
        while True:
            ui.clear_screen()
            ui.display_header("Inventory")
            
            # Show inventory summary
            ui.show_message(f"Items: {len(self.items)}/{self.max_inventory_size}")
            
            if not self.items:
                ui.show_message("Your inventory is empty.")
                ui.wait_for_input("Press Enter to return...")
                return GamePhase.CAVE_HOME
                
            # Show items
            sorted_items = self.sort_inventory()
            ui.show_inventory_summary(sorted_items)
            
            options = [
                "1. Use Item",
                "2. View Item Details",
                "3. Drop Item",
                "4. Sort by Type",
                "5. View Stats",
                "6. Back"
            ]
            
            choice = ui.show_menu("Inventory Actions", options)
            
            if str(choice) == "1":
                self._handle_use_item(ui, player)
            elif str(choice) == "2":
                self._handle_view_item(ui)
            elif str(choice) == "3":
                self._handle_drop_item(ui)
            elif str(choice) == "4":
                ui.show_message("Inventory sorted by type!")
                ui.wait_for_input("Press Enter to continue...")
            elif str(choice) == "5":
                self.ui.show_player_stats(player)
                ui.wait_for_input("Press Enter to continue...")
            elif str(choice) == "6" or str(choice).upper() == "ESC":
                return GamePhase.CAVE_HOME
                
    def _handle_use_item(self, ui, player):
        """Handle using an item"""
        consumables = self.get_consumable_items()
        if not consumables:
            ui.show_message("No consumable items available!")
            ui.wait_for_input("Press Enter to continue...")
            return
            
        item_name = ui.show_item_selection(consumables)
        if item_name:
            result = self.use_consumable(item_name, player)
            if result['success']:
                ui.show_success(result['message'])
            else:
                ui.show_error(result['message'])
            ui.wait_for_input("Press Enter to continue...")
            
    def _handle_view_item(self, ui):
        """Handle viewing item details"""
        if not self.items:
            return
            
        item_name = ui.show_item_selection(self.items)
        if item_name:
            item = self.get_item_info(item_name)
            if item:
                ui.clear_screen()
                ui.display_header(f"Item Details: {item.name}")
                
                item_quantity = self.items.get(item_name, 0)
                formatted_details = item.get_formatted_details(item_quantity)
                
                for detail_line in formatted_details:
                    # We need to handle color tags if UIManager doesn't directly.
                    # For now, assuming Item.get_formatted_details returns strings with ANSI codes.
                    ui.show_message(detail_line)
                                
                ui.wait_for_input("Press Enter to continue...")

    def _handle_drop_item(self, ui):
        """Handle dropping an item"""
        if not self.items:
            return
            
        item_name = ui.show_item_selection(self.items)
        if item_name:
            quantity = self.items[item_name]
            if quantity > 1:
                try:
                    drop_amount = int(ui.get_input(f"How many to drop? (1-{quantity}): "))
                    if 1 <= drop_amount <= quantity:
                        if ui.confirm(f"Drop {drop_amount}x {item_name}?"):
                            self.remove_item(item_name, drop_amount)
                            ui.show_success(f"Dropped {drop_amount}x {item_name}")
                    else:
                        ui.show_error("Invalid amount!")
                except ValueError:
                    ui.show_error("Please enter a valid number!")
            else:
                if ui.confirm(f"Drop {item_name}?"):
                    self.remove_item(item_name, 1)
                    ui.show_success(f"Dropped {item_name}")
                    
            ui.wait_for_input("Press Enter to continue...")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert inventory to dictionary for saving"""
        return {
            'items': self.items,
            'max_inventory_size': self.max_inventory_size
        }
        
    def load_from_dict(self, data: Dict[str, Any]):
        """Load inventory from dictionary"""
        self.items = data.get('items', {})
        self.max_inventory_size = data.get('max_inventory_size', 100)