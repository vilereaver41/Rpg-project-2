"""
Player character system for the Python RPG
Handles player stats, character creation, and progression
"""

from dataclasses import dataclass, asdict, field
from enum import Enum, auto
from typing import Dict, Any, Optional, Callable
import random
import logging # For logging warnings

# --- Equipment Slot Definition ---
class EquipmentSlot(Enum):
    MAIN_HAND = auto()
    OFF_HAND = auto()
    HEAD = auto()
    CHEST = auto()
    LEGS = auto()
    FEET = auto()
    RING1 = auto()
    RING2 = auto()
    AMULET = auto()

# --- Constants for Player Stats and Mechanics ---
DEFAULT_MAIN_STAT_VALUE = 2
DEFAULT_LUCK_STAT_VALUE = 1
INITIAL_FREE_POINTS = 3
INITIAL_LEVEL = 1
INITIAL_EXPERIENCE = 0
INITIAL_EXPERIENCE_TO_NEXT = 100
MAX_ACTION_TIMER_DEFAULT = 1000

# Base values for secondary stats
BASE_HP = 31
BASE_MP = 20
BASE_ATTACK = 5
BASE_DEFENSE = 2
BASE_MAGIC_ATTACK = 5
BASE_MAGIC_DEFENSE = 2

# Stat multipliers for secondary stats
VITALITY_HP_MULTIPLIER = 9
INTELLIGENCE_MP_MULTIPLIER = 5
STRENGTH_ATTACK_MULTIPLIER = 1.30
AGILITY_ATTACK_MULTIPLIER = 0.10
VITALITY_DEFENSE_MULTIPLIER = 1.20
INTELLIGENCE_MAGIC_ATTACK_MULTIPLIER = 1.0 # Explicitly stating 1 for clarity
WISDOM_MAGIC_DEFENSE_MULTIPLIER = 1.0 # Explicitly stating 1 for clarity
WISDOM_RESTORATIVE_MAGIC_MULTIPLIER = 1.0 # Explicitly stating 1 for clarity
DEXTERITY_CRIT_RATE_MULTIPLIER = 0.50
AGILITY_DODGE_MULTIPLIER = 0.50
DEXTERITY_DODGE_MULTIPLIER = 0.10

# Combat mechanics
MINIMUM_DAMAGE = 1
MAX_DODGE_CHANCE = 95.0 # Percentage
MAX_CRIT_CHANCE = 95.0  # Percentage
CRITICAL_HIT_MULTIPLIER = 1.5
DAMAGE_VARIANCE_PERCENTAGE = 0.1 # 10% variance

# Leveling
EXPERIENCE_TO_NEXT_LEVEL_MULTIPLIER = 1.2 # 20% increase
STAT_POINTS_PER_LEVEL = 1
AUTO_ASSIGNED_STATS_ON_LEVEL_UP = ["strength", "vitality", "wisdom", "intelligence", "agility", "dexterity", "speed"]

# Status Effects defaults
DEFAULT_POISON_DAMAGE = 5
DEFAULT_REGEN_HEAL = 5
DEFAULT_BURN_DAMAGE = 3
# --- End Constants ---


@dataclass
class MainStats:
    """Primary character statistics"""
    strength: int = DEFAULT_MAIN_STAT_VALUE
    vitality: int = DEFAULT_MAIN_STAT_VALUE
    wisdom: int = DEFAULT_MAIN_STAT_VALUE
    intelligence: int = DEFAULT_MAIN_STAT_VALUE
    agility: int = DEFAULT_MAIN_STAT_VALUE
    dexterity: int = DEFAULT_MAIN_STAT_VALUE
    luck: int = DEFAULT_LUCK_STAT_VALUE
    speed: int = DEFAULT_MAIN_STAT_VALUE
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MainStats':
        return cls(**data)

@dataclass
class SecondaryStats:
    """Calculated secondary statistics"""
    max_hp: int = 0
    max_mp: int = 0
    attack: int = 0
    defense: int = 0
    m_attack: int = 0
    m_defense: int = 0
    restorative_magic: int = 0
    crit_rate: float = 0.0
    dodge: float = 0.0
    luck: int = 0
    discovery: float = 0.0 # Directly tied to luck main stat
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecondaryStats':
        return cls(**data)

@dataclass
class StatusEffectData:
    """Data for a status effect instance."""
    name: str  # e.g., "Minor Poison", "Heavy Bleed"
    type: str  # e.g., "poison", "stun", "regen_hp", "stat_boost"
    duration: int  # in turns or ticks
    potency: Optional[float] = None  # e.g., damage per tick for poison, heal per tick for regen
    value: Optional[Any] = None  # e.g., amount for stat_boost, not used by all effects
    target_stat: Optional[str] = None # e.g., "strength" for stat_boost
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusEffectData':
        return cls(**data)

class Player:
    """Player character class"""
    
    def __init__(self, name: str = "", gender: str = ""):
        self.name = name
        self.gender = gender
        self.main_stats = MainStats()
        self.secondary_stats = SecondaryStats()
        self.free_points = INITIAL_FREE_POINTS
        self.level = INITIAL_LEVEL
        self.experience = INITIAL_EXPERIENCE
        self.experience_to_next = INITIAL_EXPERIENCE_TO_NEXT
        
        self.equipment = {slot: None for slot in EquipmentSlot}
        
        self.calculate_secondary_stats()
        self.current_hp = self.secondary_stats.max_hp
        self.current_mp = self.secondary_stats.max_mp
        
        self.action_timer = 0
        self.max_action_timer = MAX_ACTION_TIMER_DEFAULT
        
        self.status_effects: list[StatusEffectData] = [] # Now stores StatusEffectData objects
        self.unlocked_crafting_professions = set()
        
        # Dispatch dictionary for status effect handlers
        self._status_effect_handlers: Dict[str, Callable[[StatusEffectData], None]] = {
            "poison": self._apply_poison_effect,
            "stun": self._apply_stun_effect,
            "regen_hp": self._apply_regen_hp_effect,
            "stat_boost": self._apply_stat_boost_effect, # Placeholder, needs implementation
            "burn": self._apply_burn_effect, # Added for existing burn logic
            # Add other effect types and their handlers here
        }
        
    def calculate_secondary_stats(self):
        """Calculate secondary stats based on main stats"""
        ms = self.main_stats
        sec = self.secondary_stats
        
        # Reset base secondary stats before recalculating
        sec.max_hp = BASE_HP
        sec.max_mp = BASE_MP
        sec.attack = BASE_ATTACK
        sec.defense = BASE_DEFENSE
        sec.m_attack = BASE_MAGIC_ATTACK
        sec.m_defense = BASE_MAGIC_DEFENSE
        sec.restorative_magic = 0 # Assuming base is 0 before wisdom
        sec.crit_rate = 0.0
        sec.dodge = 0.0
        # Luck and discovery are direct from main stats, not typically reset here unless equipment could modify them.
        # For now, let's keep them as they are, as they are direct conversions.

        # Calculate from main stats
        sec.max_hp += (ms.vitality * VITALITY_HP_MULTIPLIER)
        sec.max_mp += (ms.intelligence * INTELLIGENCE_MP_MULTIPLIER)
        sec.attack += (ms.strength * STRENGTH_ATTACK_MULTIPLIER) + \
                      (ms.agility * AGILITY_ATTACK_MULTIPLIER)
        sec.defense += (ms.vitality * VITALITY_DEFENSE_MULTIPLIER)
        sec.m_attack += (ms.intelligence * INTELLIGENCE_MAGIC_ATTACK_MULTIPLIER)
        sec.m_defense += (ms.wisdom * WISDOM_MAGIC_DEFENSE_MULTIPLIER)
        sec.restorative_magic += ms.wisdom * WISDOM_RESTORATIVE_MAGIC_MULTIPLIER
        # Convert crit_rate to percentage (0-100%)
        sec.crit_rate += ms.dexterity * DEXTERITY_CRIT_RATE_MULTIPLIER
# Convert dodge to percentage (0-100%)
        sec.dodge += (ms.agility * AGILITY_DODGE_MULTIPLIER) + \
                     (ms.dexterity * DEXTERITY_DODGE_MULTIPLIER)
        sec.luck = ms.luck
        # Convert discovery to percentage (0-100%)
        sec.discovery = float(ms.luck) * 2.0 # Discovery percentage is luck * 2%
        
        # Apply equipment bonuses after base calculations from main stats
        self._apply_equipment_bonuses()
        
        # TODO: Apply status effect modifications to secondary stats here if they directly modify them
        # For now, status effects are handled separately in process_status_effects
        
    def _apply_equipment_bonuses(self):
        """
        Apply bonuses from equipped items.
        This is a placeholder and will be expanded when the equipment and item systems are more developed.
        """
        # TODO: Implement full equipment stat application logic
        # Reset stats that equipment might modify to avoid stacking on multiple calls
        # This assumes equipment primarily boosts these stats. If equipment can grant base amounts,
        # this reset logic might need adjustment or be part of the initial reset in calculate_secondary_stats.
        # For now, we'll assume additive bonuses.
        
        # Example: if equipment could grant HP/MP directly, you might do:
        # self.secondary_stats.max_hp -= self._equipment_hp_bonus_cache (and similar for others)
        # self._equipment_hp_bonus_cache = 0
        # For simplicity in this placeholder, we'll let calculate_secondary_stats handle the base reset.

        for slot, item_instance in self.equipment.items():
            if item_instance is not None:
                # Assuming item_instance is an object from inventory_system.py
                # and has a 'name' attribute and a 'stats' attribute (e.g., an ItemStats object)
                item_name = getattr(item_instance, 'name', 'Unknown Item')
                print(f"DEBUG: Checking item '{item_name}' in slot {slot.name}")

                if hasattr(item_instance, 'stats') and item_instance.stats is not None:
                    item_stats = item_instance.stats # Assuming this is an ItemStats like object
                    print(f"DEBUG: Applying stats from {item_name} in {slot.name}: {item_stats}")

                    # Optional: Simple Placeholder Application
                    # These direct additions are temporary. A real system would be more nuanced.
                    if hasattr(self.secondary_stats, 'attack') and hasattr(item_stats, 'attack'):
                        self.secondary_stats.attack += item_stats.attack
                    if hasattr(self.secondary_stats, 'defense') and hasattr(item_stats, 'defense'):
                        self.secondary_stats.defense += item_stats.defense
                    if hasattr(self.secondary_stats, 'm_attack') and hasattr(item_stats, 'm_attack'):
                        self.secondary_stats.m_attack += item_stats.m_attack
                    if hasattr(self.secondary_stats, 'm_defense') and hasattr(item_stats, 'm_defense'):
                        self.secondary_stats.m_defense += item_stats.m_defense
                    if hasattr(self.secondary_stats, 'max_hp') and hasattr(item_stats, 'hp'): # Assuming item stat is 'hp' for max_hp
                        self.secondary_stats.max_hp += item_stats.hp
                    if hasattr(self.secondary_stats, 'max_mp') and hasattr(item_stats, 'mp'): # Assuming item stat is 'mp' for max_mp
                        self.secondary_stats.max_mp += item_stats.mp
                    # Add more for other stats if they map clearly (e.g., crit_rate, dodge)
                    if hasattr(self.secondary_stats, 'crit_rate') and hasattr(item_stats, 'crit_rate'):
                        self.secondary_stats.crit_rate += item_stats.crit_rate
                    if hasattr(self.secondary_stats, 'dodge') and hasattr(item_stats, 'dodge'):
                        self.secondary_stats.dodge += item_stats.dodge
                else:
                    print(f"DEBUG: Item {item_name} in {slot.name} has no 'stats' attribute or stats are None.")
        
    def allocate_stat_point(self, stat_name: str, points: int):
        """Allocate stat points to a specific stat"""
        if points > 0 and self.free_points < points:
            return False
            
        if hasattr(self.main_stats, stat_name):
            current_value = getattr(self.main_stats, stat_name)
            
            base_value = DEFAULT_LUCK_STAT_VALUE if stat_name == 'luck' else DEFAULT_MAIN_STAT_VALUE
            allocated_points = current_value - base_value
            
            if points < 0:
                points_to_remove = abs(points)
                if points_to_remove > allocated_points:
                    return False
            
            setattr(self.main_stats, stat_name, current_value + points)
            self.free_points -= points
            self.calculate_secondary_stats()
            return True
            
        return False
        
    def reset_stats(self):
        """Reset all stats to base values"""
        self.main_stats = MainStats() # Re-initializes with default constants
        self.free_points = INITIAL_FREE_POINTS
        self.calculate_secondary_stats()
        
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken"""
        damage = max(0, damage) # Ensure damage is non-negative
        actual_damage = max(MINIMUM_DAMAGE, damage - self.secondary_stats.defense)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
        
    def take_magic_damage(self, damage: int) -> int:
        """Take magic damage and return actual damage taken"""
        damage = max(0, damage) # Ensure damage is non-negative
        actual_damage = max(MINIMUM_DAMAGE, damage - self.secondary_stats.m_defense)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
        
    def heal(self, amount: int) -> int:
        """Heal HP and return actual amount healed"""
        amount = max(0, amount) # Ensure heal amount is non-negative
        old_hp = self.current_hp
        self.current_hp = min(self.secondary_stats.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp
        
    def restore_mp(self, amount: int) -> int:
        """Restore MP and return actual amount restored"""
        old_mp = self.current_mp
        self.current_mp = min(self.secondary_stats.max_mp, self.current_mp + amount)
        return self.current_mp - old_mp
        
    def use_mp(self, amount: int) -> bool:
        """Use MP if available"""
        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False
        
    def is_alive(self) -> bool:
        """Check if player is alive"""
        return self.current_hp > 0
        
    def get_hp_percentage(self) -> float:
        """Get HP as percentage"""
        if self.secondary_stats.max_hp == 0:
            return 0.0
        return (self.current_hp / self.secondary_stats.max_hp) * 100
        
    def get_mp_percentage(self) -> float:
        """Get MP as percentage"""
        if self.secondary_stats.max_mp == 0:
            return 0.0
        return (self.current_mp / self.secondary_stats.max_mp) * 100
        
    def gain_experience(self, exp: int):
        """Gain experience points"""
        self.experience += exp
        while self.experience >= self.experience_to_next:
            self.level_up()
            
    def level_up(self):
        """Level up the player"""
        self.experience -= self.experience_to_next
        self.level += 1
        self.experience_to_next = int(self.experience_to_next * EXPERIENCE_TO_NEXT_LEVEL_MULTIPLIER)
        
        for stat in AUTO_ASSIGNED_STATS_ON_LEVEL_UP:
            current_value = getattr(self.main_stats, stat)
            setattr(self.main_stats, stat, current_value + 1)
        
        self.free_points += STAT_POINTS_PER_LEVEL
        
        old_max_hp = self.secondary_stats.max_hp
        old_max_mp = self.secondary_stats.max_mp
        
        self.calculate_secondary_stats()
        
        hp_gain = self.secondary_stats.max_hp - old_max_hp
        mp_gain = self.secondary_stats.max_mp - old_max_mp
        
        self.current_hp = min(self.secondary_stats.max_hp, self.current_hp + hp_gain)
        self.current_mp = min(self.secondary_stats.max_mp, self.current_mp + mp_gain)
        
    def can_dodge(self) -> bool:
        """Check if player can dodge an attack"""
        dodge_chance = min(MAX_DODGE_CHANCE, self.secondary_stats.dodge)
        return random.random() * 100 < dodge_chance
        
    def can_crit(self) -> bool:
        """Check if player can land a critical hit"""
        crit_chance = min(MAX_CRIT_CHANCE, self.secondary_stats.crit_rate)
        return random.random() * 100 < crit_chance
        
    def get_attack_damage(self) -> int:
        """Calculate attack damage"""
        base_damage = self.secondary_stats.attack
        variance = int(base_damage * DAMAGE_VARIANCE_PERCENTAGE)
        damage = random.randint(max(MINIMUM_DAMAGE, base_damage - variance), base_damage + variance)
        
        if self.can_crit():
            damage = int(damage * CRITICAL_HIT_MULTIPLIER)
            
        return max(MINIMUM_DAMAGE, damage)
        
    def get_magic_damage(self) -> int:
        """Calculate magic attack damage"""
        base_damage = self.secondary_stats.m_attack
        variance = int(base_damage * DAMAGE_VARIANCE_PERCENTAGE)
        damage = random.randint(max(MINIMUM_DAMAGE, base_damage - variance), base_damage + variance)
        
        if self.can_crit():
            damage = int(damage * CRITICAL_HIT_MULTIPLIER)
            
        return max(MINIMUM_DAMAGE, damage)
        
    def add_status_effect(self, effect_data: StatusEffectData):
        """Add a status effect. Expects a StatusEffectData object."""
        if not isinstance(effect_data, StatusEffectData):
            logging.warning(f"Attempted to add invalid status effect: {effect_data}. Expected StatusEffectData.")
            # Optionally, raise TypeError("effect_data must be an instance of StatusEffectData")
            return

        # TODO: Consider stacking logic here. For now, just append.
        # Example: if an effect of the same type and name exists, refresh duration or stack potency.
        self.status_effects.append(effect_data)
        
    def remove_status_effect(self, effect_name: str):
        """Remove a status effect by name"""
        # This will remove all effects with the given name.
        # If multiple instances of the same named effect can exist and need specific removal,
        # a more sophisticated ID or tracking mechanism would be needed.
        self.status_effects = [effect for effect in self.status_effects
                               if effect.name != effect_name]

    # --- Status Effect Handler Methods ---
    def _apply_poison_effect(self, effect_data: StatusEffectData):
        """Applies poison damage."""
        damage = int(effect_data.potency if effect_data.potency is not None else DEFAULT_POISON_DAMAGE)
        self.current_hp = max(0, self.current_hp - damage)
        # print(f"{self.name} takes {damage} poison damage. HP: {self.current_hp}/{self.secondary_stats.max_hp}")

    def _apply_stun_effect(self, effect_data: StatusEffectData):
        """Applies stun effect (prevents action)."""
        # The main effect of stun is handled in the combat loop by checking if a stun effect is active.
        # This method could log or apply secondary effects if any.
        # print(f"{self.name} is stunned for this turn.")
        pass # Actual stun logic is usually external (e.g., in combat turn processing)

    def _apply_regen_hp_effect(self, effect_data: StatusEffectData):
        """Applies HP regeneration."""
        heal_amount = int(effect_data.potency if effect_data.potency is not None else DEFAULT_REGEN_HEAL)
        self.heal(heal_amount)
        # print(f"{self.name} regenerates {heal_amount} HP. HP: {self.current_hp}/{self.secondary_stats.max_hp}")

    def _apply_burn_effect(self, effect_data: StatusEffectData):
        """Applies burn damage."""
        damage = int(effect_data.potency if effect_data.potency is not None else DEFAULT_BURN_DAMAGE)
        self.current_hp = max(0, self.current_hp - damage)
        # print(f"{self.name} takes {damage} burn damage. HP: {self.current_hp}/{self.secondary_stats.max_hp}")

    def _apply_stat_boost_effect(self, effect_data: StatusEffectData):
        """Applies a temporary stat boost."""
        # This is more complex as it requires tracking original stats and reverting.
        # For now, this is a placeholder.
        # A proper implementation would:
        # 1. Store the original stat value if not already boosted by this specific effect instance.
        # 2. Apply the boost.
        # 3. When the effect expires, revert the stat.
        # This might involve modifying calculate_secondary_stats or having a separate layer for temporary boosts.
        if effect_data.target_stat and effect_data.value is not None:
            # print(f"{self.name} receives a boost to {effect_data.target_stat} by {effect_data.value}.")
            # Actual stat modification logic needs careful design to handle stacking and removal.
            pass
        else:
            logging.warning(f"Stat boost effect '{effect_data.name}' is missing target_stat or value.")

    def process_status_effects(self):
        """Process all active status effects using the dispatch dictionary."""
        active_effects_this_turn = []
        effects_to_remove_indices = []

        for i, effect in enumerate(self.status_effects):
            handler = self._status_effect_handlers.get(effect.type)
            if handler:
                handler(effect)
            else:
                logging.warning(f"No handler found for status effect type: {effect.type} ({effect.name})")

            effect.duration -= 1
            if effect.duration <= 0:
                effects_to_remove_indices.append(i)
            else:
                active_effects_this_turn.append(effect)
        
        # Remove expired effects by index, iterating in reverse to maintain correct indices
        for index in sorted(effects_to_remove_indices, reverse=True):
            expired_effect = self.status_effects.pop(index)
            # print(f"Status effect {expired_effect.name} has expired for {self.name}.")
            # Add logic here if stat boosts need to be reverted upon expiration.
            if expired_effect.type == "stat_boost" and expired_effect.target_stat:
                # This is where you'd call a method to revert the specific stat boost.
                # self._revert_stat_boost(expired_effect) # Needs implementation
                logging.info(f"Stat boost {expired_effect.name} expired. Reversion logic needed.")


    def get_status_effect_names(self) -> list[str]:
        """Get list of active status effect names"""
        return [effect.name for effect in self.status_effects]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary for saving"""
        return {
            'name': self.name,
            'gender': self.gender,
            'main_stats': self.main_stats.to_dict(),
            'secondary_stats': self.secondary_stats.to_dict(),
            'free_points': self.free_points,
            'current_hp': self.current_hp,
            'current_mp': self.current_mp,
            'level': self.level,
            'experience': self.experience,
            'experience_to_next': self.experience_to_next,
            'action_timer': self.action_timer,
            'max_action_timer': self.max_action_timer,
            'equipment': {slot.name: item for slot, item in self.equipment.items()}, # Convert Enum keys to strings
            'status_effects': [effect.to_dict() for effect in self.status_effects], # Serialize StatusEffectData
            'unlocked_crafting_professions': list(self.unlocked_crafting_professions)
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """Create player from dictionary"""
        player = cls(data.get('name', ''), data.get('gender', ''))
        player.main_stats = MainStats.from_dict(data.get('main_stats', {}))
        player.secondary_stats = SecondaryStats.from_dict(data.get('secondary_stats', {}))
        player.free_points = data.get('free_points', INITIAL_FREE_POINTS)
        player.current_hp = data.get('current_hp', 0) # Should be set based on stats after load if new game
        player.current_mp = data.get('current_mp', 0) # Should be set based on stats after load if new game
        player.level = data.get('level', INITIAL_LEVEL)
        player.experience = data.get('experience', INITIAL_EXPERIENCE)
        player.experience_to_next = data.get('experience_to_next', INITIAL_EXPERIENCE_TO_NEXT)
        player.action_timer = data.get('action_timer', 0)
        player.max_action_timer = data.get('max_action_timer', MAX_ACTION_TIMER_DEFAULT)
        
        # Initialize equipment with Enum keys
        player.equipment = {slot: None for slot in EquipmentSlot}
        raw_equipment = data.get('equipment', {})
        if isinstance(raw_equipment, dict): # Check if it's a dict (new format or old string-keyed format)
            for slot_key, item_data in raw_equipment.items():
                if isinstance(slot_key, EquipmentSlot): # Already an Enum (e.g. if loaded from non-serialized source)
                    player.equipment[slot_key] = item_data # TODO: Deserialize item_data if it's complex
                elif isinstance(slot_key, str): # String key from saved data
                    try:
                        slot_enum = EquipmentSlot[slot_key]
                        player.equipment[slot_enum] = item_data # TODO: Deserialize item_data if it's complex
                    except KeyError:
                        logging.warning(f"Unknown equipment slot key '{slot_key}' in save data. Ignoring.")
                else:
                    logging.warning(f"Invalid equipment slot key type '{type(slot_key)}' in save data. Ignoring.")
        else: # Fallback for very old saves that might have a different structure or None
            logging.warning(f"Equipment data is not in expected dictionary format: {raw_equipment}. Initializing empty.")
            player.equipment = {slot: None for slot in EquipmentSlot}


        # Deserialize status effects into StatusEffectData objects
        status_effects_data = data.get('status_effects', [])
        player.status_effects = [StatusEffectData.from_dict(ef_data) for ef_data in status_effects_data]
        
        crafting_professions = data.get('unlocked_crafting_professions', [])
        player.unlocked_crafting_professions = set(crafting_professions)

        # Ensure HP/MP are correctly set if loading a character that might not have them saved
        # or if they were 0 from a default dict.
        # If current_hp/mp are explicitly in save data and non-zero, they should be used.
        # Otherwise, recalculate based on stats. This handles new characters vs loaded.
        if player.current_hp == 0 and player.secondary_stats.max_hp > 0 : # Check if it was default from data.get
             player.current_hp = player.secondary_stats.max_hp
        if player.current_mp == 0 and player.secondary_stats.max_mp > 0: # Check if it was default from data.get
             player.current_mp = player.secondary_stats.max_mp
        
        # If loading an old save that didn't have secondary_stats explicitly, recalculate them.
        # Modern saves should have them.
        if not data.get('secondary_stats'):
            player.calculate_secondary_stats()
            player.current_hp = player.secondary_stats.max_hp
            player.current_mp = player.secondary_stats.max_mp


        return player
        
    def __str__(self) -> str:
        """String representation of player"""
        return f"{self.name} (Level {self.level} {self.gender})"
        
    def unlock_crafting_profession(self, profession_name: str) -> bool:
        """Unlock a crafting profession"""
        if profession_name in self.unlocked_crafting_professions:
            return False
        self.unlocked_crafting_professions.add(profession_name)
        return True
        
    def has_crafting_profession(self, profession_name: str) -> bool:
        """Check if a crafting profession is unlocked"""
        return profession_name in self.unlocked_crafting_professions

# PlayerData class removed as it was redundant.
# Player.to_dict() and Player.from_dict() handle serialization directly.