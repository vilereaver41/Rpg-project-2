"""
Bestiary system for the Python console RPG
Allows players to view information about encountered enemies.
"""

import os # For path joining
from typing import Dict, List, Optional, Set, Any

from enemy import EnemyDatabase, Enemy
from ui_manager import UIManager
from bestiary_utils import Colors, RARITY_COLORS, ZONE_NAME_COLORS, format_text_color, load_zone_data, get_zone_level_range_display, get_loot_rarity, get_enemy_loot_from_zone_file # Added get_enemy_loot_from_zone_file

# Define the base path for data files relative to this script
BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
ZONE_BESTIARY_PATH = os.path.join(BASE_DATA_PATH, "bestiary")


class Bestiary:
    """Manages discovered enemies and displays their information."""

    def __init__(self, enemy_db: EnemyDatabase):
        self.enemy_database = enemy_db
        self.discovered_enemies: Set[str] = set() # Stores internal ID names of discovered enemies
        self.discovered_gatherables: Dict[str, Set[str]] = {} # Tracks gathered resources by zone
        self.zones_data: Dict[str, Dict[str, Any]] = load_zone_data(ZONE_BESTIARY_PATH, self.enemy_database)


    def discover_enemy(self, enemy_id_name: str):
        """Mark an enemy (by its ID name) as discovered."""
        if enemy_id_name in self.enemy_database.enemies: # Check against internal ID names
            self.discovered_enemies.add(enemy_id_name)

    def get_discovered_enemy_display_names(self) -> List[str]:
        """Returns a sorted list of discovered enemy display names."""
        # We need to get the display name from the enemy object if possible,
        # or fall back to the ID name if not (though ideally all discovered enemies exist).
        display_names = []
        for enemy_id in sorted(list(self.discovered_enemies)):
            enemy_instance = self.enemy_database.create_enemy(enemy_id)
            if enemy_instance:
                display_names.append(enemy_instance.name) # Assuming Enemy.name is the display name
            else:
                display_names.append(enemy_id) # Fallback
        return display_names
    
    def get_discovered_enemy_ids(self) -> List[str]:
        """Returns a sorted list of discovered enemy ID names."""
        return sorted(list(self.discovered_enemies))

    def get_enemy_details(self, enemy_id_name: str) -> Optional[Enemy]:
        """
        Get the full Enemy object for a discovered enemy.
        Returns None if the enemy is not discovered or not in the database.
        """
        if enemy_id_name in self.discovered_enemies or enemy_id_name in self.enemy_database.enemies:
            # Allow viewing details for any enemy in the database if accessed via zone view,
            # or only discovered enemies if accessed via discovered list.
            return self.enemy_database.create_enemy(enemy_id_name)
        return None
        
    def discover_gatherable(self, zone_name: str, resource_name: str):
        """
        Record a resource that has been gathered in a specific zone.
        """
        if zone_name not in self.discovered_gatherables:
            self.discovered_gatherables[zone_name] = set()
        
        self.discovered_gatherables[zone_name].add(resource_name)
        
    def is_gatherable_discovered(self, zone_name: str, resource_name: str) -> bool:
        """
        Check if a specific resource has been discovered in a zone.
        """
        if zone_name not in self.discovered_gatherables:
            return False
        
        return resource_name in self.discovered_gatherables[zone_name]
        
    def get_discovered_gatherables(self, zone_name: str) -> Set[str]:
        """
        Get all discovered gatherables for a specific zone.
        """
        return self.discovered_gatherables.get(zone_name, set())

    def show_bestiary_menu(self, ui: UIManager, game: Any): # Added game parameter (type Any to avoid circular import with Game)
        """Handles the main UI interactions for the bestiary."""
        from main import GamePhase # Local import to avoid circular dependency with GamePhase

        while True:
            ui.clear_screen()
            ui.display_header("Bestiary")
            options = [
                "1. View Discovered Enemies",
                "2. View Enemies by Zone",
                "3. Back to Options"
            ]
            choice = ui.show_menu("Select an option:", options)

            if choice == 1:
                self._show_discovered_enemies_menu(ui, game) # Pass game instance
            elif choice == 2:
                self._show_bestiary_by_zone_menu(ui) # No game instance needed here
            elif choice == 3:
                return GamePhase.OPTIONS
            else:
                ui.show_error("Invalid choice. Please try again.")
                ui.wait_for_input()

    def _show_discovered_enemies_menu(self, ui: UIManager, game: Any): # Added game parameter
        """Shows the list of discovered enemies."""
        # from main import GamePhase # Not needed here as we return to main bestiary menu

        if not game.player: # Check if a player character exists
            ui.clear_screen()
            ui.display_header("Discovered Enemies - Access Denied")
            ui.show_message("A game must be started or loaded to view discovered enemies.")
            ui.wait_for_input("Press Enter to return to the Bestiary Menu...")
            return # Returns to show_bestiary_menu loop

        while True:
            ui.clear_screen()
            ui.display_header("Bestiary - Discovered Enemies")

            discovered_ids = self.get_discovered_enemy_ids()

            if not discovered_ids:
                ui.show_message("No enemies discovered yet.")
                ui.show_message("Defeat enemies in combat to add them to your bestiary.")
                ui.wait_for_input("Press Enter to return...")
                return # Return to main bestiary menu

            options = []
            for i, enemy_id in enumerate(discovered_ids):
                enemy = self.enemy_database.create_enemy(enemy_id)
                if enemy:
                    display_name = enemy.name
                    rarity_color = RARITY_COLORS.get(enemy.rarity.lower(), Colors.WHITE)
                    options.append(f"{i+1}. {rarity_color}{display_name}{Colors.RESET} (Lvl {enemy.stats.level})")
                else:
                    options.append(f"{i+1}. {enemy_id} (Error loading details)")

            options.append(f"{len(discovered_ids)+1}. Back")

            choice_num = ui.show_menu("Select an enemy to view details:", options)

            if choice_num is None:
                ui.show_error("Invalid input. Please enter a number.")
                ui.wait_for_input()
                continue
                
            if 1 <= choice_num <= len(discovered_ids):
                selected_enemy_id = discovered_ids[choice_num - 1]
                self._show_enemy_details_screen(ui, selected_enemy_id)
            elif choice_num == len(discovered_ids) + 1:
                return # Return to main bestiary menu
            else:
                ui.show_error("Invalid choice. Please try again.")
                ui.wait_for_input()

    def _show_bestiary_by_zone_menu(self, ui: UIManager):
        """Allows player to select a zone and view its enemies."""
        while True:
            ui.clear_screen()
            ui.display_header("Bestiary - Enemies by Zone")

            if not self.zones_data:
                ui.show_message("No zone data loaded. Check 'python_game/data/bestiary/' folder.")
                ui.wait_for_input("Press Enter to return...")
                return

            # Sort zones by level range (highest max level first)
            def get_sort_key(zone_name_key):
                zone_info = self.zones_data[zone_name_key]
                level_range_str = zone_info.get('file_level_range', 'N/A') # Use file_level_range
                
                max_lvl = -1 # Default for N/A or unparsable, sorts them lower
                min_lvl = -1

                if level_range_str != 'N/A':
                    try:
                        # Remove "Lv " prefix
                        level_range_str = level_range_str.replace("Lv ", "").strip()
                        if "-" in level_range_str:
                            parts = level_range_str.split("-")
                            min_lvl = int(parts[0])
                            max_lvl = int(parts[1])
                        else:
                            min_lvl = max_lvl = int(level_range_str)
                    except ValueError:
                        pass # Keep default -1 if parsing fails
                # Sort by max level (desc), then min level (desc), then name (asc)
                return (-max_lvl, -min_lvl, zone_name_key)

            sorted_zone_names = sorted(list(self.zones_data.keys()), key=get_sort_key)
            
            options = []
            for i, zone_name in enumerate(sorted_zone_names):
                zone_info = self.zones_data[zone_name]
                level_range_display = zone_info.get('file_level_range', zone_info.get('actual_level_range', 'N/A'))
                
                # Get color for zone name from bestiary_utils.ZONE_NAME_COLORS
                # Ensure the key lookup is case-insensitive and matches how keys are stored if necessary
                # Assuming zone_name is already in the correct format (e.g., "Shapira Plains")
                zone_color_code = ZONE_NAME_COLORS.get(zone_name.lower(), Colors.WHITE) # Use .lower() for robust key matching
                
                colored_zone_name = f"{zone_color_code}{zone_name}{Colors.RESET}"
                
                options.append(f"{i+1}. {colored_zone_name} ({level_range_display})")
            
            options.append(f"{len(sorted_zone_names)+1}. Back")

            choice_num = ui.show_menu("Select a zone:", options)

            if choice_num is None:
                ui.show_error("Invalid input. Please enter a number.")
                ui.wait_for_input()
                continue
                
            if 1 <= choice_num <= len(sorted_zone_names):
                selected_zone_name = sorted_zone_names[choice_num - 1]
                self._show_enemies_in_zone_screen(ui, selected_zone_name)
            elif choice_num == len(sorted_zone_names) + 1:
                return # Return to main bestiary menu
            else:
                ui.show_error("Invalid choice. Please try again.")
                ui.wait_for_input()

    def _show_enemies_in_zone_screen(self, ui: UIManager, zone_name: str):
        """Displays enemies for a selected zone."""
        zone_info = self.zones_data.get(zone_name)
        if not zone_info or not zone_info.get("enemies"):
            ui.show_error(f"No enemy data found for zone: {zone_name}")
            ui.wait_for_input()
            return

        enemies_in_zone = zone_info["enemies"] # This is already sorted by level, then name

        while True:
            ui.clear_screen()
            level_range_display = zone_info.get('actual_level_range', zone_info.get('file_level_range', 'N/A'))
            ui.display_header(f"Bestiary - {zone_name} ({level_range_display})")

            options = []
            enemy_id_list_for_selection = []

            for i, enemy_data in enumerate(enemies_in_zone):
                display_name = enemy_data.get("display_name", "Unknown")
                enemy_id = enemy_data.get("id_name", "")
                level = enemy_data.get("level", "N/A")
                rarity = enemy_data.get("rarity", "Common")
                
                # Color coding for rarity
                rarity_color = RARITY_COLORS.get(rarity.lower(), Colors.WHITE)
                colored_name = f"{rarity_color}{display_name}{Colors.RESET}"
                
                # Check if discovered
                discovered_marker = " (Discovered)" if enemy_id in self.discovered_enemies else ""
                
                options.append(f"{i+1}. {colored_name} (Lvl {level}){discovered_marker}")
                enemy_id_list_for_selection.append(enemy_id)

            options.append(f"{len(enemies_in_zone)+1}. Back to Zone List")

            choice_num = ui.show_menu("Select an enemy to view details:", options)

            if choice_num is None:
                ui.show_error("Invalid input. Please enter a number.")
                ui.wait_for_input()
                continue
                
            if 1 <= choice_num <= len(enemies_in_zone):
                selected_enemy_id = enemy_id_list_for_selection[choice_num - 1]
                if selected_enemy_id: # Ensure ID is valid
                    self._show_enemy_details_screen(ui, selected_enemy_id)
                else:
                    ui.show_error("Invalid enemy data.")
                    ui.wait_for_input()
            elif choice_num == len(enemies_in_zone) + 1:
                return # Return to zone list
            else:
                ui.show_error("Invalid choice. Please try again.")
                ui.wait_for_input()


    def _show_enemy_details_screen(self, ui: UIManager, enemy_id_name: str):
        """Displays detailed information for a single enemy by its ID name."""
        enemy = self.get_enemy_details(enemy_id_name)

        if not enemy:
            ui.show_error(f"Could not retrieve details for {enemy_id_name}.")
            ui.wait_for_input()
            return

        ui.clear_screen()
        
        rarity_color = RARITY_COLORS.get(enemy.rarity.lower(), Colors.WHITE)
        colored_name = f"{rarity_color}{enemy.name}{Colors.RESET}"
        ui.display_header(f"Bestiary - {colored_name}")


        ui.show_message(f"Name: {colored_name}")
        ui.show_message(f"Type: {enemy.type}")
        ui.show_message(f"Rarity: {format_text_color(enemy.rarity, enemy.rarity.lower())}") # Already uses format_text_color
        ui.show_message(f"Level: {enemy.stats.level}")
        
        ui.show_message(f"\n--- Stats ---")
        ui.show_message(f"  Max HP:        {enemy.stats.max_hp}")
        # Ensure max_mp exists and is a number before checking if > 0
        max_mp_display = 'N/A'
        if hasattr(enemy.stats, 'max_mp') and isinstance(enemy.stats.max_mp, (int, float)) and enemy.stats.max_mp > 0:
            max_mp_display = str(enemy.stats.max_mp)
        ui.show_message(f"  Max MP:        {max_mp_display}")
        ui.show_message(f"  Attack:        {enemy.stats.attack}")
        ui.show_message(f"  Defense:       {enemy.stats.defense}")
        ui.show_message(f"  Magic Attack:  {enemy.stats.m_attack}")
        ui.show_message(f"  Magic Defense: {enemy.stats.m_defense}")
        ui.show_message(f"  Agility:       {enemy.stats.agility}")
        ui.show_message(f"  Luck:          {enemy.stats.luck}")

        ui.show_message(f"\n--- Abilities ---")
        if enemy.abilities:
            for ability in enemy.abilities:
                if ability and ability.strip().upper() != "NULL": # Filter out NULL abilities
                    ui.show_message(f"  - {ability}")
        else:
            ui.show_message(f"  None known.")

        ui.show_message(f"\n--- Known Loot Drops ---")
        # Use zone file as source of truth for loot
        zone_file_path = None
        if hasattr(enemy, 'zone_file_path'):
            zone_file_path = enemy.zone_file_path
        elif hasattr(self, 'current_zone_file_path'):
            zone_file_path = self.current_zone_file_path
        if zone_file_path:
            loot_list = get_enemy_loot_from_zone_file(zone_file_path, enemy.id_name)
            if loot_list:
                for loot_item in loot_list:
                    ui.show_message(f"  - {format_text_color(loot_item, get_loot_rarity(loot_item))}")
            else:
                ui.show_message(f"  None known.")
        elif enemy.loot_table:
            valid_loot = [loot for loot in enemy.loot_table if loot and loot.strip().upper() != "NULL"]
            if valid_loot:
                for loot_item in valid_loot:
                    ui.show_message(f"  - {format_text_color(loot_item, get_loot_rarity(loot_item))}")
            else:
                ui.show_message(f"  None known.")
        else:
            ui.show_message(f"  None known.")
        
        # Placeholder for resistances/weaknesses if added later
        # ui.show_message(f"\n--- Resistances/Weaknesses ---")
        # ui.show_message(f"  Fire: Normal, Ice: Weak, etc.")

        ui.wait_for_input("\nPress Enter to return...")

    def to_dict(self) -> Dict[str, Any]:
        """Convert bestiary state to dictionary for saving."""
        # Convert set of gatherables to list for JSON serialization
        discovered_gatherables_dict = {}
        for zone, items in self.discovered_gatherables.items():
            discovered_gatherables_dict[zone] = list(items)
            
        return {
            "discovered_enemies": list(self.discovered_enemies), # Save internal ID names
            "discovered_gatherables": discovered_gatherables_dict # Save gatherables by zone
        }

    def load_from_dict(self, data: Dict[str, Any]):
        """Load bestiary state from dictionary."""
        self.discovered_enemies = set(data.get("discovered_enemies", []))
        
        # Convert lists back to sets for discovered_gatherables
        discovered_gatherables_dict = data.get("discovered_gatherables", {})
        self.discovered_gatherables = {}
        for zone, items in discovered_gatherables_dict.items():
            self.discovered_gatherables[zone] = set(items)