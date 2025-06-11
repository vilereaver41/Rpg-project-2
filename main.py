#!/usr/bin/env python3
"""
Main entry point for the Python console-based RPG
Converted from JavaScript browser game to Python console game
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from player import Player # PlayerData removed
from game_state import GameState
from ui_manager import UIManager
from combat_system import CombatSystem, CombatResult
from inventory_system import InventorySystem
from save_system import SaveSystem
from zone_system import ZoneSystem
from storage_system import StorageSystem  # Added for cave home storage
from enemy import EnemyDatabase # Added for Bestiary
from bestiary import Bestiary # Added for Bestiary
from bestiary_utils import ZONE_NAME_COLORS, Colors, RARITY_COLORS # Moved from local imports

class GamePhase(Enum):
    MAIN_MENU = "main_menu"
    CHARACTER_CREATION = "character_creation"
    STAT_ALLOCATION = "stat_allocation"
    CAVE_HOME = "cave_home"
    TRAVEL_MENU = "travel_menu"
    ZONE_ACTIONS = "zone_actions"
    COMBAT = "combat"
    INVENTORY = "inventory"
    STORAGE = "storage"
    CRAFTING = "crafting"
    OPTIONS = "options"
    BESTIARY = "bestiary" # Added for Bestiary

class Game:
    """Main game controller class"""

    # Stat Names (used as keys and for display)
    STRENGTH = "strength"
    VITALITY = "vitality"
    WISDOM = "wisdom"
    INTELLIGENCE = "intelligence"
    AGILITY = "agility"
    DEXTERITY = "dexterity"
    LUCK = "luck"

    # Ordered list for consistent display and mapping configuration
    ORDERED_STATS_CONFIG = [
        (STRENGTH, "Attack +1.30"),
        (VITALITY, "Max HP +9, Defense +1.20"),
        (WISDOM, "Restorative Magic +1, Magic Defense +1"),
        (INTELLIGENCE, "Max MP +5, Magic Attack +1"),
        (AGILITY, "Dodge +0.50, Attack +0.10"),
        (DEXTERITY, "Crit Rate +0.50, Dodge +0.10"),
        (LUCK, "Discovery +0.50"),
    ]

    # Menu choice keys (as strings)
    STAT_MENU_CHOICE_RESET_KEY = "8"
    STAT_MENU_CHOICE_CONFIRM_KEY = "9"
    
    def __init__(self):
        self._initialize_stat_allocation_data()
        self.ui = UIManager()
        self.game_state = GameState()
        self.player: Optional[Player] = None
        self.enemy_database = EnemyDatabase()
        self.bestiary = Bestiary(enemy_db=self.enemy_database)
        self.combat_system = CombatSystem(bestiary=self.bestiary) # Pass bestiary to CombatSystem
        self.inventory_system = InventorySystem()
        self.storage_system = StorageSystem()
        self.save_system = SaveSystem()
        self.zone_system = ZoneSystem(enemy_db=self.enemy_database)
        self.current_phase = GamePhase.MAIN_MENU
        self.running = True

    def _go_back_one_phase(self):
        """Navigate to the previous game phase."""
        if len(self.phase_history) > 1:
            self.phase_history.pop()
            self.current_phase = self.phase_history[-1]

    def start(self):
        """Start the game"""
        self.ui.clear_screen()
        self.ui.show_title()

        # Track previous game phases for ESC key navigation
        self.phase_history = [GamePhase.MAIN_MENU]

        # Game phase dispatch dictionary
        self.phase_handlers = {
            GamePhase.MAIN_MENU: self.handle_main_menu,
            GamePhase.CHARACTER_CREATION: self.handle_character_creation,
            GamePhase.STAT_ALLOCATION: self.handle_stat_allocation,
            GamePhase.CAVE_HOME: self.handle_cave_home,
            GamePhase.TRAVEL_MENU: self.handle_travel_menu,
            GamePhase.ZONE_ACTIONS: self.handle_zone_actions,
            GamePhase.COMBAT: self.handle_combat,
            GamePhase.INVENTORY: self.handle_inventory,
            GamePhase.STORAGE: self.handle_storage,
            GamePhase.CRAFTING: self.handle_crafting,
            GamePhase.OPTIONS: self.handle_options,
            GamePhase.BESTIARY: self.handle_bestiary,
        }
        
        while self.running:
            try:
                # Always check for ESC key
                if self.ui.check_for_esc():
                    self._go_back_one_phase()
                    continue
                
                handler = self.phase_handlers.get(self.current_phase)
                if handler:
                    handler()
                else:
                    self.ui.show_error("Unknown game phase!")
                    self.current_phase = GamePhase.MAIN_MENU
                    self.phase_history = [GamePhase.MAIN_MENU]
                    
            except KeyboardInterrupt:
                self._prompt_confirmation_and_change_phase(
                    prompt_message="Are you sure you want to quit via Ctrl+C?",
                    confirm_action=lambda: setattr(self, 'running', False),
                    cancel_phase=None # Stay in current phase if cancelled
                )
            except Exception as e:
                self.ui.show_error(f"An error occurred: {e}")
                self.ui.wait_for_input("Press Enter to continue...")
                
        self.ui.show_message("Thanks for playing!")
        
    def handle_main_menu(self):
        """Handle main menu interactions"""
        self.ui.clear_screen()
        self.ui.show_title()
        
        options = [
            "1. New Game",
            "2. Load Game", 
            "3. Options",
            "4. Credits",
            "5. Quit"
        ]
        
        choice = self.ui.show_menu("Main Menu", options)
        
        if choice == 1:
            self.start_new_game()
        elif choice == 2:
            self.load_game()
        elif choice == 3:
            self.change_phase(GamePhase.OPTIONS)
        elif choice == 4:
            self.show_credits()
        elif choice == 5:
            self._prompt_confirmation_and_change_phase(
                prompt_message="Are you sure you want to quit?",
                confirm_action=lambda: setattr(self, 'running', False),
                cancel_phase=None
            )
                
    def _prompt_confirmation_and_change_phase(self, prompt_message: str, confirm_action: callable, cancel_phase: Optional[GamePhase] = None, confirm_phase: Optional[GamePhase] = None) -> bool:
        """
        Displays a confirmation dialog and performs an action or changes phase based on user input.
        
        Args:
            prompt_message: The message to display in the confirmation dialog.
            confirm_action: A callable to execute if the user confirms.
                            This can be a phase change or any other action (e.g., setting self.running = False).
            cancel_phase: The phase to switch to if the user cancels. If None, stays in the current phase.
            confirm_phase: The phase to switch to AFTER the confirm_action is executed. If None, no phase change after action.
            
        Returns:
            True if the user confirmed the action, False otherwise.
        """
        if self.ui.confirm(prompt_message):
            confirm_action()
            if confirm_phase:
                self.change_phase(confirm_phase)
            return True
        elif cancel_phase:
            self.change_phase(cancel_phase)
        # If cancel_phase is None and user cancels, nothing happens, stays in current phase.
        return False

    def change_phase(self, new_phase):
        """Change game phase and update history"""
        if new_phase != self.current_phase:
            self.phase_history.append(new_phase)
            self.current_phase = new_phase
            
    def return_to_phase(self, target_phase):
        """Return to a specific phase, removing all intervening phases"""
        if target_phase in self.phase_history:
            while self.phase_history[-1] != target_phase:
                self.phase_history.pop()
            self.current_phase = target_phase
        else:
            self.phase_history.append(target_phase)
            self.current_phase = target_phase
    
    def start_new_game(self):
        """Start a new game"""
        self.player = None
        self.game_state.reset()
        
        # Clear and recreate inventory system with profession books for testing
        self.inventory_system = InventorySystem()
        # TODO: Consider making this conditional or moving to a dedicated test/debug setup.
        self.inventory_system.add_all_profession_books()
        
        self.change_phase(GamePhase.CHARACTER_CREATION)
        
    def load_game(self):
        """Load a saved game"""
        try:
            save_data = self.save_system.load_game()
            if save_data:
                self.player = Player.from_dict(save_data['player'])
                self.game_state.load_from_dict(save_data['game_state'])
                self.inventory_system.load_from_dict(save_data['inventory'])
                if 'storage' in save_data:
                    self.storage_system.load_from_dict(save_data['storage'])
                self.zone_system.load_from_dict(save_data.get('zone_system', {}))
                self.bestiary.load_from_dict(save_data.get('bestiary', {}))

                # Ensure profession books are present if profession not unlocked
                profession_books = [
                    ("Introduction to Alchemy", "Alchemy"),
                    ("Introduction to Blacksmithing", "Blacksmithing"),
                    ("Introduction to Cloth Work", "Cloth Work"),
                    ("Introduction to Cooking", "Cooking"),
                    ("Introduction to Lapidary", "Lapidary"),
                    ("Introduction to Leatherwork", "Leatherwork"),
                    ("Introduction to Woodworking", "Woodworking"),
                ]
                for book, profession in profession_books:
                    # Check both inventory and if the book was previously used (profession unlocked)
                    if profession not in self.player.unlocked_crafting_professions:
                        # Always add the book if not present, even if inventory is full (force add)
                        if not self.inventory_system.has_item(book):
                            # Try to add, but if inventory is full, forcibly insert
                            added = self.inventory_system.add_item(book, 1)
                            if not added:
                                # Force insert if inventory is full and book is missing
                                self.inventory_system.items[book] = 1

                self.ui.show_message("Game loaded successfully!")
                self.change_phase(GamePhase.CAVE_HOME)
            else:
                self.ui.show_message("No saved game found.")
        except FileNotFoundError:
            self.ui.show_error("Failed to load game: Save file not found.")
        except json.JSONDecodeError:
            self.ui.show_error("Failed to load game: Save file is corrupted (invalid JSON format).")
        except KeyError as e:
            self.ui.show_error(f"Failed to load game: Save file is corrupted (missing data: {e}).")
        except Exception as e:
            self.ui.show_error(f"Failed to load game: An unexpected error occurred: {e}")
            
    def handle_character_creation(self):
        """Handle character creation"""
        self.ui.clear_screen()
        self.ui.display_header("Character Creation")
        
        name = self.ui.get_input("Enter your character's name: ").strip()
        if not name:
            self.ui.show_error("Name cannot be empty!")
            return
            
        gender_options = ["1. Male", "2. Female"]
        gender_choice = self.ui.show_menu("Select Gender", gender_options)
        gender = "Male" if gender_choice == "1" else "Female"
        
        self.player = Player(name, gender)
        self.ui.show_message(f"Character '{name}' ({gender}) created!")
        if self.ui.wait_for_input("Press Enter to continue to stat allocation...") == "ESC":
            self._go_back_one_phase()
        else:
            self.change_phase(GamePhase.STAT_ALLOCATION)

    def _initialize_stat_allocation_data(self):
        """Initializes data structures for stat allocation."""
        self.stat_choice_to_name_map: Dict[str, str] = {}
        self.stat_allocation_menu_items: list[str] = []

        for i, (stat_name, description) in enumerate(Game.ORDERED_STATS_CONFIG):
            choice_key = str(i + 1)
            self.stat_choice_to_name_map[choice_key] = stat_name
            self.stat_allocation_menu_items.append(f"{choice_key}. {stat_name.title()} ({description})")
        
        self.stat_allocation_menu_items.append(f"{Game.STAT_MENU_CHOICE_RESET_KEY}. Reset Stats")
        self.stat_allocation_menu_items.append(f"{Game.STAT_MENU_CHOICE_CONFIRM_KEY}. Confirm Allocation")

    def _display_stat_allocation_ui(self):
        """Displays the UI elements for stat allocation."""
        if not self.player: return
        self.ui.clear_screen()
        self.ui.display_header(f"{self.player.name}'s Stat Allocation")
        self.ui.show_player_stats(self.player)
        self.ui.show_message(f"Free Points: {self.player.free_points}")
        self.ui.show_message("\nTIP: To add points enter the stat number (e.g. '1')")
        self.ui.show_message("     To remove points enter the stat number followed by -amount (e.g. '1 -1')")

    def _get_stat_allocation_options(self) -> list[str]:
        """Returns the list of menu options for stat allocation."""
        return self.stat_allocation_menu_items

    def _process_stat_allocation_input(self, full_choice: str, stat_choice_key: str):
        """Processes user input for allocating stat points."""
        if not self.player: return
        stat_name = self.stat_choice_to_name_map[stat_choice_key]
        
        points_to_add = 1 # Default to adding 1 point
        choice_parts = full_choice.split()
        
        if len(choice_parts) > 1: # If more than just the stat number is provided (e.g., "1 -1")
            try:
                points_to_add = int(choice_parts[1])
            except ValueError:
                self.ui.show_error("Invalid format for points! Use 'number' or 'number -amount'.")
                return

        if points_to_add > 0 and self.player.free_points < points_to_add:
            self.ui.show_error("Not enough free points!")
            return

        if self.player.allocate_stat_point(stat_name, points_to_add):
            if points_to_add > 0:
                self.ui.show_success(f"Added {points_to_add} point(s) to {stat_name.title()}")
            else:
                self.ui.show_success(f"Removed {abs(points_to_add)} point(s) from {stat_name.title()}")
            self.player.calculate_secondary_stats() # Update secondary stats immediately
        else:
            if points_to_add < 0:
                # Check if the stat is already at its base or minimum
                current_stat_value = getattr(self.player.base_stats, stat_name)
                # Assuming base stats are the minimum, or Player.allocate_stat_point handles this
                self.ui.show_error(f"Cannot remove points from {stat_name.title()} (at or below base value).")
            else:
                # This case might occur if allocate_stat_point has other internal logic preventing allocation
                self.ui.show_error(f"Could not allocate points to {stat_name.title()}.")

    def _handle_stat_reset(self):
        """Handles resetting player stats."""
        if not self.player: return
        self.player.reset_stats()
        self.player.calculate_secondary_stats() # Recalculate after reset
        self.ui.show_message("Stats reset!")

    def _finalize_stats_and_proceed(self):
        """Finalizes stat allocation and proceeds to the next game phase or stays."""
        if not self.player: return
        self.player.calculate_secondary_stats() # Ensure secondary stats are current
        self.player.current_hp = self.player.secondary_stats.max_hp
        self.player.current_mp = self.player.secondary_stats.max_mp
        self.ui.show_message("Stats confirmed!")
        
        if self.ui.wait_for_input("Press Enter to enter your cave home...") != "ESC":
            self.change_phase(GamePhase.CAVE_HOME)
        # If "ESC" is pressed, phase remains STAT_ALLOCATION, and handle_stat_allocation will return,
        # effectively staying on the screen for the next iteration of the main game loop.
        
    def handle_stat_allocation(self):
        """Handle stat point allocation using helper methods."""
        if not self.player:
            self.change_phase(GamePhase.CHARACTER_CREATION)
            return
            
        while True:
            self._display_stat_allocation_ui()
            
            if self.player.free_points == 0:
                # Recalculate and re-display to show final secondary stats before confirmation
                self.player.calculate_secondary_stats()
                self._display_stat_allocation_ui() # Show updated stats
                
                # Use the new helper method for confirmation
                confirmed = self._prompt_confirmation_and_change_phase(
                    prompt_message="You have allocated all points. Continue to confirm?",
                    confirm_action=self._finalize_stats_and_proceed, # This will handle phase change or staying
                    cancel_phase=None # Stay in stat allocation if "No"
                )
                if confirmed: # If _finalize_stats_and_proceed led to a phase change or intended exit
                    # Check if phase actually changed, or if _finalize_stats_and_proceed decided to stay
                    # This logic is now mostly handled within _finalize_stats_and_proceed
                    return # Exit handler


            options = self._get_stat_allocation_options()
            # Use the new UI method that returns raw string input
            choice_str = self.ui.display_menu_for_string_input("Allocate Stat Points", options)
            
            if choice_str.upper() == "ESC": # Handle ESC input if it comes as a string
                confirmed_exit = self._prompt_confirmation_and_change_phase(
                    prompt_message="Exit stat allocation? Changes will be lost if not confirmed.",
                    confirm_action=self._go_back_one_phase, # Action is to go back
                    cancel_phase=None # Stay in stat allocation if "No"
                )
                if confirmed_exit:
                    return # Exit handler as phase has changed
                else:
                    continue # Restart loop to re-display UI
            
            # Process the raw string input
            # stat_choice_key will be the first part of the input, e.g., "1" from "1" or "1 -1"
            # full_choice_str is the complete input string.
            full_choice_str = choice_str
            stat_choice_key = full_choice_str.split()[0] if full_choice_str else ""

            if stat_choice_key == Game.STAT_MENU_CHOICE_RESET_KEY:
                self._handle_stat_reset()
            elif stat_choice_key == Game.STAT_MENU_CHOICE_CONFIRM_KEY:
                if self.player.free_points == 0:
                    self._finalize_stats_and_proceed()
                    return # Exit handler
                else:
                    self.ui.show_error("Please allocate all free points first!")
            elif stat_choice_key in self.stat_choice_to_name_map:
                self._process_stat_allocation_input(full_choice_str, stat_choice_key)
            else:
                self.ui.show_error("Invalid choice!")
            
            # Loop continues, will re-display UI and options.
            
    def handle_cave_home(self):
        """Handle cave home interactions"""
        if not self.player:
            self.change_phase(GamePhase.CHARACTER_CREATION)
            return
            
        self.ui.clear_screen()
        self.ui.display_header("Cave Home")
        
        self.ui.show_cave_home_art()
        
        self.ui.show_player_status(self.player)
        
        options = [
            "1. Rest (Restore HP/MP)",
            "2. Crafting",
            "3. Inventory",
            "4. Storage",
            "5. Exploration (Travel)",
            "6. View Stats",
            "7. Save Game",
            "8. Back to Main Menu"
        ]
        
        choice = self.ui.show_menu("What would you like to do?", options) # Returns Optional[int]
        
        # ESC key press is handled globally in Game.start() loop.
        # show_menu returns an int (1-indexed) or None (though unlikely with current setup if options exist).
        
        if choice == 1: # Rest
            self.handle_rest()
        elif choice == 2: # Crafting
            self.change_phase(GamePhase.CRAFTING)
        elif choice == 3: # Inventory
            self.change_phase(GamePhase.INVENTORY)
        elif choice == 4: # Storage
            self.change_phase(GamePhase.STORAGE)
        elif choice == 5: # Exploration (Travel)
            self.change_phase(GamePhase.TRAVEL_MENU)
        elif choice == 6: # View Stats
            if self.player: # Ensure player exists before showing stats
                self.ui.show_player_stats(self.player)
            self.ui.wait_for_input("Press Enter to continue...")
        elif choice == 7: # Save Game
            self.save_game()
        elif choice == 8: # Back to Main Menu
            self._prompt_confirmation_and_change_phase(
                prompt_message="Return to main menu? (Unsaved progress will be lost)",
                confirm_action=lambda: self.return_to_phase(GamePhase.MAIN_MENU),
                cancel_phase=None # Stay in Cave Home
            )
        # Add an else for unexpected choice values if show_menu could return None or out-of-range
        # else:
        #     self.ui.show_error("Invalid menu choice in Cave Home.") # Or simply do nothing / loop

    def handle_rest(self):
        """Handle resting in cave"""
        if not self.player:
            return
            
        self.ui.show_message("You rest peacefully in your cave...")
        self.player.current_hp = self.player.secondary_stats.max_hp
        self.player.current_mp = self.player.secondary_stats.max_mp
        self.ui.show_message("HP and MP fully restored!")
        result = self.ui.wait_for_input("Press Enter to continue...")
        
    def save_game(self):
        """Save the current game"""
        if not self.player:
            self.ui.show_error("No player data to save!")
            return
            
        try:
            save_data = {
                'player': self.player.to_dict(),
                'game_state': self.game_state.to_dict(),
                'inventory': self.inventory_system.to_dict(),
                'storage': self.storage_system.to_dict(),
                'zone_system': self.zone_system.to_dict(),
                'bestiary': self.bestiary.to_dict()
            }
            self.save_system.save_game(save_data)
            self.ui.show_message("Game saved successfully!")
        except Exception as e:
            self.ui.show_error(f"Failed to save game: {e}")
            
    def handle_travel_menu(self):
        """Handle travel menu"""
        self.ui.clear_screen()
        self.ui.display_header("Travel Menu")

        # Determine if coming from Cave Home for specific logic if needed by get_formatted_travel_options
        coming_from_cave_home = bool(self.phase_history and self.phase_history[-2] == GamePhase.CAVE_HOME)
        
        # Get formatted options from ZoneSystem
        # The get_available_zones() method in ZoneSystem already sorts zones by level.
        # The get_formatted_travel_options now also handles the formatting.
        options = self.zone_system.get_formatted_travel_options(coming_from_cave_home=coming_from_cave_home)
        
        # The "Back" option is now part of the options list returned by get_formatted_travel_options.
        # We need the actual list of zone names for selection logic.
        # get_available_zones returns the names in the correct order.
        available_zone_names = self.zone_system.get_available_zones()

        choice = self.ui.show_menu("Select Destination", options)
        
        if choice == "ESC":
            self._go_back_one_phase()
        # The "Back" option is the last one in the `options` list.
        # Its index will be len(options) if options are 1-indexed in the UI.
        # Or, if choice is the string number, it will be str(len(options)).
        elif choice == str(len(options)): # Assumes "Back" is the last option
            self._go_back_one_phase()
        else:
            try:
                zone_index = int(choice) - 1
                if 0 <= zone_index < len(available_zone_names): # Compare with the actual number of zones
                    selected_zone = available_zone_names[zone_index]
                    self.zone_system.current_zone = selected_zone
                    self.ui.show_message(f"Traveling to {selected_zone}...")
                    if self.ui.wait_for_input("Press Enter to continue...") != "ESC":
                        self.change_phase(GamePhase.ZONE_ACTIONS)
                else: # Handles cases where choice is a number but out of actual zone range
                    self.ui.show_error("Invalid zone selection!")
            except (ValueError, IndexError):
                self.ui.show_error("Invalid choice!")
                
    def handle_zone_actions(self):
        """Handle zone action menu"""
        self.ui.clear_screen()
        current_zone = self.zone_system.get_current_zone_name() # Use getter
        
        if not current_zone:
            self.ui.show_error("No current zone selected. Returning.")
            self._go_back_one_phase()
            return

        # Apply zone color formatting
        zone_color_code = ZONE_NAME_COLORS.get(current_zone.lower(), Colors.WHITE)
        colored_zone_name = f"{zone_color_code}{current_zone}{Colors.RESET}"
        
        self.ui.display_header(f"Zone: {colored_zone_name}")
        
        self.zone_system.display_zone_art(self.ui)
        
        # Get and display formatted zone details from ZoneSystem
        zone_details_list = self.zone_system.get_formatted_zone_details(self.bestiary)
        for detail_line in zone_details_list:
            self.ui.show_message(detail_line)
        
        options = [
            "1. Explore (Find Enemies)",
            "2. Gather Resources",
            "3. Rest",
            "4. Open Inventory",
            "5. View Stats",
            "6. Return to Cave"
        ]
        
        choice = self.ui.show_menu("What would you like to do?", options)
        
        if choice == "ESC":
            self._go_back_one_phase()
        elif choice == "1":
            self.start_encounter()
        elif choice == "2":
            self.gather_resources()
        elif choice == "3":
            self.handle_rest()
        elif choice == "4":
            self.change_phase(GamePhase.INVENTORY)
        elif choice == "5":
            self.ui.show_player_stats(self.player)
            self.ui.wait_for_input("Press Enter to continue...")
        elif choice == "6":
            self._go_back_one_phase()
            
    def start_encounter(self):
        """Start a combat encounter"""
        enemies = self.zone_system.generate_encounter()
        if enemies:
            self.combat_system.start_combat(self.player, enemies)
            self.change_phase(GamePhase.COMBAT)
        else:
            self.ui.show_message("You explore the area but find nothing...")
            self.ui.wait_for_input("Press Enter to continue...")
            
    def gather_resources(self):
        """Gather resources in current zone"""
        current_zone = self.zone_system.current_zone
        resources = self.zone_system.gather_resources()
        
        if resources:
            # Display the gathering results using the UI's gathering result method
            self.ui.show_gathering_result(resources)
            
            for resource, amount in resources.items():
                self.inventory_system.add_item(resource, amount)
                
                # Record as discovered in bestiary
                self.bestiary.discover_gatherable(current_zone, resource)
        else:
            self.ui.show_message("You search but find no resources...")
            
        self.ui.wait_for_input("Press Enter to continue...")
        
    def handle_combat(self):
        """Handle combat phase using the refactored CombatSystem."""
        if not self.player: # Should not happen if combat was initiated
            self.ui.show_error("Player not available for combat. Returning.")
            self._go_back_one_phase()
            return

        # The CombatSystem now manages the entire encounter.
        # It needs the player, enemies (which it gets from its internal state
        # set by start_encounter -> combat_system.start_combat), and the UI.
        # Enemies are already set in combat_system by start_encounter.
        combat_outcome = self.combat_system.execute_combat_encounter(self.player, self.combat_system.enemies, self.ui)

        if combat_outcome == CombatResult.VICTORY:
            self.handle_combat_victory()
        elif combat_outcome == CombatResult.DEFEAT:
            self.handle_combat_defeat()
        elif combat_outcome == CombatResult.FLED:
            self.ui.show_message("You successfully fled from combat.")
            self.ui.wait_for_input("Press Enter to continue...")
            self._go_back_one_phase() # Return to previous phase (e.g., Zone Actions)
        else: # ONGOING or other unexpected states
            # This case should ideally not be reached if execute_combat_encounter always returns a final state.
            # If it's ONGOING, it means combat ended prematurely without resolution.
            self.ui.show_error("Combat ended unexpectedly. Returning to zone.")
            self._go_back_one_phase()

    def handle_combat_victory(self):
        """Handles the aftermath of a combat victory."""
        exp_gained = self.combat_system.get_experience_gained()
        if exp_gained > 0:
            self.ui.show_victory_message(exp_gained)
            # Player experience gain and level up are handled by combat_system._end_combat

        loot = self.combat_system.get_loot()
        if loot:
            self.ui.show_loot_message(loot)
            for item, amount in loot.items():
                self.inventory_system.add_item(item, amount)

        # Discover defeated enemies for bestiary
        # combat_system.enemies still holds the list of enemies from the completed combat
        for enemy in self.combat_system.enemies:
            if not enemy.is_alive(): # Should be all of them in a victory
                # Check if already discovered to avoid repeated messages if not desired
                # For now, discover_enemy handles duplicates gracefully.
                self.bestiary.discover_enemy(enemy.name)
                # self.ui.show_message(f"{enemy.name} added to Bestiary.") # Optional: Bestiary might handle this

        self.ui.wait_for_input("Press Enter to continue...")
        self._go_back_one_phase() # Return to previous phase (e.g., Zone Actions)

    def handle_combat_defeat(self):
        """Handles the aftermath of a combat defeat."""
        if not self.player: return

        self.ui.show_message("Defeat! You have been defeated...")
        self.player.current_hp = 1  # Don't kill player completely, leave them at 1 HP
        self.player.current_mp = 0 # Optionally drain MP
        # Consider other penalties like gold loss, item loss, etc. here if desired.

        self.ui.wait_for_input("Press Enter to return to your Cave Home...")
        self.return_to_phase(GamePhase.CAVE_HOME) # Use return_to_phase to reset history correctly

    def handle_inventory(self):
        """Handle inventory management"""
        next_phase = self.inventory_system.show_inventory_menu(self.ui, self.player)
        
        # Simplify the navigation - always return to CAVE_HOME
        if next_phase == GamePhase.MAIN_MENU:
            # Return to main menu (reset history)
            self.phase_history = [GamePhase.MAIN_MENU]
            self.current_phase = GamePhase.MAIN_MENU
        else:
            # For any other result, return to CAVE_HOME
            # This ensures consistent navigation regardless of what inventory returns
            self.return_to_phase(GamePhase.CAVE_HOME)
        
    def handle_crafting(self):
        """Handle crafting menu"""
        if not self.player:
            return
            
        self.ui.clear_screen()
        self.ui.display_header("Crafting")
        self.ui.show_crafting_art()
        
        # Define crafting professions in alphabetical order
        crafting_professions = [
            "Alchemy",
            "Blacksmithing",
            "Cloth Work",
            "Cooking",
            "Lapidary",
            "Leatherwork",
            "Woodworking"
        ]
        
        # Create menu options with strikethrough for locked professions
        options = []
        for i, profession in enumerate(crafting_professions):
            is_unlocked = self.player.has_crafting_profession(profession)
            
            if is_unlocked:
                option_text = f"{i+1}. {profession} (Level 1)"
                options.append(option_text)
            else:
                # Use the UI helper to format locked options with hidden name
                option_text = f"{i+1}. ?????? (Locked)"
                options.append(self.ui.format_locked_option(option_text))
            
        options.append(f"{len(crafting_professions)+1}. Back")
        
        choice = self.ui.show_menu("Select Crafting Profession", options)
        
        if choice == "ESC":
            self._go_back_one_phase()
            return
            
        try:
            choice_num = int(choice) - 1
            if choice_num >= 0 and choice_num < len(crafting_professions):
                profession = crafting_professions[choice_num]
                
                if self.player.has_crafting_profession(profession):
                    self._handle_profession_crafting(profession)
                else:
                    self.ui.show_message(f"This crafting profession is locked.")
                    self.ui.show_message(f"Find an 'Introduction to {profession}' book to unlock it.")
                    self.ui.wait_for_input("Press Enter to continue...")
            elif choice_num == len(crafting_professions):
                self._go_back_one_phase()
        except ValueError:
            self.ui.show_error("Invalid selection!")
            self.ui.wait_for_input("Press Enter to continue...")
    
    def _handle_profession_crafting(self, profession: str):
        """Handle crafting within a specific profession"""
        self.ui.clear_screen()
        self.ui.display_header(f"{profession} Crafting")
        
        # This will be expanded later with actual recipes for each profession
        self.ui.show_message(f"{profession} recipes are not yet implemented.")
        self.ui.show_message(f"Your {profession} skill level: 1/100")
        
        self.ui.wait_for_input("Press Enter to return to crafting menu...")
        
    def handle_storage(self):
        """Handle storage system in cave home"""
        if not self.player:
            return
            
        next_phase = self.storage_system.show_storage_menu(self.ui, self.player, self.inventory_system)
        
        # Simplify the navigation - always return to CAVE_HOME
        if next_phase == GamePhase.MAIN_MENU:
            # Return to main menu (reset history)
            self.phase_history = [GamePhase.MAIN_MENU]
            self.current_phase = GamePhase.MAIN_MENU
        else:
            # For any other result, return to CAVE_HOME
            # This ensures consistent navigation regardless of what storage returns
            self.return_to_phase(GamePhase.CAVE_HOME)
        
    def handle_options(self):
        """Handle options menu"""
        self.ui.clear_screen()
        self.ui.display_header("Options")
        
        options = [
            "1. View Controls",
            "2. Bestiary", # Added Bestiary
            "3. About",
            "4. Back to Main Menu"
        ]
        
        choice_num = self.ui.show_menu("Options", options) # Returns Optional[int]
        
        if choice_num is None: # Should not happen if options are provided
            self._go_back_one_phase() # Or handle as error
            return

        # ESC key press is handled globally in Game.start() loop.
        # show_menu returns an int (1-indexed).
        
        if choice_num == 1: # View Controls
            self.show_controls()
        elif choice_num == 2: # Bestiary
            self.change_phase(GamePhase.BESTIARY)
        elif choice_num == 3: # About
            self.show_about()
        elif choice_num == 4: # Back to Main Menu
            # Use the confirmation helper to ensure user wants to go back
            self._prompt_confirmation_and_change_phase(
                prompt_message="Return to main menu?",
                confirm_action=lambda: self.return_to_phase(GamePhase.MAIN_MENU),
                cancel_phase=None # Stay in Options menu
            )

    def handle_bestiary(self):
        """Handle Bestiary interactions.
        Allows viewing zone data even if no player is loaded.
        Discovered enemies will only show if a player is active.
        """
        # The Bestiary instance is always available.
        # The Bestiary class's methods will handle whether to show discovered data
        # based on its internal state (which is loaded with player data).
        # Zone data is loaded on Bestiary initialization and is always available.

        # The bestiary UI logic is handled within the Bestiary class itself.
        # It should return a GamePhase (e.g., GamePhase.OPTIONS when backing out).
        # Pass the game instance (self) to the bestiary menu
        returned_phase = self.bestiary.show_bestiary_menu(self.ui, self)
        
        if isinstance(returned_phase, GamePhase):
            self.current_phase = returned_phase
        else:
            # Fallback if an unexpected or no phase is returned
            self.ui.show_error("Returning to Options menu due to an issue in Bestiary.")
            self.current_phase = GamePhase.OPTIONS
            
    def show_controls(self):
        """Show game controls"""
        self.ui.clear_screen()
        self.ui.display_header("Controls")
        controls = [
            "• Use number keys to select menu options",
            "• Press Enter to confirm selections",
            "• Press Ctrl+C to quit at any time",
            "• Type 'i' in zones to open inventory",
            "• Follow on-screen prompts for actions"
        ]
        for control in controls:
            self.ui.show_message(control)
        self.ui.wait_for_input("Press Enter to return...")
        
    def show_about(self):
        """Show about information"""
        self.ui.clear_screen()
        self.ui.display_header("About")
        self.ui.show_message("Python Console RPG")
        self.ui.show_message("Converted from JavaScript browser game")
        self.ui.show_message("A turn-based text RPG adventure")
        self.ui.wait_for_input("Press Enter to return...")
        
    def show_credits(self):
        """Show game credits"""
        self.ui.clear_screen()
        self.ui.display_header("Credits")
        self.ui.show_message("Game Design: Original JavaScript Version")
        self.ui.show_message("Python Conversion: Expert Roo")
        self.ui.show_message("A console-based RPG experience")
        self.ui.wait_for_input("Press Enter to return...")

def main():
    """Main entry point"""
    try:
        game = Game()
        game.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()