"""
Utility functions and constants for the Bestiary system.
"""
import os
import csv
from typing import Dict, List, Any, Optional
from enemy import EnemyDatabase, Enemy # Assuming EnemyDatabase and Enemy are in enemy.py

# ANSI escape codes for colors
# (These might not work on all terminals, e.g., Windows CMD by default)
class Colors:
    """ANSI color codes for console output."""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GREY = "\033[90m" # Bright black, often used as grey

RARITY_COLORS: Dict[str, str] = {
    "common": Colors.WHITE,
    "uncommon": Colors.GREEN,
    "rare": Colors.BLUE,
    "rare elite": Colors.BLUE, # Treat same as Rare for now
    "epic": Colors.MAGENTA,
    "legendary": Colors.YELLOW,
    "mythical": Colors.RED,
    "spawned": Colors.CYAN,
    "default": Colors.WHITE # Fallback
}

ZONE_NAME_COLORS: Dict[str, str] = {
    # Exact zone names as they appear after .title() and replace('_', ' ')
    "shapira plains": Colors.GREEN, # Light green
    "central shapira forest": "\033[38;2;0;100;0m", # Dark Green (using a darker standard green)
    "goblin camp": Colors.GREY, # Slight light grey
    "dungeon wahsh den": "\033[38;2;124;252;0m", # Slime green (lime)
    "west shapira mountains": "\033[38;2;160;82;45m", # Light Brown (sienna)
    "dungeon goblin fortress": "\033[38;2;105;105;105m", # Dark Grey (dim gray)
    "desert zone": "\033[38;2;237;145;33m", # Desert orange (dark orange / sandy brown)
    "volcanic zone": "\033[38;2;255;69;0m", # Dark Orange (orangered)
    "dungeon fallen dyansty ruins": "\033[38;2;218;165;32m", # Light Gold (goldenrod)
    "ice continent": Colors.CYAN, # Light blue
    "arch devil citadel": "\033[38;2;255;165;0m", # Light orange
    "fang of the fallen god": "\033[38;2;0;128;128m", # Teal
    "chaotic zone": "\033[38;2;240;248;255m", # Whiteish (aliceblue)
    "sheol": "\033[38;2;139;0;0m", # Dark red
    "edge of eternity": "\033[38;2;199;21;133m", # Dark Pink (mediumvioletred)
    "grand palace of sheol": "\033[38;2;128;0;0m", # Maroon
    "outside eternity": "\033[38;2;75;0;130m", # Dark Purple (indigo)
    "default": Colors.WHITE # Fallback for any unlisted zones
}


def format_text_color(text: str, color_name_or_code: str) -> str:
    """
    Formats text with a specified color using ANSI codes.
    color_name_or_code can be a key from RARITY_COLORS/ZONE_NAME_COLORS or a direct ANSI code.
    """
    if color_name_or_code.startswith("\033["): # It's a direct ANSI code
        color_code = color_name_or_code
    else: # It's a color name
        color_code = RARITY_COLORS.get(color_name_or_code.lower(), # Check rarity first
                       ZONE_NAME_COLORS.get(color_name_or_code.lower(), # Then zone names
                                             Colors.WHITE)) # Fallback to white
    # The line above correctly sets color_code, so the following was redundant and incorrect:
    # color_code = RARITY_COLORS.get(color_name.lower(), RARITY_COLORS["default"])
    return f"{color_code}{text}{Colors.RESET}"

def get_zone_level_range_display(enemies_in_zone: List[Dict[str, Any]]) -> str:
    """Calculates and formats the level range string for a zone based on its enemies."""
    if not enemies_in_zone:
        return "N/A"
    
    min_level = float('inf')
    max_level = float('-inf')
    
    for enemy_details in enemies_in_zone:
        level = enemy_details.get("level")
        if level is not None:
            min_level = min(min_level, level)
            max_level = max(max_level, level)
            
    if min_level == float('inf'): # No enemies had levels
        return "N/A"
    if min_level == max_level:
        return f"Lv {min_level}"
    return f"Lv {min_level}-{max_level}"


def load_zone_data(zone_folder_path: str, enemy_db: EnemyDatabase) -> Dict[str, Dict[str, Any]]:
    """
    Loads enemy data for each zone from .txt files.
    Each zone file lists enemy display names and their internal ID names.
    The function fetches full enemy details (like level and rarity) from the EnemyDatabase.
    """
    zones_data: Dict[str, Dict[str, Any]] = {}
    print(f"[DEBUG BestiaryUtils] Attempting to load zone data from: {zone_folder_path}")
    if not os.path.exists(zone_folder_path):
        print(f"[DEBUG BestiaryUtils] CRITICAL: Zone data folder not found at {zone_folder_path}")
        return zones_data
    
    if not enemy_db or not enemy_db.enemies:
        print("[DEBUG BestiaryUtils] CRITICAL: EnemyDatabase is empty or not provided to load_zone_data.")
        return zones_data
    else:
        print(f"[DEBUG BestiaryUtils] EnemyDatabase has {len(enemy_db.enemies)} entries. First 5 keys: {list(enemy_db.enemies.keys())[:5]}")


    for filename in os.listdir(zone_folder_path):
        if filename.endswith(".txt"):
            zone_name_pretty = filename[:-4].replace("_", " ").title()
            filepath = os.path.join(zone_folder_path, filename)
            print(f"[DEBUG BestiaryUtils] Processing zone file: {filename} for zone: {zone_name_pretty}")
            
            current_zone_enemies: List[Dict[str, Any]] = []
            zone_level_range_from_file = "N/A"

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    in_loot_section = False
                    for line_num, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue

                        if line.upper().startswith("LEVEL_RANGE:"):
                            in_loot_section = False
                            zone_level_range_from_file = line.split(":", 1)[1].strip()
                            print(f"[DEBUG BestiaryUtils] Zone '{zone_name_pretty}' - LEVEL_RANGE from file: {zone_level_range_from_file}")
                            continue
                        
                        parts = line.split(',')
                        if len(parts) == 2:
                            in_loot_section = False
                            display_name = parts[0].strip()
                            enemy_id_from_file = parts[1].strip()
                            # print(f"[DEBUG BestiaryUtils] Zone '{zone_name_pretty}' - File line: Display='{display_name}', ID='{enemy_id_from_file}'")
                            
                            found_db_key = None
                            # Normalize by removing spaces and underscores, then lowercasing
                            normalized_id_from_file = enemy_id_from_file.lower().replace("_", "").replace(" ", "")
                            
                            for db_key in enemy_db.enemies.keys():
                                normalized_db_key = db_key.lower().replace("_", "").replace(" ", "")
                                if normalized_db_key == normalized_id_from_file:
                                    found_db_key = db_key
                                    break
                            
                            enemy_instance: Optional[Enemy] = None
                            if found_db_key:
                                # print(f"[DEBUG BestiaryUtils] Zone '{zone_name_pretty}' - Matched ID '{enemy_id_from_file}' to DB key '{found_db_key}'")
                                enemy_instance = enemy_db.create_enemy(found_db_key)
                            
                            if enemy_instance:
                                # print(f"[DEBUG BestiaryUtils] Zone '{zone_name_pretty}' - Successfully created instance for '{enemy_instance.name}', Level: {enemy_instance.stats.level}, Rarity: {enemy_instance.rarity}")
                                current_zone_enemies.append({
                                    "display_name": display_name, # Keep display name from zone file for the list
                                    "id_name": found_db_key, # Store the actual database key for later use
                                    "level": enemy_instance.stats.level,
                                    "rarity": enemy_instance.rarity
                                })
                            else:
                                print(f"[DEBUG BestiaryUtils] WARNING: Enemy ID '{enemy_id_from_file}' (from zone '{zone_name_pretty}') not found in database. Searched for key like '{normalized_id_from_file}', found_db_key: '{found_db_key}'.")
                        elif line_num > 0:
                            # Only warn if the line is not a loot line, not a header, and not an enemy definition
                            if not line:
                                continue
                            if line.upper().startswith("LEVEL_RANGE:"):
                                in_loot_section = False
                                continue
                            if ',' in line and not line.startswith(' '):
                                in_loot_section = False
                                continue  # enemy definition
                            lstripped = line.lstrip()
                            # Start loot section
                            if lstripped.lower() == 'loot:':
                                in_loot_section = True
                                continue
                            # Accept loot lines: indented, start with dash/bullet, or are loot headers
                            if (
                                line.startswith(' ') or line.startswith('\t') or
                                lstripped.startswith('-') or lstripped.startswith('•') or
                                lstripped.lower() == '(no loot listed)'
                            ):
                                continue
                            # Accept any line in a loot section (until next enemy/section)
                            if in_loot_section:
                                continue
                            print(f"[DEBUG BestiaryUtils] WARNING: Malformed line in {filename}: '{line}'")
                
                actual_level_range_display = get_zone_level_range_display(current_zone_enemies)
                print(f"[DEBUG BestiaryUtils] Zone '{zone_name_pretty}' - Calculated actual level range: {actual_level_range_display}. Found {len(current_zone_enemies)} enemies.")

                zones_data[zone_name_pretty] = {
                    "file_level_range": zone_level_range_from_file,
                    "actual_level_range": actual_level_range_display,
                    "enemies": sorted(current_zone_enemies, key=lambda x: (x.get('level', 0), x.get('display_name', '')))
                }
                if not current_zone_enemies:
                    print(f"[DEBUG BestiaryUtils] WARNING: Zone '{zone_name_pretty}' has no enemies loaded into its list.")


            except Exception as e:
                print(f"Error loading zone file {filename}: {e}")
    
    if not zones_data:
        print("[DEBUG BestiaryUtils] CRITICAL: No zones were loaded into zones_data.")
    else:
        print(f"[DEBUG BestiaryUtils] Finished loading all zone data. Total zones loaded: {len(zones_data)}. Zone keys: {list(zones_data.keys())}")
                
    return zones_data

def get_loot_rarity(item_name: str) -> str:
    """
    Looks up the rarity of a loot item by name from loot_rarity_master.txt.
    Supports format: Item Name = (Rarity)
    Returns 'common' if not found. Uses robust normalization for matching.
    Skips headers and comments robustly.
    Uses absolute path for loot_rarity_master.txt.
    """
    import re
    loot_master_path = os.path.join(os.path.dirname(__file__), 'data', 'csv', 'loot_rarity_master.txt')
    def norm(s):
        return s.strip().lower().replace('_', '').replace(' ', '').replace("'", '').replace('-', '').replace('.', '')
    try:
        with open(loot_master_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    name, rarity_part = line.split('=', 1)
                    name = name.strip()
                    match = re.search(r'\(([^)]+)\)', rarity_part)
                    if match:
                        rarity = match.group(1).strip().lower()
                        if norm(name) == norm(item_name):
                            return rarity
                # fallback: support old comma format if present
                elif ',' in line:
                    name, rarity = line.split(',', 1)
                    if norm(name) == norm(item_name):
                        return rarity.strip().lower()
    except Exception as e:
        print(f"[DEBUG BestiaryUtils] Error in get_loot_rarity: {e}")
    return "common"

def format_loot_list_colored(loot_list) -> str:
    """
    Returns a string with each loot item colored according to its rarity, using loot_rarity_master.txt.
    """
    colored_loot = []
    for item in loot_list:
        rarity = get_loot_rarity(item)
        colored_loot.append(format_text_color(item, rarity))
    return ", ".join(colored_loot)

def get_enemy_loot_from_zone_file(zone_file_path: str, enemy_id: str) -> List[str]:
    """
    Parses the given zone .txt file and returns a unique, ordered list of loot items for the specified enemy_id.
    Handles all loot formats: dashed, bulleted, indented, or plain lines after 'Loot:'.
    """
    loot_items = []
    found_enemy = False
    in_loot_section = False
    def norm(s):
        return s.lower().replace('_', '').replace(' ', '')
    try:
        with open(zone_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line.strip():
                    continue
                # Enemy line
                if not line.startswith(' ') and ',' in line:
                    parts = line.split(',', 1)
                    if len(parts) == 2 and norm(parts[1].strip()) == norm(enemy_id):
                        found_enemy = True
                        in_loot_section = False
                        continue
                    else:
                        found_enemy = False
                        in_loot_section = False
                if found_enemy:
                    lstripped = line.lstrip()
                    # Start loot section
                    if lstripped.lower() == 'loot:':
                        in_loot_section = True
                        continue
                    # End loot section if new enemy or section header
                    if (not line.startswith(' ') and ',' in line) or lstripped.lower().startswith('level_range:'):
                        in_loot_section = False
                        found_enemy = False
                        continue
                    # Collect loot lines in loot section
                    if in_loot_section:
                        if lstripped.lower() == '(no loot listed)' or lstripped.lower() == 'loot:':
                            continue
                        # Accept any non-empty line as loot
                        item = lstripped.lstrip('-•').strip()
                        if item and item not in loot_items:
                            loot_items.append(item)
                    # Also support old format: indented/dashed/bulleted lines directly after enemy
                    elif lstripped.startswith('-') or lstripped.startswith('•'):
                        item = lstripped.lstrip('-•').strip()
                        if item and item not in loot_items:
                            loot_items.append(item)
                    # Stop if next enemy encountered (for old format)
                    elif not line.startswith(' '):
                        break
    except Exception as e:
        print(f"[DEBUG BestiaryUtils] Error reading loot for enemy '{enemy_id}' from '{zone_file_path}': {e}")
    return loot_items