"""
Zone and travel system for the Python console RPG
Handles world map, zone details, encounters, and resources
"""

import random
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from bestiary_utils import ZONE_NAME_COLORS, Colors, RARITY_COLORS # Added for formatting
from bestiary import Bestiary # Added for type hinting and access
from enemy import EnemyDatabase, Enemy

@dataclass
class ZoneResource:
    """Defines a resource that can be gathered in a zone"""
    name: str
    quantity_min: int
    quantity_max: int
    chance: float  # 0.0 to 1.0

@dataclass
class ZoneData:
    """Holds data for a specific game zone"""
    name: str
    description: str
    min_level: int
    max_level: int
    encounter_rate: float  # Base rate, e.g., 0.3 for 30% chance per step
    possible_enemies: List[str]  # Names of enemies that can appear
    resources: List[ZoneResource]  # Resources that can be gathered
    travel_time_hours: int = 1 # Hours it takes to travel to this zone
    is_safe_zone: bool = False # No encounters if true

class ZoneSystem:
    """Manages game zones, travel, and zone-specific interactions"""

    def __init__(self, enemy_db: Optional[EnemyDatabase] = None):
        self.enemy_database = enemy_db if enemy_db else EnemyDatabase()
        self.zones: Dict[str, ZoneData] = self._initialize_zones()
        self.current_zone: Optional[str] = "Cave Home" # Start in the cave

    def _initialize_zones(self) -> Dict[str, ZoneData]:
        """Initialize all game zones with their data"""
        # This data should ideally be loaded from a file, but for simplicity:
        zones_data = {
            "Cave Home": ZoneData(
                name="Cave Home",
                description="A safe and quiet cave, your sanctuary.",
                min_level=1,
                max_level=1,
                encounter_rate=0.0,
                possible_enemies=[],
                resources=[],
                travel_time_hours=0,
                is_safe_zone=True
            ),
            "Outside Eternity": ZoneData(
                name="Outside Eternity",
                description="The outermost realm of existence, where reality frays at the edges.",
                min_level=100,
                max_level=120,
                encounter_rate=0.40,
                possible_enemies=["Sealed Titan", "Blood Demon Drinker", "Blood Demon Flayer"],
                resources=[
                    ZoneResource(name="Eternity Crystal", quantity_min=1, quantity_max=3, chance=0.3),
                    ZoneResource(name="Void Essence", quantity_min=1, quantity_max=2, chance=0.2)
                ],
                travel_time_hours=24
            ),
            "Grand Palace Of Sheol": ZoneData(
                name="Grand Palace Of Sheol",
                description="The magnificent palace at the heart of Sheol, home to the most powerful entities.",
                min_level=90,
                max_level=105,
                encounter_rate=0.40,
                possible_enemies=["Dark Servant Warrior", "Dark Servant Evoker", "Dark Servant Shade"],
                resources=[
                    ZoneResource(name="Royal Sheol Crystal", quantity_min=1, quantity_max=2, chance=0.3),
                    ZoneResource(name="Corrupted Palace Stone", quantity_min=1, quantity_max=3, chance=0.4)
                ],
                travel_time_hours=20
            ),
            "Edge Of Eternity": ZoneData(
                name="Edge Of Eternity",
                description="The border between worlds, where time and space become fluid.",
                min_level=86,
                max_level=105,
                encounter_rate=0.35,
                possible_enemies=["Twisted Behemoth", "Corrupted Fey Sprite"],
                resources=[
                    ZoneResource(name="Eternity Fragment", quantity_min=1, quantity_max=2, chance=0.3),
                    ZoneResource(name="Temporal Dust", quantity_min=1, quantity_max=3, chance=0.4)
                ],
                travel_time_hours=18
            ),
            "Chaotic Zone": ZoneData(
                name="Chaotic Zone",
                description="A realm of pure chaos and unpredictability.",
                min_level=65,
                max_level=95,
                encounter_rate=0.45,
                possible_enemies=["Umbra Slime", "Radiant Slime"],
                resources=[
                    ZoneResource(name="Chaos Crystal", quantity_min=1, quantity_max=3, chance=0.4),
                    ZoneResource(name="Unstable Matter", quantity_min=1, quantity_max=4, chance=0.5)
                ],
                travel_time_hours=16
            ),
            "Sheol": ZoneData(
                name="Sheol",
                description="The dark underworld, home to ancient demons and forgotten souls.",
                min_level=76,
                max_level=90,
                encounter_rate=0.40,
                possible_enemies=["Demon Imp Knight", "Demon Imp Sorcerer"],
                resources=[
                    ZoneResource(name="Sheol Stone", quantity_min=1, quantity_max=3, chance=0.4),
                    ZoneResource(name="Dark Essence", quantity_min=1, quantity_max=2, chance=0.3)
                ],
                travel_time_hours=15
            ),
            "Fang Of The Fallen God": ZoneData(
                name="Fang Of The Fallen God",
                description="A jagged mountain formation said to be the remains of a divine being.",
                min_level=65,
                max_level=80,
                encounter_rate=0.35,
                possible_enemies=["Dark Goblin Warrior", "Dark Goblin Slayer", "Dark Goblin Elite Protector"],
                resources=[
                    ZoneResource(name="Divine Fragment", quantity_min=1, quantity_max=2, chance=0.2),
                    ZoneResource(name="Crystallized Faith", quantity_min=1, quantity_max=3, chance=0.3)
                ],
                travel_time_hours=14
            ),
            "Arch Devil Citadel": ZoneData(
                name="Arch Devil Citadel",
                description="A fortress of the demon lords, built from dark stone and malice.",
                min_level=54,
                max_level=70,
                encounter_rate=0.40,
                possible_enemies=["Dark Goblin King Brinrib", "Demon Imp Knight"],
                resources=[
                    ZoneResource(name="Demonic Steel", quantity_min=1, quantity_max=3, chance=0.4),
                    ZoneResource(name="Infernal Coal", quantity_min=2, quantity_max=4, chance=0.5)
                ],
                travel_time_hours=13
            ),
            "Ice Continent": ZoneData(
                name="Ice Continent",
                description="A vast frozen landscape where few creatures can survive.",
                min_level=48,
                max_level=60,
                encounter_rate=0.30,
                possible_enemies=["Ice Slime", "Stone Fur Lynx"],
                resources=[
                    ZoneResource(name="Eternal Ice", quantity_min=2, quantity_max=4, chance=0.6),
                    ZoneResource(name="Frozen Crystal", quantity_min=1, quantity_max=2, chance=0.3)
                ],
                travel_time_hours=12
            ),
            "Dungeon Fallen Dynasty Ruins": ZoneData(
                name="Dungeon Fallen Dynasty Ruins",
                description="The crumbling remains of an ancient civilization.",
                min_level=45,
                max_level=51,
                encounter_rate=0.45,
                possible_enemies=["Earth Elemental", "Rock Golem"],
                resources=[
                    ZoneResource(name="Ancient Relic", quantity_min=1, quantity_max=2, chance=0.3),
                    ZoneResource(name="Dynasty Stone", quantity_min=1, quantity_max=3, chance=0.4)
                ],
                travel_time_hours=10
            ),
            "Volcanic Zone": ZoneData(
                name="Volcanic Zone",
                description="An area of active volcanoes and geothermal activity.",
                min_level=36,
                max_level=51,
                encounter_rate=0.35,
                possible_enemies=["Fire Slime", "Earth Slime"],
                resources=[
                    ZoneResource(name="Volcanic Rock", quantity_min=2, quantity_max=4, chance=0.5),
                    ZoneResource(name="Fire Crystal", quantity_min=1, quantity_max=2, chance=0.3)
                ],
                travel_time_hours=9
            ),
            "Desert Zone": ZoneData(
                name="Desert Zone",
                description="A harsh, dry landscape with minimal vegetation and extreme temperatures.",
                min_level=30,
                max_level=37,
                encounter_rate=0.30,
                possible_enemies=["Earth Slime", "Mountain Troll"],
                resources=[
                    ZoneResource(name="Desert Sand", quantity_min=3, quantity_max=6, chance=0.7),
                    ZoneResource(name="Cactus Fruit", quantity_min=1, quantity_max=3, chance=0.4)
                ],
                travel_time_hours=8
            ),
            "Dungeon Goblin Fortress": ZoneData(
                name="Dungeon Goblin Fortress",
                description="A stronghold built by goblins to defend their territory.",
                min_level=26,
                max_level=35,
                encounter_rate=0.40,
                possible_enemies=["Goblin Brute", "Goblin Blacksmith", "Goblin Mage"],
                resources=[
                    ZoneResource(name="Goblin Crafted Metal", quantity_min=1, quantity_max=3, chance=0.4),
                    ZoneResource(name="Goblin Banner", quantity_min=1, quantity_max=1, chance=0.2)
                ],
                travel_time_hours=7
            ),
            "West Shapira Mountains": ZoneData(
                name="West Shapira Mountains",
                description="A range of mountains with diverse wildlife and treacherous paths.",
                min_level=21,
                max_level=25,
                encounter_rate=0.35,
                possible_enemies=["Alpine Bandit", "Thunder Bird", "Stone Fur Lynx"],
                resources=[
                    ZoneResource(name="Mountain Herb", quantity_min=1, quantity_max=3, chance=0.5),
                    ZoneResource(name="Pure Mountain Water", quantity_min=1, quantity_max=2, chance=0.4)
                ],
                travel_time_hours=6
            ),
            "Dungeon Wahsh Den": ZoneData(
                name="Dungeon Wahsh Den",
                description="The underground lair of the Wahsh creatures.",
                min_level=17,
                max_level=20,
                encounter_rate=0.45,
                possible_enemies=["Wahsh Hunter", "Mature Wahsh", "Wahsh Juggernaught"],
                resources=[
                    ZoneResource(name="Wahsh Hide", quantity_min=1, quantity_max=2, chance=0.4),
                    ZoneResource(name="Wahsh Claw", quantity_min=1, quantity_max=3, chance=0.3)
                ],
                travel_time_hours=5
            ),
            "Central Shapira Forest": ZoneData(
                name="Central Shapira Forest",
                description="A dense forest at the heart of the Shapira region.",
                min_level=10,
                max_level=20,
                encounter_rate=0.35,
                possible_enemies=["Leaf Lurker", "Forest Serpent", "Treant Elder"],
                resources=[
                    ZoneResource(name="Forest Wood", quantity_min=2, quantity_max=4, chance=0.6),
                    ZoneResource(name="Medicinal Herbs", quantity_min=1, quantity_max=3, chance=0.5)
                ],
                travel_time_hours=4
            ),
            "Goblin Camp": ZoneData(
                name="Goblin Camp",
                description="A temporary settlement of goblins in the wilderness.",
                min_level=15,
                max_level=18,
                encounter_rate=0.40,
                possible_enemies=["Goblin Scout", "Goblin Slasher", "Goblin King Brinrib"],
                resources=[
                    ZoneResource(name="Goblin Tools", quantity_min=1, quantity_max=2, chance=0.3),
                    ZoneResource(name="Stolen Goods", quantity_min=1, quantity_max=2, chance=0.4)
                ],
                travel_time_hours=3
            ),
            "Shapira Plains": ZoneData(
                name="Shapira Plains",
                description="Open grasslands teeming with small wildlife and beginner threats.",
                min_level=1,
                max_level=10,
                encounter_rate=0.25,
                possible_enemies=["Squirrelkin", "Swift Sparrow", "Goblin Forager", "Wahshling"],
                resources=[
                    ZoneResource(name="Wild Berries", quantity_min=1, quantity_max=3, chance=0.6),
                    ZoneResource(name="Plain Grass", quantity_min=2, quantity_max=5, chance=0.8),
                    ZoneResource(name="Small Stone", quantity_min=1, quantity_max=2, chance=0.4)
                ],
                travel_time_hours=2
            )
        }
        return zones_data

    def get_zone_data(self, zone_name: str) -> Optional[ZoneData]:
        """Get data for a specific zone"""
        return self.zones.get(zone_name)

    def get_available_zones(self, discovered_zones: Optional[List[str]] = None) -> List[str]:
        """Get a list of zones available for travel"""
        # Get all zones except the current one if it's Cave Home
        if self.current_zone == "Cave Home":
            available_zones = [zone for zone in self.zones.keys() if zone != "Cave Home"]
        else:
            available_zones = list(self.zones.keys())
            
        # Sort zones by level in descending order (highest to lowest)
        sorted_zones = sorted(
            available_zones,
            key=lambda zone_name: self.zones[zone_name].max_level,
            reverse=True
        )
        
        return sorted_zones

    def travel_to_zone(self, zone_name: str) -> Tuple[bool, str, int]:
        """
        Attempt to travel to a new zone.
        Returns (success, message, time_taken_hours)
        """
        if zone_name not in self.zones:
            return False, f"Zone '{zone_name}' does not exist.", 0

        zone_data = self.zones[zone_name]
        if self.current_zone == zone_name:
            return False, f"You are already in {zone_name}.", 0

        # Here you could add checks for player level, required items, etc.
        self.current_zone = zone_name
        return True, f"You have arrived at {zone_name}.", zone_data.travel_time_hours

    def generate_encounter(self, player_level: Optional[int] = 1) -> List[Enemy]:
        """
        Generate a list of enemies for an encounter in the current zone.
        Returns an empty list if no encounter occurs.
        """
        if self.current_zone is None:
            return []

        zone_data = self.get_zone_data(self.current_zone)
        if not zone_data or zone_data.is_safe_zone:
            return []

        # Check encounter rate
        if random.random() > zone_data.encounter_rate:
            return [] # No encounter

        # Determine number of enemies (e.g., 1 to 3)
        num_enemies = random.randint(1, min(3, len(zone_data.possible_enemies) if zone_data.possible_enemies else 1))
        encounter_enemies: List[Enemy] = []

        possible_enemies_in_zone = [
            name for name in zone_data.possible_enemies
            if self.enemy_database.enemies.get(name) # Ensure enemy exists in DB
        ]

        if not possible_enemies_in_zone: # No valid enemies for this zone
            return []


        for _ in range(num_enemies):
            # Filter enemies by level appropriateness if player_level is provided
            # For simplicity, we'll pick randomly from the zone's list for now.
            # A more advanced system would filter based on zone_data.min_level/max_level
            # and potentially player_level.
            enemy_name = random.choice(possible_enemies_in_zone)
            enemy_instance = self.enemy_database.create_enemy(enemy_name, level_override=None)
            if enemy_instance:
                # Adjust enemy level slightly based on zone's min/max if needed
                # For now, create_enemy handles basic level randomization from its template
                encounter_enemies.append(enemy_instance)

        return encounter_enemies


    def gather_resources(self) -> Dict[str, int]:
        """
        Attempt to gather resources in the current zone.
        Returns a dictionary of gathered items and their quantities.
        """
        gathered_items: Dict[str, int] = {}
        if self.current_zone is None:
            return gathered_items
        
        zone_data = self.get_zone_data(self.current_zone)
        if not zone_data or not zone_data.resources:
            return gathered_items
        
        for resource_info in zone_data.resources:
            if random.random() < resource_info.chance:
                quantity = random.randint(resource_info.quantity_min, resource_info.quantity_max)
                if quantity > 0:
                    gathered_items[resource_info.name] = gathered_items.get(resource_info.name, 0) + quantity
        
        # Small chance to find a crafting profession book while gathering
        if random.random() < 0.05:  # 5% chance
            books = [
                "Introduction to Alchemy",
                "Introduction to Blacksmithing",
                "Introduction to Cloth Work",
                "Introduction to Cooking",
                "Introduction to Lapidary",
                "Introduction to Leatherwork",
                "Introduction to Woodworking"
            ]
            book = random.choice(books)
            gathered_items[book] = 1
            
        return gathered_items

    def get_current_zone_name(self) -> Optional[str]:
        """Returns the name of the current zone."""
        return self.current_zone

    def get_current_zone_description(self) -> str:
        """Returns the description of the current zone."""
        if self.current_zone:
            zone_data = self.get_zone_data(self.current_zone)
            if zone_data:
                return zone_data.description
        return "You are in an unknown location."
    
    def display_zone_art(self, ui):
        """Display ASCII art for the current zone"""
        if self.current_zone:
            ui.show_zone_art(self.current_zone)

    def to_dict(self) -> Dict[str, Any]:
        """Convert zone system state to dictionary for saving"""
        return {
            'current_zone': self.current_zone
            # Other zone-specific persistent data could be added here
        }

    def load_from_dict(self, data: Dict[str, Any]):
        """Load zone system state from dictionary"""
        self.current_zone = data.get('current_zone', "Cave Home")

    def get_formatted_travel_options(self, coming_from_cave_home: bool) -> List[str]:
        """
        Prepares a list of formatted zone names for the travel menu.
        Includes level information and color coding.
        """
        zones = self.get_available_zones() # This already sorts by level descending

        options = []
        for i, zone_name in enumerate(zones):
            zone_data = self.get_zone_data(zone_name)
            zone_color_code = ZONE_NAME_COLORS.get(zone_name.lower(), Colors.WHITE)
            
            if zone_data:
                options.append(
                    f"{i+1}. {zone_color_code}{zone_name}{Colors.RESET} "
                    f"(Level {zone_data.min_level}-{zone_data.max_level})"
                )
            else:
                options.append(f"{i+1}. {zone_color_code}{zone_name}{Colors.RESET}")
        
        options.append(f"{len(zones)+1}. Back") # Generic back option
        return options

    def get_formatted_zone_details(self, bestiary: Bestiary) -> List[str]:
        """
        Prepares a list of strings containing formatted details for the current zone.
        Includes description, level range, enemies, and gatherables.
        """
        details = []
        if not self.current_zone:
            details.append("No current zone selected.")
            return details

        zone_data = self.get_zone_data(self.current_zone)
        if not zone_data:
            details.append(f"Could not retrieve data for {self.current_zone}.")
            return details

        # Zone Description and Level
        details.append(f"Description: {zone_data.description}")
        details.append(f"Level Range: {zone_data.min_level}-{zone_data.max_level}")
        details.append("\n=== Zone Information ===")

        # Enemies
        details.append("\nEnemies:")
        discovered_enemies = bestiary.discovered_enemies
        if zone_data.possible_enemies:
            for enemy_name in zone_data.possible_enemies:
                if enemy_name in discovered_enemies:
                    enemy = self.enemy_database.create_enemy(enemy_name) # enemy_database is part of ZoneSystem
                    if enemy:
                        rarity_color = RARITY_COLORS.get(enemy.rarity.lower(), Colors.WHITE)
                        details.append(f"  - {rarity_color}{enemy.name}{Colors.RESET}")
                    else:
                        details.append(f"  - {enemy_name}") # Fallback if enemy creation fails
                else:
                    details.append(f"  - ???")
        else:
            details.append("  None known.")

        # Gatherables
        details.append("\nGatherables:")
        if zone_data.resources:
            discovered_gatherables = bestiary.get_discovered_gatherables(self.current_zone)
            for resource in zone_data.resources:
                if resource.name in discovered_gatherables:
                    details.append(f"  - {resource.name}")
                else:
                    details.append(f"  - ???")
        else:
            details.append("  None known.")
            
        return details