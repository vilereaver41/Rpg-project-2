"""
Combat system for the Python console RPG
Handles turn-based combat mechanics
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from player import Player
from enemy import Enemy, EnemyDatabase # Added EnemyDatabase
from ui_manager import UIManager
from bestiary import Bestiary # Added Bestiary

class CombatResult(Enum):
    ONGOING = "ongoing"
    VICTORY = "victory"
    DEFEAT = "defeat"
    FLED = "fled"

class CombatAction(Enum):
    ATTACK = "attack"
    MAGIC_ATTACK = "magic_attack"
    DEFEND = "defend"
    USE_ITEM = "use_item"
    RUN_AWAY = "run_away"

class CombatSystem:
    """Handles turn-based combat mechanics"""
    
    def __init__(self, bestiary: Bestiary): # Added bestiary parameter
        self.player: Optional[Player] = None
        self.enemies: List[Enemy] = []
        self.bestiary = bestiary # Store bestiary instance
        self.combat_active = False
        self.turn_order: List[Any] = []
        self.current_turn_index = 0
        self.combat_log: List[str] = []
        self.total_exp_gained = 0
        self.total_loot = {}

    def start_combat(self, player: Player, enemies: List[Enemy]):
        """Initialize a combat encounter's state. Called by execute_combat_encounter."""
        self.player = player
        self.enemies = enemies # These are instances of Enemy
        self.combat_active = True
        self.combat_log = []
        self.total_exp_gained = 0
        self.total_loot = {}

        # Discover enemies at the start of combat
        for enemy_instance in self.enemies:
            # Assuming enemy_instance.name is the unique ID used in EnemyDatabase keys
            # If Enemy.name is a display name and there's another ID field, use that.
            # For now, assuming enemy_instance.name is the key.
            # We need to ensure the name used for discovery matches the keys in EnemyDatabase
            # and the ID names in the bestiary zone files.
            # Let's assume enemy_instance.name is the correct ID for now.
            self.bestiary.discover_enemy(enemy_instance.name)


        # Initialize turn order based on agility/speed
        self._initialize_turn_order()
        
        # Reset defending state
        if self.player: # Ensure player is not None
            self.player.is_defending = False
        for enemy in self.enemies:
            enemy.is_defending = False
            
    def _initialize_turn_order(self):
        """Initialize combat turn order based on agility"""
        if not self.player: # Should not happen if start_combat is called correctly
            return
        participants = [self.player] + self.enemies
        
        # Calculate initiative for each participant
        initiative_list = []
        for participant in participants:
            if hasattr(participant, 'main_stats'):  # Player
                base_agility = participant.main_stats.agility + participant.main_stats.speed
            else:  # Enemy
                base_agility = participant.stats.agility
                
            # Add random factor
            initiative = base_agility + random.randint(1, 10)
            initiative_list.append((participant, initiative))
            
        # Sort by initiative (highest first)
        initiative_list.sort(key=lambda x: x[1], reverse=True)
        self.turn_order = [participant for participant, _ in initiative_list]
        self.current_turn_index = 0
        
    def is_combat_active(self) -> bool:
        """Check if combat is currently active"""
        return self.combat_active
        
    def get_current_actor(self):
        """Get the current actor whose turn it is"""
        if not self.turn_order:
            return None
        return self.turn_order[self.current_turn_index]

    def execute_combat_encounter(self, player: Player, enemies: List[Enemy], ui: UIManager) -> CombatResult:
        """
        Manages the entire combat loop from start to finish.
        Returns the outcome of the combat (VICTORY, DEFEAT, FLED).
        """
        self.start_combat(player, enemies)

        while self.is_combat_active():
            # Check win/lose conditions at the start of each iteration
            result = self._check_combat_end()
            if result != CombatResult.ONGOING:
                self._end_combat(result)
                return result # Combat ended (victory, defeat)

            current_actor = self.get_current_actor()
            if not current_actor:
                # This case should ideally not be reached if turn order is managed correctly
                # and combat ends when no actors are left or player is defeated.
                self._end_combat(CombatResult.ONGOING) # Or some error state
                return CombatResult.ONGOING # Or an error specific enum

            # Show combat status (player and alive enemies)
            if self.player: # Ensure player is not None
                ui.show_combat_status(self.player, [e for e in self.enemies if e.is_alive()])
            
            # Process turn based on actor type
            if current_actor == self.player:
                action_taken = self._process_player_turn(ui)
                if not action_taken: # e.g. player chose to run and failed, turn ends
                    pass # Turn still advances
                if not self.is_combat_active(): # Player successfully fled
                    self._end_combat(CombatResult.FLED) # Ensure combat is marked as ended
                    return CombatResult.FLED
            else: # Enemy turn
                self._process_enemy_turn(current_actor, ui)
                
            # Process status effects for all participants after the action
            self._process_status_effects(ui)
            
            # Advance to next turn (if combat is still active)
            if self.is_combat_active():
                self._advance_turn()
            
            # Check combat end again after turn and status effects
            # This is important if status effects defeat the last enemy or the player
            result_after_turn = self._check_combat_end()
            if result_after_turn != CombatResult.ONGOING:
                self._end_combat(result_after_turn)
                return result_after_turn

        # Fallback, should be covered by checks within the loop
        final_check = self._check_combat_end()
        self._end_combat(final_check)
        return final_check

    def _process_player_turn(self, ui: UIManager) -> bool:
        """
        Process the player's turn.
        Returns True if an action was taken that consumes the turn, False otherwise (e.g., failed item use).
        Modifies self.combat_active to False if player flees.
        """
        if not self.player: # Should not happen
            return False

        ui.show_message(f"\n{self.player.name}'s turn!")
        
        # Reset defending state at start of turn
        self.player.is_defending = False
        
        while True: # Loop until a valid action is taken or player flees
            choice = ui.show_combat_menu()
            
            if choice == "1":  # Attack
                self._player_attack(ui)
                return True
            elif choice == "2":  # Magic Attack
                self._player_magic_attack(ui)
                return True
            elif choice == "3":  # Defend
                self._player_defend(ui)
                return True
            elif choice == "4":  # Use Item
                if self._player_use_item(ui): # _player_use_item should return True if turn is consumed
                    return True
                # If item use failed/cancelled, loop again for another choice
            elif choice == "5":  # Run Away
                if self._player_run_away(ui): # This method now sets self.combat_active = False if successful
                    # If run_away was successful, combat_active is false.
                    # If failed, combat_active is true, and turn is consumed.
                    return True # Turn is consumed whether successful or not.
            else:
                ui.show_error("Invalid choice!")
                # Loop again for another choice
                
    def _player_attack(self, ui: UIManager):
        """Handle player attack action"""
        alive_enemies = [e for e in self.enemies if e.is_alive()]
        if not alive_enemies:
            ui.show_message("No enemies to attack!")
            return
            
        if len(alive_enemies) == 1:
            target = alive_enemies[0]
        else:
            target_index = ui.show_target_selection(alive_enemies)
            target = alive_enemies[target_index]
            
        # Check if target dodges
        if target.can_dodge():
            ui.show_dodge_message(target.name)
            return
            
        # Calculate damage
        damage = self.player.get_attack_damage()
        is_crit = self.player.can_crit()
        actual_damage = target.take_damage(damage)
        
        ui.show_damage_message(self.player.name, target.name, actual_damage, is_crit)
        
        if not target.is_alive():
            ui.show_message(f"{target.name} has been defeated!")
            
    def _player_magic_attack(self, ui: UIManager):
        """Handle player magic attack action"""
        mp_cost = 10
        if not self.player.use_mp(mp_cost):
            ui.show_error("Not enough MP!")
            return
            
        alive_enemies = [e for e in self.enemies if e.is_alive()]
        if not alive_enemies:
            ui.show_message("No enemies to attack!")
            return
            
        if len(alive_enemies) == 1:
            target = alive_enemies[0]
        else:
            target_index = ui.show_target_selection(alive_enemies)
            target = alive_enemies[target_index]
            
        # Check if target dodges
        if target.can_dodge():
            ui.show_dodge_message(target.name)
            return
            
        # Calculate magic damage
        damage = self.player.get_magic_damage()
        is_crit = self.player.can_crit()
        actual_damage = target.take_magic_damage(damage)
        
        ui.show_message(f"{self.player.name} casts a magic spell!")
        ui.show_damage_message("Magic", target.name, actual_damage, is_crit)
        
        if not target.is_alive():
            ui.show_message(f"{target.name} has been defeated!")
            
    def _player_defend(self, ui: UIManager):
        """Handle player defend action"""
        self.player.is_defending = True
        ui.show_message(f"{self.player.name} takes a defensive stance!")
        ui.show_message("Defense increased for this turn!")
        
    def _player_use_item(self, ui: UIManager) -> bool:
        """Handle player item use - placeholder for now"""
        ui.show_message("Item system not yet implemented!")
        return False
        
    def _player_run_away(self, ui: UIManager) -> bool:
        """Handle player running away"""
        # Calculate run chance based on agility
        player_agility = self.player.main_stats.agility + self.player.main_stats.speed
        enemy_agility = max(e.stats.agility for e in self.enemies if e.is_alive())
        
        run_chance = 50 + ((player_agility - enemy_agility) * 5)
        run_chance = max(10, min(90, run_chance))  # Clamp between 10-90%
        
        if random.random() * 100 < run_chance:
            ui.show_message(f"{self.player.name} successfully runs away!")
            self.combat_active = False
            return True
        else:
            ui.show_message(f"{self.player.name} couldn't escape!")
            return True  # Turn is used even if escape fails
            
    def _process_enemy_turn(self, enemy: Enemy, ui: UIManager):
        """Process an enemy's turn"""
        if not enemy.is_alive():
            return
            
        ui.show_message(f"\n{enemy.name}'s turn!")
        
        # Reset defending state
        enemy.is_defending = False
        
        # AI chooses action
        action = enemy.choose_action(self.player)
        
        if action['type'] == 'attack':
            self._enemy_attack(enemy, ui)
        elif action['type'] == 'magic_attack':
            self._enemy_magic_attack(enemy, ui)
        elif action['type'] == 'defend':
            self._enemy_defend(enemy, ui)
        elif action['type'] == 'heal':
            self._enemy_heal(enemy, ui)
        elif action['type'] == 'ability':
            self._enemy_use_ability(enemy, ui)
        else:
            # Default to attack
            self._enemy_attack(enemy, ui)
            
    def _enemy_attack(self, enemy: Enemy, ui: UIManager):
        """Handle enemy attack"""
        # Check if player dodges
        if self.player.can_dodge():
            ui.show_dodge_message(self.player.name)
            return
            
        damage = enemy.get_attack_damage()
        is_crit = enemy.can_crit()
        
        # Apply defense bonus if player is defending
        if hasattr(self.player, 'is_defending') and self.player.is_defending:
            damage = int(damage * 0.5)  # 50% damage reduction when defending
            
        actual_damage = self.player.take_damage(damage)
        ui.show_damage_message(enemy.name, self.player.name, actual_damage, is_crit)
        
    def _enemy_magic_attack(self, enemy: Enemy, ui: UIManager):
        """Handle enemy magic attack"""
        if not enemy.use_mp(10):
            # Fall back to regular attack
            self._enemy_attack(enemy, ui)
            return
            
        if self.player.can_dodge():
            ui.show_dodge_message(self.player.name)
            return
            
        damage = enemy.get_magic_damage()
        is_crit = enemy.can_crit()
        
        if hasattr(self.player, 'is_defending') and self.player.is_defending:
            damage = int(damage * 0.5)
            
        actual_damage = self.player.take_magic_damage(damage)
        ui.show_message(f"{enemy.name} casts a spell!")
        ui.show_damage_message("Magic", self.player.name, actual_damage, is_crit)
        
    def _enemy_defend(self, enemy: Enemy, ui: UIManager):
        """Handle enemy defend"""
        enemy.is_defending = True
        ui.show_message(f"{enemy.name} takes a defensive stance!")
        
    def _enemy_heal(self, enemy: Enemy, ui: UIManager):
        """Handle enemy heal"""
        if enemy.use_mp(20):
            heal_amount = random.randint(15, 25)
            actual_heal = enemy.heal(heal_amount)
            ui.show_heal_message(enemy.name, actual_heal)
        else:
            # Fall back to defend
            self._enemy_defend(enemy, ui)
            
    def _enemy_use_ability(self, enemy: Enemy, ui: UIManager):
        """Handle enemy ability use"""
        if enemy.abilities:
            ability = random.choice(enemy.abilities)
            result = enemy.use_ability(ability, self.player)
            
            if result['success']:
                ui.show_message(result['message'])
                
                if result['type'] == 'attack':
                    if not self.player.can_dodge():
                        actual_damage = self.player.take_damage(result['damage'])
                        ui.show_damage_message(ability, self.player.name, actual_damage)
                        
                        # Apply status effect if any
                        if 'status_effect' in result:
                            self.player.add_status_effect(result['status_effect'])
                            ui.show_status_effect_message(
                                self.player.name, 
                                result['status_effect']['name']
                            )
                    else:
                        ui.show_dodge_message(self.player.name)
                        
                elif result['type'] == 'magic_attack':
                    if not self.player.can_dodge():
                        actual_damage = self.player.take_magic_damage(result['damage'])
                        ui.show_damage_message(ability, self.player.name, actual_damage)
                    else:
                        ui.show_dodge_message(self.player.name)
            else:
                ui.show_message(result['message'])
                # Fall back to attack
                self._enemy_attack(enemy, ui)
        else:
            # No abilities, fall back to attack
            self._enemy_attack(enemy, ui)
            
    def _process_status_effects(self, ui: UIManager):
        """Process status effects for all participants"""
        # Process player status effects
        old_hp = self.player.current_hp
        self.player.process_status_effects()
        if self.player.current_hp != old_hp:
            damage = old_hp - self.player.current_hp
            if damage > 0:
                ui.show_message(f"{self.player.name} takes {damage} damage from status effects!")
            else:
                heal = self.player.current_hp - old_hp
                ui.show_message(f"{self.player.name} recovers {heal} HP from status effects!")
                
        # Process enemy status effects
        for enemy in self.enemies:
            if enemy.is_alive():
                old_hp = enemy.current_hp
                enemy.process_status_effects()
                if enemy.current_hp != old_hp:
                    damage = old_hp - enemy.current_hp
                    if damage > 0:
                        ui.show_message(f"{enemy.name} takes {damage} damage from status effects!")
                    else:
                        heal = enemy.current_hp - old_hp
                        ui.show_message(f"{enemy.name} recovers {heal} HP from status effects!")
                        
    def _advance_turn(self):
        """Advance to the next participant's turn"""
        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        
        # Skip dead enemies
        attempts = 0
        while attempts < len(self.turn_order):
            current_actor = self.turn_order[self.current_turn_index]
            if current_actor == self.player or current_actor.is_alive():
                break
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            attempts += 1
            
    def _check_combat_end(self) -> CombatResult:
        """Check if combat should end"""
        if not self.player.is_alive():
            return CombatResult.DEFEAT
            
        alive_enemies = [e for e in self.enemies if e.is_alive()]
        if not alive_enemies:
            return CombatResult.VICTORY
            
        return CombatResult.ONGOING
        
    def _end_combat(self, result: CombatResult):
        """End combat and calculate rewards"""
        self.combat_active = False
        
        if result == CombatResult.VICTORY:
            # Calculate experience and loot
            total_exp = 0
            total_loot = {}
            
            # Get the item rarity map from the EnemyDatabase if accessible
            rarity_map = None
            try:
                from enemy import EnemyDatabase
                db = EnemyDatabase()
                rarity_map = db.item_rarity_map
            except (ImportError, AttributeError):
                # If we can't access the EnemyDatabase or it doesn't have item_rarity_map,
                # proceed without the rarity map (will fall back to heuristics)
                pass
            
            for enemy in self.enemies:
                exp = enemy.get_experience_value()
                total_exp += exp
                
                # Pass player and rarity map to get_loot to apply discovery bonus
                loot = enemy.get_loot(self.player, rarity_map)
                for item, quantity in loot.items():
                    total_loot[item] = total_loot.get(item, 0) + quantity
                    
            self.total_exp_gained = total_exp
            self.total_loot = total_loot
            
            # Give experience to player
            old_level = self.player.level
            self.player.gain_experience(total_exp)
            
            # Check for level up
            if self.player.level > old_level:
                # Level up occurred during experience gain
                pass
                
    def get_loot(self) -> Dict[str, int]:
        """Get loot from the last combat"""
        return self.total_loot.copy()
        
    def get_experience_gained(self) -> int:
        """Get experience gained from last combat"""
        return self.total_exp_gained