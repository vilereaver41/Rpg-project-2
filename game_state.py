"""
Game state management for the Python console RPG
Handles global game state and progression
"""

from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

class TimeOfDay(Enum):
    DAWN = "Dawn"
    MORNING = "Morning"
    NOON = "Noon"
    AFTERNOON = "Afternoon"
    DUSK = "Dusk"
    EVENING = "Evening"
    NIGHT = "Night"
    MIDNIGHT = "Midnight"

@dataclass
class GameFlags:
    """Boolean flags for game progression"""
    tutorial_completed: bool = False
    first_combat_won: bool = False
    visited_shapira_plains: bool = False
    met_first_npc: bool = False
    crafted_first_item: bool = False
    reached_level_5: bool = False
    reached_level_10: bool = False
    discovered_cave_secrets: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameFlags':
        return cls(**data)

@dataclass
class GameCounters:
    """Numeric counters for game statistics"""
    enemies_defeated: int = 0
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    items_crafted: int = 0
    resources_gathered: int = 0
    zones_discovered: int = 0
    times_rested: int = 0
    total_playtime_minutes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameCounters':
        return cls(**data)

class GameState:
    """Manages global game state and progression"""
    
    def __init__(self):
        self.current_time = TimeOfDay.MORNING
        self.day_count = 1
        self.flags = GameFlags()
        self.counters = GameCounters()
        self.discovered_zones = ["Cave Home"]  # Start with cave discovered
        self.unlocked_recipes = []
        self.completed_quests = []
        self.active_quests = []
        self.world_events = []
        
        # Game difficulty settings
        self.difficulty_multiplier = 1.0
        self.enemy_spawn_rate = 1.0
        self.resource_spawn_rate = 1.0
        
    def advance_time(self, hours: int = 1):
        """Advance game time by specified hours"""
        time_values = list(TimeOfDay)
        current_index = time_values.index(self.current_time)
        
        for _ in range(hours):
            current_index = (current_index + 1) % len(time_values)
            if current_index == 0:  # Wrapped around to dawn
                self.day_count += 1
                
        self.current_time = time_values[current_index]
        
    def get_time_description(self) -> str:
        """Get descriptive text for current time"""
        descriptions = {
            TimeOfDay.DAWN: "The sun begins to rise, painting the sky in soft pastels.",
            TimeOfDay.MORNING: "The morning sun shines brightly, full of promise.",
            TimeOfDay.NOON: "The sun reaches its peak, casting sharp shadows.",
            TimeOfDay.AFTERNOON: "The afternoon sun warms the land gently.",
            TimeOfDay.DUSK: "The sun begins to set, creating golden hues.",
            TimeOfDay.EVENING: "Twilight settles over the world peacefully.",
            TimeOfDay.NIGHT: "Stars twinkle in the dark night sky.",
            TimeOfDay.MIDNIGHT: "The world sleeps under the pale moonlight."
        }
        return descriptions.get(self.current_time, "Time flows onward...")
        
    def discover_zone(self, zone_name: str):
        """Discover a new zone"""
        if zone_name not in self.discovered_zones:
            self.discovered_zones.append(zone_name)
            self.counters.zones_discovered += 1
            
    def is_zone_discovered(self, zone_name: str) -> bool:
        """Check if a zone has been discovered"""
        return zone_name in self.discovered_zones
        
    def unlock_recipe(self, recipe_name: str):
        """Unlock a crafting recipe"""
        if recipe_name not in self.unlocked_recipes:
            self.unlocked_recipes.append(recipe_name)
            
    def is_recipe_unlocked(self, recipe_name: str) -> bool:
        """Check if a recipe is unlocked"""
        return recipe_name in self.unlocked_recipes
        
    def complete_quest(self, quest_id: str):
        """Mark a quest as completed"""
        if quest_id in self.active_quests:
            self.active_quests.remove(quest_id)
        if quest_id not in self.completed_quests:
            self.completed_quests.append(quest_id)
            
    def start_quest(self, quest_id: str):
        """Start a new quest"""
        if quest_id not in self.active_quests and quest_id not in self.completed_quests:
            self.active_quests.append(quest_id)
            
    def is_quest_completed(self, quest_id: str) -> bool:
        """Check if a quest is completed"""
        return quest_id in self.completed_quests
        
    def is_quest_active(self, quest_id: str) -> bool:
        """Check if a quest is active"""
        return quest_id in self.active_quests
        
    def add_world_event(self, event: Dict[str, Any]):
        """Add a world event"""
        event['day'] = self.day_count
        event['time'] = self.current_time.value
        self.world_events.append(event)
        
    def get_recent_events(self, days: int = 3) -> List[Dict[str, Any]]:
        """Get recent world events"""
        cutoff_day = max(1, self.day_count - days)
        return [event for event in self.world_events if event.get('day', 0) >= cutoff_day]
        
    def set_flag(self, flag_name: str, value: bool = True):
        """Set a game flag"""
        if hasattr(self.flags, flag_name):
            setattr(self.flags, flag_name, value)
            
    def get_flag(self, flag_name: str) -> bool:
        """Get a game flag value"""
        return getattr(self.flags, flag_name, False)
        
    def increment_counter(self, counter_name: str, amount: int = 1):
        """Increment a game counter"""
        if hasattr(self.counters, counter_name):
            current_value = getattr(self.counters, counter_name)
            setattr(self.counters, counter_name, current_value + amount)
            
    def get_counter(self, counter_name: str) -> int:
        """Get a counter value"""
        return getattr(self.counters, counter_name, 0)
        
    def get_playtime_string(self) -> str:
        """Get formatted playtime string"""
        total_minutes = self.counters.total_playtime_minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
            
    def get_game_statistics(self) -> Dict[str, Any]:
        """Get comprehensive game statistics"""
        return {
            'playtime': self.get_playtime_string(),
            'day': self.day_count,
            'time_of_day': self.current_time.value,
            'zones_discovered': self.counters.zones_discovered,
            'enemies_defeated': self.counters.enemies_defeated,
            'total_damage_dealt': self.counters.total_damage_dealt,
            'total_damage_taken': self.counters.total_damage_taken,
            'items_crafted': self.counters.items_crafted,
            'resources_gathered': self.counters.resources_gathered,
            'times_rested': self.counters.times_rested,
            'quests_completed': len(self.completed_quests),
            'active_quests': len(self.active_quests)
        }
        
    def check_achievements(self, player) -> List[str]:
        """Check for newly unlocked achievements"""
        achievements = []
        
        # Level-based achievements
        if player.level >= 5 and not self.get_flag('reached_level_5'):
            achievements.append("Novice Adventurer - Reached Level 5")
            self.set_flag('reached_level_5')
            
        if player.level >= 10 and not self.get_flag('reached_level_10'):
            achievements.append("Experienced Explorer - Reached Level 10")
            self.set_flag('reached_level_10')
            
        # Combat achievements
        if self.counters.enemies_defeated >= 10 and not self.get_flag('first_combat_won'):
            achievements.append("Monster Slayer - Defeated 10 enemies")
            self.set_flag('first_combat_won')
            
        # Exploration achievements
        if self.counters.zones_discovered >= 3:
            achievements.append("Explorer - Discovered 3 zones")
            
        # Crafting achievements
        if self.counters.items_crafted >= 5 and not self.get_flag('crafted_first_item'):
            achievements.append("Craftsman - Crafted 5 items")
            self.set_flag('crafted_first_item')
            
        return achievements
        
    def apply_time_effects(self, player):
        """Apply effects based on time of day"""
        # Different times could affect various game mechanics
        time_effects = {
            TimeOfDay.DAWN: {'exp_bonus': 1.1, 'encounter_rate': 0.8},
            TimeOfDay.MORNING: {'exp_bonus': 1.0, 'encounter_rate': 1.0},
            TimeOfDay.NOON: {'exp_bonus': 1.0, 'encounter_rate': 1.2},
            TimeOfDay.AFTERNOON: {'exp_bonus': 1.0, 'encounter_rate': 1.0},
            TimeOfDay.DUSK: {'exp_bonus': 1.0, 'encounter_rate': 1.1},
            TimeOfDay.EVENING: {'exp_bonus': 1.0, 'encounter_rate': 0.9},
            TimeOfDay.NIGHT: {'exp_bonus': 1.2, 'encounter_rate': 1.3},
            TimeOfDay.MIDNIGHT: {'exp_bonus': 1.3, 'encounter_rate': 1.5}
        }
        
        return time_effects.get(self.current_time, {'exp_bonus': 1.0, 'encounter_rate': 1.0})
        
    def reset(self):
        """Reset game state for new game"""
        self.current_time = TimeOfDay.MORNING
        self.day_count = 1
        self.flags = GameFlags()
        self.counters = GameCounters()
        self.discovered_zones = ["Cave Home"]
        self.unlocked_recipes = []
        self.completed_quests = []
        self.active_quests = []
        self.world_events = []
        self.difficulty_multiplier = 1.0
        self.enemy_spawn_rate = 1.0
        self.resource_spawn_rate = 1.0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary for saving"""
        return {
            'current_time': self.current_time.value,
            'day_count': self.day_count,
            'flags': self.flags.to_dict(),
            'counters': self.counters.to_dict(),
            'discovered_zones': self.discovered_zones,
            'unlocked_recipes': self.unlocked_recipes,
            'completed_quests': self.completed_quests,
            'active_quests': self.active_quests,
            'world_events': self.world_events,
            'difficulty_multiplier': self.difficulty_multiplier,
            'enemy_spawn_rate': self.enemy_spawn_rate,
            'resource_spawn_rate': self.resource_spawn_rate
        }
        
    def load_from_dict(self, data: Dict[str, Any]):
        """Load game state from dictionary"""
        self.current_time = TimeOfDay(data.get('current_time', TimeOfDay.MORNING.value))
        self.day_count = data.get('day_count', 1)
        self.flags = GameFlags.from_dict(data.get('flags', {}))
        self.counters = GameCounters.from_dict(data.get('counters', {}))
        self.discovered_zones = data.get('discovered_zones', ["Cave Home"])
        self.unlocked_recipes = data.get('unlocked_recipes', [])
        self.completed_quests = data.get('completed_quests', [])
        self.active_quests = data.get('active_quests', [])
        self.world_events = data.get('world_events', [])
        self.difficulty_multiplier = data.get('difficulty_multiplier', 1.0)
        self.enemy_spawn_rate = data.get('enemy_spawn_rate', 1.0)
        self.resource_spawn_rate = data.get('resource_spawn_rate', 1.0)
        
    def __str__(self) -> str:
        """String representation of game state"""
        return f"Day {self.day_count}, {self.current_time.value}"