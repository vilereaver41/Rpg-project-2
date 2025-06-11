"""
GameController: GUI-friendly wrapper for main game logic and state.
Handles all game phases and exposes methods for the GUI to call.
"""
from enemy import EnemyDatabase
from bestiary import Bestiary
from game_state import GameState
from player import Player
from combat_system import CombatSystem
from inventory_system import InventorySystem
from save_system import SaveSystem
from zone_system import ZoneSystem
from enum import Enum

class GamePhase(Enum):
    MAIN_MENU = "main_menu"
    CHARACTER_CREATION = "character_creation"
    STAT_ALLOCATION = "stat_allocation"
    CAVE_HOME = "cave_home"
    TRAVEL_MENU = "travel_menu"
    ZONE_ACTIONS = "zone_actions"
    COMBAT = "combat"
    INVENTORY = "inventory"
    CRAFTING = "crafting"
    OPTIONS = "options"
    BESTIARY = "bestiary"

class GameController:
    def __init__(self):
        self.game_state = GameState()
        self.player = None
        self.enemy_db = EnemyDatabase()
        self.bestiary = Bestiary(enemy_db=self.enemy_db)
        self.combat_system = CombatSystem(bestiary=self.bestiary)
        self.inventory_system = InventorySystem()
        self.save_system = SaveSystem()
        self.zone_system = ZoneSystem(enemy_db=self.enemy_db)
        self.current_phase = GamePhase.MAIN_MENU
        self.running = True

    # Methods for each phase/menu will be added here for GUI to call
    # Example stubs:
    def start_new_game(self):
        self.player = None
        self.game_state.reset()
        self.current_phase = GamePhase.CHARACTER_CREATION

    def load_game(self, save_data):
        # To be implemented: load from save_data
        pass

    # ...and so on for each phase
