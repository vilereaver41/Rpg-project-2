"""
Enemy system for the Python console RPG
Handles enemy data, AI, and combat behavior
"""

import random
import csv # Added for CSV reading
import os # Added for path joining
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Define the base path for data files relative to this script
BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "csv")

@dataclass
class EnemyStats:
    """Enemy statistics"""
    level: int
    max_hp: int
    max_mp: int
    attack: int
    defense: int
    m_attack: int
    m_defense: int
    agility: int
    luck: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level,
            'max_hp': self.max_hp,
            'max_mp': self.max_mp,
            'attack': self.attack,
            'defense': self.defense,
            'm_attack': self.m_attack,
            'm_defense': self.m_defense,
            'agility': self.agility,
            'luck': self.luck
        }

class Enemy:
    """Enemy class for combat encounters"""
    
    def __init__(self, name: str, enemy_type: str, rarity: str, stats: EnemyStats,
                 abilities: List[str] = None, loot: List[str] = None):
        self.name = name
        self.type = enemy_type
        self.rarity = rarity # Added rarity
        self.stats = stats
        self.max_hp = stats.max_hp
        self.current_hp = stats.max_hp
        self.max_mp = stats.max_mp
        self.current_mp = stats.max_mp
        self.abilities = abilities or []
        # Deduplicate loot while preserving order
        self.loot_table = list(dict.fromkeys(loot or []))

        # Combat state
        self.action_timer = 0
        self.max_action_timer = 1000
        self.status_effects = []
        self.is_defending = False
        
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken"""
        defense = self.stats.defense
        if self.is_defending:
            defense = int(defense * 1.5)  # 50% defense bonus when defending
            
        actual_damage = max(1, damage - defense)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
        
    def take_magic_damage(self, damage: int) -> int:
        """Take magic damage and return actual damage taken"""
        defense = self.stats.m_defense
        if self.is_defending:
            defense = int(defense * 1.5)
            
        actual_damage = max(1, damage - defense)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
        
    def heal(self, amount: int) -> int:
        """Heal HP and return actual amount healed"""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp
        
    def use_mp(self, amount: int) -> bool:
        """Use MP if available"""
        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False
        
    def is_alive(self) -> bool:
        """Check if enemy is alive"""
        return self.current_hp > 0
        
    def can_dodge(self) -> bool:
        """Check if enemy can dodge an attack"""
        dodge_chance = min(95, self.stats.agility * 0.5)  # Agility affects dodge
        return random.random() * 100 < dodge_chance
        
    def can_crit(self) -> bool:
        """Check if enemy can land a critical hit"""
        crit_chance = min(95, self.stats.luck * 0.3)  # Luck affects crit
        return random.random() * 100 < crit_chance
        
    def get_attack_damage(self) -> int:
        """Calculate attack damage"""
        base_damage = self.stats.attack
        variance = int(base_damage * 0.15)  # 15% variance for enemies
        damage = random.randint(max(1, base_damage - variance), base_damage + variance)
        
        if self.can_crit():
            damage = int(damage * 1.5)
            
        return max(1, damage)
        
    def get_magic_damage(self) -> int:
        """Calculate magic attack damage"""
        base_damage = self.stats.m_attack
        variance = int(base_damage * 0.15)
        damage = random.randint(max(1, base_damage - variance), base_damage + variance)
        
        if self.can_crit():
            damage = int(damage * 1.5)
            
        return max(1, damage)
        
    def add_status_effect(self, effect: Dict[str, Any]):
        """Add a status effect"""
        self.status_effects.append(effect)
        
    def remove_status_effect(self, effect_name: str):
        """Remove a status effect by name"""
        self.status_effects = [effect for effect in self.status_effects 
                              if effect.get('name') != effect_name]
        
    def process_status_effects(self):
        """Process all active status effects"""
        effects_to_remove = []
        
        for i, effect in enumerate(self.status_effects):
            effect['duration'] -= 1
            
            # Apply effect
            if effect['type'] == 'poison':
                damage = effect.get('damage', 5)
                self.current_hp = max(0, self.current_hp - damage)
            elif effect['type'] == 'regen':
                heal_amount = effect.get('heal', 5)
                self.heal(heal_amount)
            elif effect['type'] == 'burn':
                damage = effect.get('damage', 3)
                self.current_hp = max(0, self.current_hp - damage)
                
            if effect['duration'] <= 0:
                effects_to_remove.append(i)
                
        for i in reversed(effects_to_remove):
            self.status_effects.pop(i)
            
    def get_status_effect_names(self) -> List[str]:
        """Get list of active status effect names"""
        return [effect.get('name', 'Unknown') for effect in self.status_effects]
        
    def choose_action(self, player) -> Dict[str, Any]:
        """AI chooses an action based on current situation"""
        # Simple AI logic
        actions = []
        
        # Always can attack
        actions.append({'type': 'attack', 'weight': 60})
        
        # Magic attack if has MP
        if self.current_mp >= 10:
            actions.append({'type': 'magic_attack', 'weight': 30})
            
        # Defend if low health
        if self.current_hp < self.max_hp * 0.3:
            actions.append({'type': 'defend', 'weight': 40})
            
        # Use abilities if available
        if self.abilities and self.current_mp >= 15:
            actions.append({'type': 'ability', 'weight': 25})
            
        # Heal if very low health and has MP
        if self.current_hp < self.max_hp * 0.2 and self.current_mp >= 20:
            actions.append({'type': 'heal', 'weight': 80})
            
        # Choose action based on weights
        total_weight = sum(action['weight'] for action in actions)
        if total_weight == 0:
            return {'type': 'attack'}
            
        roll = random.randint(1, total_weight)
        current_weight = 0
        
        for action in actions:
            current_weight += action['weight']
            if roll <= current_weight:
                return action
                
        return {'type': 'attack'}  # Fallback
        
    def use_ability(self, ability_name: str, target) -> Dict[str, Any]:
        """Use a special ability"""
        if ability_name not in self.abilities:
            return {'success': False, 'message': f"{self.name} doesn't know {ability_name}"}
            
        # Simple ability system - can be expanded
        if ability_name == "Heal":
            if self.use_mp(20):
                heal_amount = random.randint(15, 25)
                actual_heal = self.heal(heal_amount)
                return {
                    'success': True,
                    'message': f"{self.name} heals for {actual_heal} HP",
                    'type': 'heal',
                    'amount': actual_heal
                }
        elif ability_name == "Poison Strike":
            if self.use_mp(15):
                damage = self.get_attack_damage()
                poison_effect = {
                    'name': 'Poison',
                    'type': 'poison',
                    'damage': 5,
                    'duration': 3
                }
                return {
                    'success': True,
                    'message': f"{self.name} uses Poison Strike",
                    'type': 'attack',
                    'damage': damage,
                    'status_effect': poison_effect
                }
        elif ability_name == "Fire Blast":
            if self.use_mp(25):
                damage = int(self.get_magic_damage() * 1.3)
                return {
                    'success': True,
                    'message': f"{self.name} casts Fire Blast",
                    'type': 'magic_attack',
                    'damage': damage
                }
                
        return {'success': False, 'message': f"{self.name} fails to use {ability_name}"}
        
    def get_loot(self, player=None, rarity_map=None) -> Dict[str, int]:
        """Generate loot drops
        
        Args:
            player: Optional player object for discovery stat bonuses
            rarity_map: Optional dictionary mapping item names to rarities
        """
        loot = {}
        
        for item in self.loot_table:
            # Base drop chance of 30%, modified by luck
            drop_chance = 30 + (self.stats.luck * 0.5)
            
            # Apply discovery bonus based on item rarity if player is provided
            if player is not None:
                discovery_bonus = 0
                
                # Determine item rarity using rarity map if provided
                item_rarity = self._determine_item_rarity(item, rarity_map)
                
                # Apply discovery bonus based on item rarity
                discovery = player.secondary_stats.discovery
                if item_rarity == "common":
                    discovery_bonus = discovery * 10.0  # 10% per discovery point
                elif item_rarity == "uncommon":
                    discovery_bonus = discovery * 5.0   # 5% per discovery point
                elif item_rarity == "rare":
                    discovery_bonus = discovery * 2.0   # 2% per discovery point
                elif item_rarity == "epic":
                    discovery_bonus = discovery * 1.0   # 1% per discovery point
                elif item_rarity == "legendary":
                    discovery_bonus = discovery * 0.5   # 0.5% per discovery point
                elif item_rarity == "mythical":
                    discovery_bonus = discovery * 0.2   # 0.2% per discovery point
                
                drop_chance += discovery_bonus
            
            if random.random() * 100 < drop_chance:
                # Most items drop 1, some might drop more
                quantity = 1
                if item.endswith("Fragment") or item.endswith("Shard"):
                    quantity = random.randint(1, 3)
                elif "Essence" in item:
                    quantity = random.randint(1, 2)
                    
                loot[item] = loot.get(item, 0) + quantity
                
        return loot
        
    def _determine_item_rarity(self, item_name: str, rarity_map: Dict[str, str] = None) -> str:
        """Determine the rarity of an item based on the rarity map or keywords
        
        Args:
            item_name: The name of the item
            rarity_map: Optional dictionary mapping item names to rarities
        
        Returns:
            String representing the item's rarity (common, uncommon, rare, etc.)
        """
        # If we have a rarity map, check it first
        if rarity_map is not None and item_name in rarity_map:
            return rarity_map[item_name]
        
        # Try with a normalized version of the item name
        if rarity_map is not None:
            # Try to find a matching key by ignoring case and punctuation
            normalized_item = item_name.lower().replace('_', ' ').strip()
            for map_item, rarity in rarity_map.items():
                map_item_normalized = map_item.lower().replace('_', ' ').strip()
                if normalized_item == map_item_normalized:
                    return rarity
        
        # Fall back to the simple heuristic based on item name
        item_lower = item_name.lower()
        if "mythical" in item_lower or "omnific" in item_lower:
            return "mythical"
        elif "legendary" in item_lower:
            return "legendary"
        elif "epic" in item_lower:
            return "epic"
        elif "rare" in item_lower:
            return "rare"
        elif "uncommon" in item_lower:
            return "uncommon"
        elif "trash" in item_lower:
            return "trash"
        else:
            return "common"
        
    def get_experience_value(self) -> int:
        """Calculate experience points this enemy gives"""
        base_exp = self.stats.level * 10
        # Add bonus based on enemy type
        type_multipliers = {
            'Physical': 1.0,
            'Fire': 1.1,
            'Water': 1.1,
            'Earth': 1.1,
            'Wind': 1.1,
            'Thunder': 1.1,
            'Ice': 1.1,
            'Nature': 1.0,
            'Light': 1.2,
            'Darkness': 1.2,
            'Null': 1.5
        }
        
        multiplier = type_multipliers.get(self.type, 1.0)
        return int(base_exp * multiplier)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert enemy to dictionary"""
        return {
            'name': self.name,
            'type': self.type,
            'rarity': self.rarity, # Added rarity
            'stats': self.stats.to_dict(),
            'current_hp': self.current_hp,
            'current_mp': self.current_mp,
            'abilities': self.abilities,
            'loot_table': self.loot_table,
            'status_effects': self.status_effects,
            'action_timer': self.action_timer
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Enemy':
        """Create enemy from dictionary"""
        stats_data = data.get('stats', {})
        stats = EnemyStats(
            level=stats_data.get('level', 1),
            max_hp=stats_data.get('max_hp', 100),
            max_mp=stats_data.get('max_mp', 50),
            attack=stats_data.get('attack', 10),
            defense=stats_data.get('defense', 5),
            m_attack=stats_data.get('m_attack', 10),
            m_defense=stats_data.get('m_defense', 5),
            agility=stats_data.get('agility', 10),
            luck=stats_data.get('luck', 10)
        )

        enemy = cls(
            name=data.get('name', 'Unknown Enemy'),
            enemy_type=data.get('type', 'Physical'),
            rarity=data.get('rarity', 'Common'), # Added rarity
            stats=stats,
            abilities=data.get('abilities', []),
            loot=data.get('loot_table', [])
        )

        enemy.current_hp = data.get('current_hp', enemy.max_hp)
        enemy.current_mp = data.get('current_mp', enemy.max_mp)
        enemy.status_effects = data.get('status_effects', [])
        enemy.action_timer = data.get('action_timer', 0)
        
        return enemy
        
    def __str__(self) -> str:
        """String representation of enemy"""
        return f"{self.name} (Level {self.stats.level} {self.rarity} {self.type})"

class EnemyDatabase:
    """Database of enemy templates"""

    def __init__(self):
        self.enemies = self._load_enemy_data_from_csv()
        self.item_rarity_map = self._load_item_rarity_data()

    def _load_enemy_data_from_csv(self) -> Dict[str, Dict[str, Any]]:
        """Load enemy data from the Enemy's-Sheet.csv file."""
        enemies_data: Dict[str, Dict[str, Any]] = {}
        file_path = os.path.join(BASE_DATA_PATH, "Enemy's-Sheet.csv")

        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if not reader.fieldnames:
                    print(f"ERROR: CSV file {file_path} is empty or has no header.")
                    return {}
                
                # Helper to safely convert to int, defaulting to 0 if empty or invalid
                def safe_int(value: Optional[str], default: int = 0) -> int:
                    if value is None or value.strip() == "":
                        return default
                    try:
                        return int(value)
                    except ValueError:
                        return default
                
                # Helper to parse comma-separated strings into a list
                def parse_list_string(value: Optional[str]) -> List[str]:
                    if not value:
                        return []
                    return [item.strip() for item in value.split(',') if item.strip()]

                for i, row in enumerate(reader):
                    try:
                        name = row.get("Name")
                        if not name or name.startswith("(") or name.startswith(","): # Skip zone headers and empty lines
                            continue
                        
                        field_names = reader.fieldnames if reader.fieldnames else []
                        
                        current_enemy_loot = parse_list_string(row.get("Enemy Loot"))
                        for loot_col_idx in range(15, 26): 
                            col_name = field_names[loot_col_idx] if len(field_names) > loot_col_idx else None
                            current_enemy_loot.extend(parse_list_string(row.get(col_name) if col_name else None))

                        enemies_data[name] = {
                            "level_range": row.get("Level Range", "1"),
                            "rarity": row.get("Spawn Chance", "Common"),
                            "type": row.get("Type", "Physical"),
                            "max_hp": safe_int(row.get("Max Hp Lowest Level")),
                            "max_mp": safe_int(row.get("Max Mp")),
                            "attack": safe_int(row.get("Attack")),
                            "defense": safe_int(row.get("Defense")),
                            "m_attack": safe_int(row.get("M.Attack")),
                            "m_defense": safe_int(row.get("M.Defense.")),
                            "agility": safe_int(row.get("Agility")),
                            "luck": safe_int(row.get("Luck")),
                            "abilities": parse_list_string(row.get("Abilitys & Spells")),
                            "loot": [item for item in current_enemy_loot if item]
                        }
                    except Exception as e_row:
                        print(f"ERROR: Could not process row {i+2} for enemy '{row.get('Name', 'Unknown')}' in {file_path}: {e_row}")
                        continue # Continue to the next row
            
            if enemies_data:
                print(f"[DEBUG EnemyDB] Loaded {len(enemies_data)} enemies from CSV. First 5 keys: {list(enemies_data.keys())[:5]}")

        except FileNotFoundError:
            print(f"ERROR: Enemy CSV file not found at {file_path}")
            return {}
        except Exception as e_file: 
            print(f"ERROR: Could not load enemy data from CSV {file_path}: {e_file}")
            return {}
            
        if not enemies_data:
            print("[DEBUG EnemyDB] CRITICAL: No data loaded from CSV (enemies_data is empty after processing).")
        return enemies_data
        
    def _load_item_rarity_data(self) -> Dict[str, str]:
        """Load item rarity data from the loot_rarity_master.txt file"""
        item_rarity_map = {}
        file_path = os.path.join(BASE_DATA_PATH, "loot_rarity_master.txt")
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    # Skip comments, empty lines and the format explanation line
                    if not line or line.startswith('#') or line == "item_name = (rarity)":
                        continue
                    
                    # Parse the line in format "Item Name = (Rarity)"
                    parts = line.split('=')
                    if len(parts) == 2:
                        item_name = parts[0].strip()
                        rarity = parts[1].strip()
                        
                        # Extract rarity from the parentheses
                        if rarity.startswith('(') and rarity.endswith(')'):
                            rarity = rarity[1:-1].lower()  # Remove parentheses and convert to lowercase
                            item_rarity_map[item_name] = rarity
            
            print(f"[DEBUG ItemRarity] Loaded {len(item_rarity_map)} item rarities from txt file.")
        
        except FileNotFoundError:
            print(f"ERROR: Item rarity file not found at {file_path}")
        except Exception as e:
            print(f"ERROR: Could not load item rarity data: {e}")
            
        return item_rarity_map

    def create_enemy(self, enemy_name: str, level_override: Optional[int] = None) -> Optional[Enemy]:
        """Create an enemy instance from the database"""
        # Normalize the input enemy_name and find the matching key in self.enemies
        normalized_input_name = enemy_name.lower().replace("_", "").replace(" ", "")
        actual_enemy_key = None
        for key in self.enemies.keys():
            normalized_db_key = key.lower().replace("_", "").replace(" ", "")
            if normalized_db_key == normalized_input_name:
                actual_enemy_key = key
                break
        
        if not actual_enemy_key:
            # print(f"[DEBUG EnemyDB create_enemy] Enemy '{enemy_name}' (normalized: '{normalized_input_name}') not found in database keys.")
            return None
            
        data = self.enemies[actual_enemy_key]
        # Use actual_enemy_key for display name if you want consistency with CSV,
        # or keep original enemy_name if it's preferred for some reason.
        # For bestiary details, using the name from the database (actual_enemy_key) is likely best.
        display_name_for_instance = actual_enemy_key


        # Parse level range
        level_str = data.get("level_range", "1") # Use "level_range" from CSV data
        if "-" in level_str:
            try:
                min_l, max_l = map(int, level_str.split("-"))
                level = random.randint(min_l, max_l)
            except ValueError: # Handle cases like "20-20" or invalid ranges
                level = int(level_str.split("-")[0]) if level_str.split("-")[0].isdigit() else 1
        else:
            level = int(level_str) if level_str.isdigit() else 1

        if level_override is not None:
            level = level_override

        # Create stats
        stats = EnemyStats(
            level=level,
            max_hp=data.get("max_hp", 10),
            max_mp=data.get("max_mp", 0),
            attack=data.get("attack", 1),
            defense=data.get("defense", 0),
            m_attack=data.get("m_attack", 0),
            m_defense=data.get("m_defense", 0),
            agility=data.get("agility", 1),
            luck=data.get("luck", 1)
        )

        # Scale stats based on level (if base stats are for level 1, or adjust logic)
        # Assuming the CSV stats are base stats that might need scaling.
        # If CSV already contains scaled stats per level, this might not be needed or needs adjustment.
        # For now, let's assume a simple scaling from a base if the enemy's own level_str was a range.
        # If the enemy has a fixed level in CSV, its stats are likely for that level.
        
        # This scaling logic might need refinement based on how CSV stats are intended.
        # If stats in CSV are for the MINIMUM level of the range, then scaling is appropriate.
        base_level_for_stats = 1
        if "-" in level_str:
            try:
                base_level_for_stats = int(level_str.split("-")[0])
            except ValueError:
                base_level_for_stats = 1
        else:
            base_level_for_stats = int(level_str) if level_str.isdigit() else 1

        if level > base_level_for_stats:
            level_diff = level - base_level_for_stats
            level_multiplier = 1 + (level_diff * 0.1) # 10% increase per level above base
            stats.max_hp = int(stats.max_hp * level_multiplier)
            stats.attack = int(stats.attack * level_multiplier)
            stats.defense = int(stats.defense * level_multiplier)
            stats.m_attack = int(stats.m_attack * level_multiplier)
            stats.m_defense = int(stats.m_defense * level_multiplier)
            # Agility and Luck might not scale or scale differently
            # stats.agility = int(stats.agility * level_multiplier)
            # stats.luck = int(stats.luck * level_multiplier)


        return Enemy(
            name=display_name_for_instance, # Use the key from the database as the canonical name
            enemy_type=data.get("type", "Physical"),
            rarity=data.get("rarity", "Common"),
            stats=stats,
            abilities=data.get("abilities", []),
            loot=data.get("loot", [])
        )

    def get_enemies_by_level(self, min_level: int, max_level: int) -> List[str]:
        """Get list of enemy names within level range"""
        suitable_enemies = []

        for name, data in self.enemies.items():
            level_str = data.get("level_range", "1")
            enemy_min_lvl, enemy_max_lvl = 1, 1
            if "-" in level_str:
                try:
                    enemy_min_lvl, enemy_max_lvl = map(int, level_str.split("-"))
                except ValueError: # Handle "20-20" or other non-standard ranges
                    enemy_min_lvl = enemy_max_lvl = int(level_str.split("-")[0]) if level_str.split("-")[0].isdigit() else 1
            else:
                enemy_min_lvl = enemy_max_lvl = int(level_str) if level_str.isdigit() else 1
            
            # Check if enemy level range overlaps with requested range
            if not (enemy_max_lvl < min_level or enemy_min_lvl > max_level):
                suitable_enemies.append(name)

        return suitable_enemies

    def get_random_enemy(self, player_level: int) -> Optional[Enemy]:
        """Get a random enemy appropriate for player level"""
        # Get enemies within 2 levels of player
        suitable_enemies = self.get_enemies_by_level(
            max(1, player_level - 2), 
            player_level + 2
        )
        
        if not suitable_enemies:
            # Fallback to any enemy
            suitable_enemies = list(self.enemies.keys())
            
        if suitable_enemies:
            enemy_name = random.choice(suitable_enemies)
            return self.create_enemy(enemy_name)
            
        return None