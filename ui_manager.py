"""
UI Manager for the Python console RPG
Handles all user interface and input/output operations
"""

import os
import platform # For platform-specific checks
try:
    import msvcrt  # For Windows key capture
    MSVCRT_AVAILABLE = True
except ImportError:
    MSVCRT_AVAILABLE = False # Not on Windows or msvcrt not available
from typing import List, Optional, Dict, Any, Tuple
from player import Player

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BROWN = "\033[38;5;130m"  # Special brown color for cave art
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Styles
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    STRIKE = "\033[9m"

class UIManager:
    """Manages console-based user interface"""

    BOX_CHARS = {
        'TL': "╔", 'TR': "╗", 'BL': "╚", 'BR': "╝",
        'H': "═", 'V': "║",
        'ML': "╠", 'MR': "╣",
        # Optional: 'MJ': "╬", 'TJ': "╦", 'BJ': "╩", 'H_THIN': "─", 'V_THIN': "│"
    }
    
    def __init__(self):
        self.width = 80
        self.separator = "=" * self.width
        self.thin_separator = "-" * self.width

        # Menu Definitions
        self.COMBAT_MENU_OPTIONS = [
            "1. Attack",
            "2. Magic Attack",
            "3. Defend",
            "4. Use Item",
            "5. Run Away"
        ]
        self.MAIN_MENU_OPTIONS = [
            "1. New Game",
            "2. Load Game",
            "3. Settings",
            "4. Exit"
        ]
        self.GAMEPLAY_MENU_OPTIONS = [
            "1. Explore",
            "2. View Inventory",
            "3. View Character Stats",
            "4. Crafting",
            "5. Save Game",
            "6. Load Game",
            "7. Exit to Main Menu"
        ]
        self.EXPLORATION_OPTIONS = [
            "1. Move to a new area",
            "2. Search for resources",
            "3. Rest",
            "4. Return to previous menu"
        ]
        self.INVENTORY_MENU_OPTIONS = [
            "1. Use Item",
            "2. Equip Item",
            "3. Unequip Item",
            "4. Drop Item",
            "5. Back"
        ]
        self.STORAGE_MENU_OPTIONS = [
            "1. Store Item",
            "2. Retrieve Item",
            "3. Back"
        ]
        self.SETTINGS_MENU_OPTIONS = [
            "1. Adjust Text Speed (Not Implemented)",
            "2. Sound On/Off (Not Implemented)",
            "3. Back to Main Menu"
        ]
        self.CLASS_CHOICE_OPTIONS = ["Warrior", "Mage", "Rogue"] # Example classes
        
        # Load ASCII art assets
        self.title_art_content = self._load_art_asset("title_dragon_art.txt")
        self.cave_home_art_content = self._load_art_asset("cave_home_art.txt")
        self.crafting_art_content = self._load_art_asset("crafting_art.txt")
        self.storage_art_content = self._load_art_asset("storage_art.txt")
        self.default_zone_art_content = self._load_art_asset("default_zone_art.txt")

        self.zone_art_map = {
            "Shapira Plains": self._load_art_asset("zone_shapira_plains.txt"),
            "Cave Home": self.cave_home_art_content, # Re-use if it's the same
            "Goblin Camp": self._load_art_asset("zone_goblin_camp.txt"),
            "Central Shapira Forest": self._load_art_asset("zone_central_shapira_forest.txt"),
            "West Shapira Mountains": self._load_art_asset("zone_west_shapira_mountains.txt"),
            "Dungeon Goblin Fortress": self._load_art_asset("zone_goblin_fortress.txt"),
            "Volcanic Zone": self._load_art_asset("zone_volcanic_zone.txt"),
            "Ice Continent": self._load_art_asset("zone_ice_continent.txt"),
            "Dungeon Wahsh Den": self._load_art_asset("zone_wahsh_den.txt"),
        }

    def _load_art_asset(self, filename: str) -> str:
        """Helper to load a single ASCII art file."""
        # Construct the full path to the asset file
        # Assuming this script is in the root directory of the project,
        # and 'data' is a subdirectory.
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, "data", "assets", "ascii_art", filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"{Colors.RED}Warning: ASCII art file {filepath} not found.{Colors.RESET}")
            return f"ASCII art '{filename}' not found." # Placeholder text
        except Exception as e:
            print(f"{Colors.RED}Error loading ASCII art file {filepath}: {e}{Colors.RESET}")
            return f"Error loading '{filename}'."

    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Enable ANSI colors in Windows terminal, primarily for older cmd.exe
        # Modern terminals like Windows Terminal often support ANSI by default.
        if platform.system() == "Windows":
            os.system('color')
        
    def show_title(self):
        """Display the game title with colors"""
        title = f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}
{Colors.BRIGHT_CYAN}║{Colors.RESET}{Colors.BRIGHT_MAGENTA}{Colors.BOLD}                          PYTHON CONSOLE RPG                                 {Colors.RESET}{Colors.BRIGHT_CYAN}║{Colors.RESET}
{Colors.BRIGHT_CYAN}║{Colors.RESET}{Colors.BRIGHT_GREEN}                     A Turn-Based Text Adventure                             {Colors.RESET}{Colors.BRIGHT_CYAN}║{Colors.RESET}
{Colors.BRIGHT_CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
        """
        print(title)
        
        # ASCII art image below the title
        if self.title_art_content:
            print(f"{Colors.BRIGHT_CYAN}{self.title_art_content}{Colors.RESET}")
            # The original code had two similar art blocks for the title.
            # This assumes the 'cave_art' was a duplicate or variant of the main title art.
            # If 'cave_art' was distinct and intended for the title screen, 
            # it should be loaded into a separate variable and printed here.
            # For now, we'll assume it was a duplicate and only print title_art_content once more
            # or remove this second print if it was truly identical.
            # Based on the prompt, "If they are truly identical, create one external file... and load it once."
            # So, we only need to print it once if it's the same art.
            # The original code printed `shapira_plains_art` here, which was incorrect.
            # The prompt clarifies `shapira_plains_art` was for `show_zone_art`.
            # The second `ascii_art` block in the original `show_title` was identical to the first.
            # So, printing `self.title_art_content` again is correct if that was the intention of `cave_art`.
            # However, the prompt also mentions "cave_art" in show_title. If it was a *different* cave art
            # specifically for the title, it would need its own file. Given the context,
            # it's more likely the second block was a duplicate or a placeholder.
            # For simplicity and based on "load it once", we'll assume the title screen uses one main art.
            # If a distinct "cave_art" for the title screen is needed, it should be loaded separately.
            # The prompt also mentions "The ascii_art and cave_art definitions" in show_title.
            # Let's assume `cave_art` was indeed the same as `ascii_art` for the title.
            # The original code had `print(shapira_plains_art)` which was likely a bug.
            # We will print the title art once. If a second, different art was intended for the title,
            # it would need its own file and loading logic.
            # The prompt says "If they are truly identical, create one external file (e.g., generic_title_art.txt) and load it once.
            # Adjust show_title() to use this single loaded art piece as appropriate."
            # Since we named it title_dragon_art.txt, and it's loaded into self.title_art_content,
            # we just print that. The original code had two print statements for art in show_title.
            # The first was `ascii_art` (lines 75-113) and the second was `cave_art` (lines 116-155).
            # These were identical. So, we only need to print it once.
            pass # The art is printed once above.

    def show_crafting_art(self):
        """Display the crafting ASCII art"""
        if self.crafting_art_content:
            print(f"{Colors.BRIGHT_CYAN}{self.crafting_art_content}{Colors.RESET}")
            
    def show_storage_art(self):
        """Display the storage ASCII art"""
        if self.storage_art_content:
            print(f"{Colors.BRIGHT_CYAN}{self.storage_art_content}{Colors.RESET}")
            
    def get_input(self, prompt: str) -> str:
        """Get input from user with prompt"""
        return input(f"  {Colors.BRIGHT_WHITE}{prompt}{Colors.RESET}").strip()

    def _get_validated_numeric_input(self,
                                     prompt: str,
                                     min_val: int,
                                     max_val: int,
                                     allow_cancel_keyword: bool = False,
                                     cancel_keyword: str = "cancel",
                                     allow_empty_to_cancel: bool = False) -> Optional[int]:
        """
        Acquires and validates numeric input from the user within a specified range.

        Args:
            prompt: The message to display to the user.
            min_val: The minimum acceptable integer value.
            max_val: The maximum acceptable integer value.
            allow_cancel_keyword: If True, allows keyword-based cancellation.
            cancel_keyword: The string that triggers keyword cancellation.
            allow_empty_to_cancel: If True, empty input triggers cancellation.

        Returns:
            The valid integer entered by the user, or None if cancelled or invalid range.
        """
        if min_val > max_val:
            self.show_error(f"Internal Error: min_val ({min_val}) cannot be greater than max_val ({max_val}) in _get_validated_numeric_input.")
            return None

        while True:
            raw_input_str = self.get_input(prompt)

            if allow_empty_to_cancel and not raw_input_str:
                return None  # Cancelled by empty input

            if allow_cancel_keyword and raw_input_str.lower() == cancel_keyword.lower():
                return None  # Cancelled by keyword

            try:
                choice = int(raw_input_str)
                if min_val <= choice <= max_val:
                    return choice  # Valid choice
                else:
                    self.show_error(f"Invalid input. Please enter a number between {min_val} and {max_val}.")
            except ValueError:
                # Avoid showing error if it was an empty string meant for cancellation but not enabled,
                # or a non-matching cancel keyword.
                if not (allow_empty_to_cancel and not raw_input_str) and \
                   not (allow_cancel_keyword and raw_input_str.lower() == cancel_keyword.lower()):
                    self.show_error("Invalid input. Please enter a valid number.")
        
    def wait_for_input(self, prompt: str = "Press Enter to continue..."):
        """
        Wait for user to press Enter or ESC.
        Falls back to standard input() if msvcrt is not available (e.g., on non-Windows).
        """
        print(f"  {Colors.BRIGHT_WHITE}{prompt}{Colors.RESET} (Press ESC to go back if supported, otherwise Enter)")
        
        if MSVCRT_AVAILABLE:
            # Windows-specific single-key press without needing Enter
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':  # Enter key
                        return "ENTER"
                    elif key == b'\x1b':  # ESC key
                        return "ESC"
        else:
            # Fallback for non-Windows or if msvcrt is unavailable
            # Note: This will require pressing Enter after the key. ESC detection won't work here.
            input() # Simple wait for Enter
            return "ENTER" # Assume Enter was pressed, as ESC cannot be easily distinguished
        
    def confirm(self, message: str) -> bool:
        """Ask for yes/no confirmation"""
        while True:
            response = input(f"  {message} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                self.show_error("Please enter 'y' for yes or 'n' for no!")
                
    def show_player_stats(self, player: Player):
        """Display player statistics"""
        BC = self.BOX_CHARS
        panel_w = self.width
        border_col = Colors.CYAN

        # --- Title Section ---
        title_content_text = f"{Colors.YELLOW}{Colors.BOLD}{player.name}'s Statistics{Colors.RESET}"
        # Original: print(f"{border_side} {title_content_text}{' ' * (self.width - len(player.name) - 15)} {border_side}")
        # The padding was (self.width - len(player.name) - 15). Visible length of title_content_text is len(player.name) + 13
        # So padding is self.width - (vis_len_title) - 2.
        # Helper content width is panel_w - 4.
        # Content for helper: title_content_text + padding to fill (panel_w - 4)
        vis_len_title = self.get_visible_length(title_content_text)
        padding_for_title = ' ' * (panel_w - 4 - vis_len_title) if (panel_w - 4 - vis_len_title) > 0 else ''
        title_line_for_helper = f"{title_content_text}{padding_for_title}"

        self._draw_bordered_panel(
            content_lines=[title_line_for_helper],
            panel_width=panel_w, border_color=border_col,
            print_top_border=True, print_bottom_border=False
        )
        print(f"{border_col}{BC['ML']}{BC['H'] * (panel_w - 2)}{BC['MR']}{Colors.RESET}")

        # --- Main Stats Section ---
        ms = player.main_stats
        main_stats_lines_for_helper = [
            # Original: f"  {Colors.BRIGHT_CYAN}Main Stats:{Colors.RESET}{' ' * (self.width - 13)} "
            # Helper adds one space, so content for helper: f" {Colors.BRIGHT_CYAN}Main Stats:{Colors.RESET}..."
            f" {Colors.BRIGHT_CYAN}Main Stats:{Colors.RESET}",
            f"   Strength:     {int(ms.strength):2d}    Vitality:     {int(ms.vitality):2d}",
            f"   Wisdom:       {int(ms.wisdom):2d}    Intelligence: {int(ms.intelligence):2d}",
            f"   Agility:      {int(ms.agility):2d}    Dexterity:    {int(ms.dexterity):2d}",
            f"   Luck:         {int(ms.luck):2d}"
        ]
        self._draw_bordered_panel(
            content_lines=main_stats_lines_for_helper,
            panel_width=panel_w, border_color=border_col,
            print_top_border=False, print_bottom_border=False
        )
        print(f"{border_col}{BC['ML']}{BC['H'] * (panel_w - 2)}{BC['MR']}{Colors.RESET}")

        # --- Secondary Stats Section ---
        ss = player.secondary_stats
        secondary_stats_lines_for_helper = [
            f" {Colors.BRIGHT_CYAN}Secondary Stats:{Colors.RESET}",
            f"   Max HP:       {int(ss.max_hp):3d}    Max MP:       {int(ss.max_mp):3d}",
            f"   Attack:       {ss.attack:3.1f}    Defense:      {ss.defense:3.1f}",
            f"   M.Attack:     {int(ss.m_attack):3d}    M.Defense:    {int(ss.m_defense):3d}",
            f"   Rest.Magic:   {int(ss.restorative_magic):3d}",
            f"   Crit Rate:    {ss.crit_rate:5.1f}%  Dodge Rate:   {ss.dodge:5.1f}%",
            f"   Discovery:    {ss.discovery:5.1f}%"
        ]
        self._draw_bordered_panel(
            content_lines=secondary_stats_lines_for_helper,
            panel_width=panel_w, border_color=border_col,
            print_top_border=False, print_bottom_border=True
        )
            
    def show_player_status(self, player: Player):
        """Display current player status"""
        BC = self.BOX_CHARS
        panel_w = self.width
        border_col = Colors.CYAN
        
        status_title_text = f"{player.name} - Level {player.level} {player.gender}"
        centered_status_title = status_title_text.center(panel_w - 4)
        title_line_for_helper = (
            f"{Colors.YELLOW}{Colors.BOLD}{centered_status_title}{Colors.RESET}"
        )

        self._draw_bordered_panel(
            content_lines=[title_line_for_helper],
            panel_width=panel_w, border_color=border_col,
            print_top_border=True, print_bottom_border=False
        )
        print(f"{border_col}{BC['ML']}{BC['H'] * (panel_w - 2)}{BC['MR']}{Colors.RESET}")
        
        content_lines_for_helper = []
        # Health and Mana bars
        hp_bar = self.create_bar(player.current_hp, player.secondary_stats.max_hp, 20, "❤️")
        mp_bar = self.create_bar(player.current_mp, player.secondary_stats.max_mp, 20, "💙")
        
        # Original: f"  HP: {hp_bar} {player.current_hp}/{player.secondary_stats.max_hp}"
        # Helper adds one space, so content for helper: f" HP: ..."
        content_lines_for_helper.append(f" HP: {hp_bar} {player.current_hp}/{player.secondary_stats.max_hp}")
        content_lines_for_helper.append(f" MP: {mp_bar} {player.current_mp}/{player.secondary_stats.max_mp}")
        
        # Experience
        if player.level < 100:  # Max level cap
            exp_bar = self.create_bar(player.experience, player.experience_to_next, 20, "⭐")
            content_lines_for_helper.append(f" EXP: {exp_bar} {player.experience}/{player.experience_to_next}")
        else:
            content_lines_for_helper.append(f" EXP: MAX LEVEL")
            
        # Status effects
        if player.status_effects:
            effects = ", ".join(player.get_status_effect_names())
            content_lines_for_helper.append(f" Status: {effects}")
            
        self._draw_bordered_panel(
            content_lines=content_lines_for_helper,
            panel_width=panel_w, border_color=border_col,
            print_top_border=False, print_bottom_border=True
        )
            
    def create_bar(self, current: int, maximum: int, length: int, symbol: str = "█") -> str:
        """Create a visual progress bar"""
        if maximum == 0:
            return "█" * length
            
        filled = int((current / maximum) * length)
        empty = length - filled
        
        return f"[{'█' * filled}{'░' * empty}]"
        
    def show_combat_status(self, player: Player, enemies: List[Any]):
        """Display combat status"""
        BC = self.BOX_CHARS
        panel_w = self.width
        border_col = Colors.BRIGHT_CYAN # Original used BRIGHT_CYAN for borders

        # --- Title Section ---
        centered_combat_title = 'COMBAT STATUS'.center(panel_w - 4)
        title_text = (
            f"{Colors.BRIGHT_RED}{Colors.BOLD}{centered_combat_title}{Colors.RESET}"
        )
        self._draw_bordered_panel(
            content_lines=[title_text],
            panel_width=panel_w, border_color=border_col,
            print_top_border=True, print_bottom_border=False
        )
        print(f"{border_col}{BC['ML']}{BC['H'] * (panel_w - 2)}{BC['MR']}{Colors.RESET}")

        # --- Player Status Section ---
        player_section_lines = []
        hp_bar = self.create_bar(player.current_hp, player.secondary_stats.max_hp, 15)
        mp_bar = self.create_bar(player.current_mp, player.secondary_stats.max_mp, 15)
        
        # Original: f"  {Colors.BRIGHT_GREEN}{player.name}:{Colors.RESET}..."
        player_section_lines.append(f" {Colors.BRIGHT_GREEN}{player.name}:{Colors.RESET}")
        # Original: f"    HP: {hp_bar}..."
        player_section_lines.append(f"   HP: {hp_bar} {player.current_hp}/{player.secondary_stats.max_hp}")
        player_section_lines.append(f"   MP: {mp_bar} {player.current_mp}/{player.secondary_stats.max_mp}")
        
        if player.status_effects:
            effects = ", ".join(player.get_status_effect_names())
            player_section_lines.append(f"   Status: {effects}")
            
        self._draw_bordered_panel(
            content_lines=player_section_lines,
            panel_width=panel_w, border_color=border_col,
            print_top_border=False, print_bottom_border=False
        )
        print(f"{border_col}{BC['ML']}{BC['H'] * (panel_w - 2)}{BC['MR']}{Colors.RESET}")

        # --- Enemies Section ---
        enemy_section_lines = []
        # Original: f"  {Colors.BRIGHT_RED}Enemies:{Colors.RESET}..."
        enemy_section_lines.append(f" {Colors.BRIGHT_RED}Enemies:{Colors.RESET}")
        
        for i, enemy in enumerate(enemies):
            if hasattr(enemy, 'current_hp') and hasattr(enemy, 'max_hp'):
                enemy_hp_bar = self.create_bar(enemy.current_hp, enemy.max_hp, 15)
                # Original: f"    {i+1}. {enemy.name}: ..."
                enemy_section_lines.append(f"   {i+1}. {enemy.name}: {enemy_hp_bar} {enemy.current_hp}/{enemy.max_hp}")
                
                if hasattr(enemy, 'status_effects') and enemy.status_effects:
                    effects = ", ".join([effect.get('name', 'Unknown') for effect in enemy.status_effects])
                    # Original: f"       Status: {effects}"
                    enemy_section_lines.append(f"      Status: {effects}") # Note: 6 spaces for helper
            else:
                enemy_section_lines.append(f"   {i+1}. {enemy.name}")
                
        self._draw_bordered_panel(
            content_lines=enemy_section_lines,
            panel_width=panel_w, border_color=border_col,
            print_top_border=False, print_bottom_border=True
        )
                
    def show_combat_menu(self) -> str:
        """Show combat action menu using predefined options."""
        return self.show_menu("Combat Actions", self.COMBAT_MENU_OPTIONS)
        
    def show_target_selection(self, enemies: List[Any]) -> int:
        """Show enemy target selection"""
        BC = self.BOX_CHARS
        centered_target_title = 'Select Target:'.center(self.width - 4)
        title_line_content = (
            f"{Colors.YELLOW}{Colors.BOLD}{centered_target_title}{Colors.RESET}"
        )

        self._draw_bordered_panel(
            content_lines=[title_line_content],
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_bottom_border=False
        )

        print(f"{Colors.CYAN}{BC['ML']}{BC['H'] * (self.width - 2)}{BC['MR']}{Colors.RESET}")

        enemy_lines_for_helper = []
        for i, enemy in enumerate(enemies):
            base_text = ""
            if hasattr(enemy, 'current_hp') and hasattr(enemy, 'max_hp'):
                status = "ALIVE" if enemy.current_hp > 0 else "DEAD"
                base_text = f"{i+1}. {enemy.name} ({status})"
            else:
                base_text = f"{i+1}. {enemy.name}"
            
            # Original content started with "  " (e.g. f"  {i+1}. {enemy.name}...")
            # Helper adds one space, so content for helper should start with one space.
            line_for_helper = f" {base_text}"
            enemy_lines_for_helper.append(line_for_helper)
            
        self._draw_bordered_panel(
            content_lines=enemy_lines_for_helper,
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_top_border=False,
            print_bottom_border=True
        )
        
        num_targets = len(enemies)
        if num_targets == 0:
            self.show_message("No targets available to select.")
            return -1 # Indicate no valid choice or error

        input_prompt = "Select target (number): "
        
        # allow_cancel_keyword can be set to True if exiting target selection via keyword is desired.
        # For now, False to match original behavior (must select a target).
        choice_1_indexed = self._get_validated_numeric_input(
            prompt=input_prompt,
            min_val=1,
            max_val=num_targets,
            allow_cancel_keyword=False
        )

        if choice_1_indexed is not None: # Should always be not None if allow_cancel_keyword is False
            return choice_1_indexed - 1  # Convert to 0-indexed for list access
        else:
            # This case implies cancellation, which is not enabled here.
            # If it were, this would be the place to handle it, e.g., return a specific sentinel.
            self.show_error("Target selection was cancelled or failed unexpectedly.") # Should not happen with current settings
            return -1
                
    def show_inventory_summary(self, inventory: Dict[str, int]):
        """Show a summary of inventory contents"""
        if not inventory:
            print("  Inventory is empty.") # Keep original behavior for empty inventory
            return
            
        BC = self.BOX_CHARS
        centered_inv_summary_title = 'Inventory Summary'.center(self.width - 4)
        title_line_content = (
            f"{Colors.YELLOW}{Colors.BOLD}{centered_inv_summary_title}{Colors.RESET}"
        )

        self._draw_bordered_panel(
            content_lines=[title_line_content],
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_bottom_border=False
        )
        
        print(f"{Colors.CYAN}{BC['ML']}{BC['H'] * (self.width - 2)}{BC['MR']}{Colors.RESET}")
        
        item_lines_for_helper = []
        for item_name, quantity in sorted(inventory.items()):
            raw_item_display = ""
            if "Introduction to " in item_name:
                raw_item_display = f"{Colors.BRIGHT_GREEN}{item_name}{Colors.RESET}: {quantity}"
            else:
                raw_item_display = f"{item_name}: {quantity}"
            
            # Original item_text started with "  " (e.g. f"  {item_name}...")
            # Helper adds one space, so content for helper should start with one space.
            line_for_helper = f" {raw_item_display}"
            item_lines_for_helper.append(line_for_helper)
            
        self._draw_bordered_panel(
            content_lines=item_lines_for_helper,
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_top_border=False,
            print_bottom_border=True
        )
            
    def show_item_selection(self, items: Dict[str, int]) -> Optional[str]:
        """Show item selection menu"""
        if not items:
            self.show_message("No items available!")
            return None
            
        item_list = list(items.keys())
        options = []
        for i, item in enumerate(item_list):
            # Check if item is an introduction book (should be rare/green)
            if "Introduction to " in item:
                # Use green color for introduction books
                options.append(f"{i+1}. {Colors.BRIGHT_GREEN}{item}{Colors.RESET} ({items[item]})")
            else:
                options.append(f"{i+1}. {item} ({items[item]})")
        options.append(f"{len(item_list)+1}. Cancel")
        
        choice_1_indexed = self.show_menu("Select Item", options) # show_menu now returns Optional[int]
        
        if choice_1_indexed is not None:
            if 1 <= choice_1_indexed <= len(item_list):
                return item_list[choice_1_indexed - 1] # Valid item choice
            elif choice_1_indexed == len(item_list) + 1: # "Cancel" option was chosen
                return None
            # else: Should not happen if show_menu returns a valid choice within its options range
        
        # If choice_1_indexed is None (e.g. show_menu failed, or if it could be cancelled internally)
        # or if the number doesn't match an item or cancel (should be caught by show_menu's validation)
        return None # Default to None if no valid item selected or cancelled
        
    def show_damage_message(self, attacker: str, target: str, damage: int, is_crit: bool = False):
        """Show damage dealt message"""
        crit_text = " (CRITICAL!)" if is_crit else ""
        print(f"  💥 {attacker} deals {damage} damage to {target}{crit_text}")
        
    def show_heal_message(self, target: str, amount: int):
        """Show healing message"""
        print(f"  💚 {target} recovers {amount} HP")
        
    def show_miss_message(self, attacker: str, target: str):
        """Show miss message"""
        print(f"  💨 {attacker}'s attack misses {target}")
        
    def show_dodge_message(self, target: str):
        """Show dodge message"""
        print(f"  🏃 {target} dodges the attack!")
        
    def show_status_effect_message(self, target: str, effect: str, applied: bool = True):
        """Show status effect message"""
        action = "is affected by" if applied else "recovers from"
        print(f"  🌟 {target} {action} {effect}")
        
    def show_level_up_message(self, player: Player):
        """Show level up message"""
        title_text = f"🎉 LEVEL UP! 🎉"
        content_lines = [
            f"{Colors.BRIGHT_YELLOW}{player.name} is now level {player.level}!{Colors.RESET}",
            f"{Colors.BRIGHT_GREEN}You gained 2 stat points to allocate!{Colors.RESET}"
        ]
        # Centering content lines manually to match original output
        centered_content_lines = []
        content_display_width = self.width - 4 # Matches original logic: self.width - 4 for center()
        for line in content_lines:
            visible_len = self.get_visible_length(line)
            padding = (content_display_width - visible_len) // 2
            left_padding = ' ' * padding
            right_padding = ' ' * (content_display_width - visible_len - padding)
            centered_content_lines.append(f"{left_padding}{line}{right_padding}")

        self._draw_bordered_panel(
            content_lines=centered_content_lines,
            title=title_text, # Title is part of the border now
            panel_width=self.width,
            border_color=Colors.BRIGHT_CYAN,
            title_color=Colors.BRIGHT_YELLOW # Default title color, but level up text was in content
        )
        # The original had the "LEVEL UP!" part in the title, and the player name in the first content line.
        # Let's adjust to match that more closely.
        # The helper puts the title in the border. The original had "LEVEL UP! ..." as a content line.
        # To preserve visual:
        # No title in _draw_bordered_panel, make level_up_text the first content line.

        level_up_msg = f'🎉 LEVEL UP! {player.name} is now level {player.level}! 🎉'
        centered_level_up_msg = level_up_msg.center(self.width - 4)
        level_up_text_line = (
            f"{Colors.BRIGHT_YELLOW}{centered_level_up_msg}{Colors.RESET}"
        )

        stats_msg = 'You gained 2 stat points to allocate!'
        centered_stats_msg = stats_msg.center(self.width - 4)
        stats_text_line = (
            f"{Colors.BRIGHT_GREEN}{centered_stats_msg}{Colors.RESET}"
        )
        
        self._draw_bordered_panel(
            content_lines=[level_up_text_line, stats_text_line],
            panel_width=self.width,
            border_color=Colors.BRIGHT_CYAN
        )

    def show_victory_message(self, exp_gained: int):
        """Show victory message"""
        victory_msg = '🏆 VICTORY! 🏆'.center(self.width - 4)
        victory_text_line = f"{Colors.BRIGHT_GREEN}{victory_msg}{Colors.RESET}"

        exp_msg = f'You gained {exp_gained} experience points!'.center(self.width - 4)
        exp_text_line = f"{Colors.BRIGHT_YELLOW}{exp_msg}{Colors.RESET}"
        
        self._draw_bordered_panel(
            content_lines=[victory_text_line, exp_text_line],
            panel_width=self.width,
            border_color=Colors.BRIGHT_CYAN
        )
        
    def show_defeat_message(self):
        """Show defeat message"""
        defeat_msg = '💀 DEFEAT 💀'.center(self.width - 4)
        defeat_text_line = f"{Colors.BRIGHT_RED}{defeat_msg}{Colors.RESET}"

        message_msg = 'You have been defeated...'.center(self.width - 4)
        message_text_line = f"{Colors.RED}{message_msg}{Colors.RESET}"

        self._draw_bordered_panel(
            content_lines=[defeat_text_line, message_text_line],
            panel_width=self.width,
            border_color=Colors.BRIGHT_CYAN
        )
        
    def show_loot_message(self, loot: Dict[str, int]):
        """Show loot obtained"""
        if not loot:
            return

        BC = self.BOX_CHARS
        centered_loot_title = 'Loot Obtained:'.center(self.width - 4)
        title_line_content = (
            f"{Colors.YELLOW}{Colors.BOLD}{centered_loot_title}{Colors.RESET}"
        )
        
        self._draw_bordered_panel(
            content_lines=[title_line_content],
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_bottom_border=False
        )
        
        print(f"{Colors.CYAN}{BC['ML']}{BC['H'] * (self.width - 2)}{BC['MR']}{Colors.RESET}")
        
        loot_item_lines = []
        for item, quantity in loot.items():
            # Original content was "  📦 {item} x{quantity}"
            # Helper adds one space, so content for helper should start with one space.
            line_for_helper = f" 📦 {item} x{quantity}"
            loot_item_lines.append(line_for_helper)
            
        self._draw_bordered_panel(
            content_lines=loot_item_lines,
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_top_border=False,
            print_bottom_border=True
        )
            
    def show_zone_info(self, zone_name: str, description: str = ""):
        """Show zone information"""
        BC = self.BOX_CHARS
        centered_zone_name = zone_name.center(self.width - 4)
        title_line_content = (
            f"{Colors.YELLOW}{Colors.BOLD}{centered_zone_name}{Colors.RESET}"
        )

        self._draw_bordered_panel(
            content_lines=[title_line_content],
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_bottom_border=False
        )

        print(f"{Colors.CYAN}{BC['ML']}{BC['H'] * (self.width - 2)}{BC['MR']}{Colors.RESET}")

        desc_lines_for_helper = []
        if description:
            # Original content was "  {description}"
            # Helper adds one space, so content for helper should start with one space.
            line_for_helper = f" {description}"
            desc_lines_for_helper.append(line_for_helper)
        # If description is empty, desc_lines_for_helper remains empty.
        # The helper will correctly print an empty content section if print_top_border=False.
            
        self._draw_bordered_panel(
            content_lines=desc_lines_for_helper,
            panel_width=self.width,
            border_color=Colors.CYAN,
            print_top_border=False,
            print_bottom_border=True
        )
            
    def show_gathering_result(self, resources: Dict[str, int]):
        """Show resource gathering results"""
        BC = self.BOX_CHARS
        
        if not resources:
            no_resources_text_content = "🔍 You search the area but find nothing useful..."
            # Helper adds one space before content. Original had one space.
            self._draw_bordered_panel(
                content_lines=[no_resources_text_content], # Pass raw text
                panel_width=self.width,
                border_color=Colors.CYAN,
                print_top_border=True, # Full box for this message
                print_bottom_border=True
            )
        else:
            title_text_content = f"{Colors.BRIGHT_GREEN}🌿 You gather some resources:{Colors.RESET}"
            # Helper adds one space before content. Original had one space.
            self._draw_bordered_panel(
                content_lines=[title_text_content], # Pass raw text
                panel_width=self.width,
                border_color=Colors.CYAN,
                print_bottom_border=False # Middle of a larger structure
            )

            print(f"{Colors.CYAN}{BC['ML']}{BC['H'] * (self.width - 2)}{BC['MR']}{Colors.RESET}")

            resource_item_lines = []
            for resource, amount in resources.items():
                # Original content was "  {resource} x{amount}"
                # Helper adds one space, so content for helper should start with one space.
                line_for_helper = f" {resource} x{amount}"
                resource_item_lines.append(line_for_helper)
            
            self._draw_bordered_panel(
                content_lines=resource_item_lines,
                panel_width=self.width,
                border_color=Colors.CYAN,
                print_top_border=False, # Continuing the structure
                print_bottom_border=True # End of the structure
            )
            
    def show_cave_home_art(self):
        """Display the cave home ASCII art"""
        if self.cave_home_art_content:
            print(f"{Colors.BROWN}{self.cave_home_art_content}{Colors.RESET}")
        
    def show_crafting_art(self):
        """Display the crafting ASCII art"""
        if self.crafting_art_content:
            print(f"{Colors.BRIGHT_CYAN}{self.crafting_art_content}{Colors.RESET}")
    
    def show_storage_art(self):
        """Display the storage ASCII art"""
        if self.storage_art_content:
            print(f"{Colors.BRIGHT_CYAN}{self.storage_art_content}{Colors.RESET}")
            
    def format_locked_option(self, text: str) -> str:
        """Format a menu option as locked/disabled with strikethrough"""
        return f"{Colors.BRIGHT_BLACK}{Colors.STRIKE}{text}{Colors.RESET}"
        
    def show_progress_bar(self, current: int, total: int, description: str = "Progress"):
        """Show a progress bar for long operations"""
        bar_length = 30
        progress = current / total if total > 0 else 0
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        percentage = int(progress * 100)
        
        progress_line = (
            f"\r  {description}: [{bar}] {percentage}% ({current}/{total})"
        )
        print(progress_line, end="", flush=True)
        
        if current >= total:
            print()  # New line when complete
            
    def check_for_esc(self) -> bool:
        """
        Check if ESC key is pressed.
        Returns False if msvcrt is not available (e.g., on non-Windows).
        """
        if MSVCRT_AVAILABLE:
            # Windows-specific single-key press detection
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC key
                    return True
            return False
        else:
            # Fallback for non-Windows or if msvcrt is unavailable
            # Cannot reliably check for ESC without msvcrt in this context
            return False
        
    def show_zone_art(self, zone_name: str):
        """Display ASCII art for a specific zone."""
        art_content = self.zone_art_map.get(zone_name)
        color = Colors.RESET # Default color

        if zone_name == "Shapira Plains":
            color = Colors.GREEN
        elif zone_name == "Cave Home":
            color = Colors.BROWN
        elif zone_name == "Goblin Camp":
            color = Colors.BRIGHT_RED
        elif zone_name == "Central Shapira Forest":
            color = Colors.GREEN
        elif zone_name == "West Shapira Mountains":
            color = Colors.BRIGHT_WHITE
        elif zone_name == "Dungeon Goblin Fortress":
            color = Colors.BRIGHT_BLACK
        elif zone_name == "Volcanic Zone":
            color = Colors.BRIGHT_RED
        elif zone_name == "Ice Continent":
            color = Colors.BRIGHT_CYAN
        elif zone_name == "Dungeon Wahsh Den":
            color = Colors.BRIGHT_RED
        
        if art_content:
            print(f"{color}{art_content}{Colors.RESET}")
        else:
            # Use default art if specific art is not found
            print(f"{Colors.CYAN}{self.default_zone_art_content.format(zone_name=zone_name)}{Colors.RESET}")

    def display_header(self, header_text: str):
        """
        Displays a prominent header, typically at the top of a new screen or section.
        Uses a bordered panel with the header text in the top border.
        """
        self._draw_bordered_panel(
            content_lines=[],
            panel_title_in_border=header_text,
            panel_width=self.width,
            border_color=Colors.CYAN,
            title_color=Colors.YELLOW + Colors.BOLD,
            print_top_border=True,
            print_bottom_border=True
        )
        # print() # Add a blank line after the header for spacing - Removed, _draw_bordered_panel handles spacing.
 
    def show_message(self, message: str, color: str = Colors.WHITE):
        """Display a generic message to the user."""
        print(f"  {color}{message}{Colors.RESET}")

    def show_error(self, message: str):
        """Display an error message."""
        print(f"  {Colors.RED}Error: {message}{Colors.RESET}")
        
    def show_success(self, message: str):
        """Display a success message."""
        print(f"  {Colors.GREEN}Success: {message}{Colors.RESET}")

    def show_menu(self, title: str, options: List[str], prompt: str = "Enter your choice: ") -> Optional[int]:
        """
        Displays a menu and gets a validated 1-indexed numeric choice from the user.
        Returns the 1-indexed choice, or None if menu display/input fails (e.g., no options).
        """
        border_top = f"{Colors.CYAN}╔{'═' * (self.width - 2)}╗{Colors.RESET}"
        border_bottom = f"{Colors.CYAN}╚{'═' * (self.width - 2)}╝{Colors.RESET}"
        border_side = f"{Colors.CYAN}║{Colors.RESET}"
        border_middle = f"{Colors.CYAN}╠{'═' * (self.width - 2)}╣{Colors.RESET}"

        print(f"\n{border_top}")
        centered_title = title.center(self.width - 4)
        title_line = (
            f"{border_side} {Colors.YELLOW}{Colors.BOLD}{centered_title}{Colors.RESET} "
            f"{border_side}"
        )
        print(title_line)
        print(f"{border_middle}")

        if not options:
            # This case should ideally be prevented by callers.
            # Print an empty content line if there are no options.
            empty_content_display_width = self.width - 4
            if empty_content_display_width < 0: empty_content_display_width = 0
            empty_line = f"{border_side}{' ' * empty_content_display_width}{border_side}"
            print(empty_line)
            print(f"{border_bottom}")
            self.show_error("Cannot display a menu with no options.")
            return None

        for option in options:
            visible_length = self.get_visible_length(option)
            # Padding: self.width (total) - 2 (for borders ║ ║) - 2 (for spaces around content "  ")
            # Content area width is self.width - 4
            # Padding is (content_area_width - visible_length_of_option_text)
            padding_needed = (self.width - 4) - visible_length
            if padding_needed < 0: padding_needed = 0
            padding = ' ' * padding_needed
            print(f"{border_side}  {option}{padding}{border_side}")
        
        print(f"{border_bottom}")
        
        num_menu_options = len(options)
        # For show_menu, cancellation is typically handled by a numbered "Cancel" option.
        # So, allow_cancel_keyword and allow_empty_to_cancel are False.
        return self._get_validated_numeric_input(
            prompt=prompt,
            min_val=1,
            max_val=num_menu_options,
            allow_cancel_keyword=False,
            allow_empty_to_cancel=False
        )

    def display_menu_for_string_input(self, title: str, options: List[str], prompt: str = "Enter your choice: ") -> str:
        """
        Displays a menu and gets raw string input from the user.
        Similar to show_menu but for free-form string input.
        Returns the raw string input. ESC key press is not specially handled here,
        it would be part of the raw string if not caught by a global handler.
        """
        border_top = f"{Colors.CYAN}╔{'═' * (self.width - 2)}╗{Colors.RESET}"
        border_bottom = f"{Colors.CYAN}╚{'═' * (self.width - 2)}╝{Colors.RESET}"
        border_side = f"{Colors.CYAN}║{Colors.RESET}"
        border_middle = f"{Colors.CYAN}╠{'═' * (self.width - 2)}╣{Colors.RESET}"

        print(f"\n{border_top}")
        centered_title = title.center(self.width - 4)
        title_line = (
            f"{border_side} {Colors.YELLOW}{Colors.BOLD}{centered_title}{Colors.RESET} "
            f"{border_side}"
        )
        print(title_line)
        print(f"{border_middle}")

        if not options:
            empty_content_display_width = self.width - 4
            if empty_content_display_width < 0: empty_content_display_width = 0
            empty_line = f"{border_side}{' ' * empty_content_display_width}{border_side}"
            print(empty_line)
            # No error message here, just display empty menu part
        else:
            for option in options:
                visible_length = self.get_visible_length(option)
                padding_needed = (self.width - 4) - visible_length
                if padding_needed < 0: padding_needed = 0
                padding = ' ' * padding_needed
                print(f"{border_side}  {option}{padding}{border_side}")
        
        print(f"{border_bottom}")
        
        return self.get_input(prompt) # Use get_input for raw string

    def _draw_bordered_panel(self,
                             content_lines: List[str],
                             panel_title_in_border: Optional[str] = None,
                             panel_width: Optional[int] = None,
                             border_color: str = Colors.CYAN,
                             title_color: str = Colors.YELLOW + Colors.BOLD,
                             print_top_border: bool = True,
                             print_bottom_border: bool = True
                            ) -> None:
        """
        Draws a bordered panel around the provided content lines.
        The panel_title_in_border, if provided, appears in the top border like: ╔═ Title ═══╗
        Content lines are left-aligned and padded within the panel.
        Can optionally omit printing top and/or bottom borders.
        """
        BC = self.BOX_CHARS
        effective_width = panel_width if panel_width is not None else self.width

        # Ensure minimum width for aesthetics
        min_width_for_title = (self.get_visible_length(panel_title_in_border) + 4) if panel_title_in_border else 0
        min_width_for_content = 4 # For ║  ║
        
        if effective_width < min_width_for_content and content_lines:
            effective_width = min_width_for_content
        if panel_title_in_border and effective_width < min_width_for_title:
             effective_width = min_width_for_title
        if effective_width < 2: # Absolute minimum for ╔╗ or ║║
            effective_width = 2

        # Top border
        if print_top_border:
            top_border_str = ""
            if panel_title_in_border:
                title_text_colored = f"{title_color}{panel_title_in_border}{Colors.RESET}"
                title_visible_len = self.get_visible_length(panel_title_in_border)
                space_for_title_segment = title_visible_len + 2
                num_H_total = effective_width - 2 - space_for_title_segment
                if num_H_total < 0:
                    num_H_total = 0
                h_left = num_H_total // 2
                h_right = num_H_total - h_left
                
                left_border_part = f"{border_color}{BC['TL']}{BC['H'] * h_left}"
                title_part = f" {title_text_colored}{border_color} "
                right_border_part = f"{BC['H'] * h_right}{BC['TR']}{Colors.RESET}"
                top_border_str = f"{left_border_part}{title_part}{right_border_part}"
            else: # No title in border
                top_border_str = (
                    f"{border_color}{BC['TL']}"
                    f"{BC['H'] * (effective_width - 2)}"
                    f"{BC['TR']}{Colors.RESET}"
                )
            print(f"\n{top_border_str}")

        # Content lines
        # Width available for text content itself (between "║ " and " ║"):
        content_display_width = effective_width - 4
        if content_display_width < 0: content_display_width = 0

        if content_lines:
            for line_text in content_lines:
                current_visible_len = self.get_visible_length(line_text)
                padding_str = ""
                text_segment_to_display = line_text
                
                if current_visible_len < content_display_width:
                    padding_str = ' ' * (content_display_width - current_visible_len)
                # else: # Content is longer or equal to display width, no padding needed.
                      # Truncation logic removed for now to match original behavior of letting lines overflow
                      # or relying on caller to pre-format lines to fit.
                    pass
                
                left_v_border = f"{border_color}{BC['V']}{Colors.RESET}"
                right_v_border = f" {border_color}{BC['V']}{Colors.RESET}"
                content_panel_line = (
                    f"{left_v_border} {text_segment_to_display}"
                    f"{padding_str}{right_v_border}"
                )
                print(content_panel_line)
        elif print_top_border and print_bottom_border and effective_width >=2: # Only print empty line if it's a full box
            # If no content lines, but it's meant to be an empty box, print one empty content line.
            # This ensures ╔══╗
            #             ║  ║
            #             ╚══╝
            # instead of just ╔══╗╚══╝ if content_lines is empty.
            # However, this might not be desired if used for partial drawing.
            # Let's only do this if it's a "full" box being drawn.
            # If content_lines is empty, and we are drawing top and bottom, print an empty line.
            # This is only relevant if content_lines is truly empty. If it's `[""]`, one blank line is printed.
            if not content_lines: # Explicitly check for empty list
                empty_content_line = (
                    f"{border_color}{BC['V']}{' ' * content_display_width}"
                    f"{BC['V']}{Colors.RESET}"
                )
                print(empty_content_line)
        # elif effective_width >= 2: # Original logic for empty content
        #      pass


        # Bottom border
        if print_bottom_border:
            bottom_border_str = (
                f"{border_color}{BC['BL']}"
                f"{BC['H'] * (effective_width - 2)}"
                f"{BC['BR']}{Colors.RESET}"
            )
            print(bottom_border_str)
 
    def get_visible_length(self, text: str) -> int:
        """Calculate the visible length of a string, ignoring ANSI escape codes."""
        import re
        # Regex to remove ANSI escape codes
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        return len(ansi_escape.sub('', text))
 
    def display_character_creation(self):
        """Guides the player through character creation."""
        self.clear_screen()
        self.show_title()
        print(f"\n{Colors.BRIGHT_YELLOW}Welcome, brave adventurer, to the world of Eldoria!{Colors.RESET}")
        print("Before you embark on your journey, let's create your character.\n")

        name = ""
        while not name:
            name = self.get_input("Enter your character's name: ")
            if not name.strip():
                self.show_error("Name cannot be empty.")
                name = ""
            elif len(name) > 15:
                self.show_error("Name is too long (max 15 characters).")
                name = ""
            elif not name.isalpha(): # Basic check, can be more complex
                self.show_error("Name should only contain letters.")
                name = ""


        gender = ""
        gender_options = ["1. Male", "2. Female"]
        gender_choice_num = self.show_menu("Choose your gender:", gender_options, "Enter choice (1 or 2): ")

        if gender_choice_num == 1:
            gender = "male"
        elif gender_choice_num == 2:
            gender = "female"
        # else: show_menu now ensures a valid choice (1 or 2) or would have looped.
        # If gender_choice_num could be None (e.g. if show_menu failed), add handling.
        # For now, assume show_menu returns a valid int if options are provided.
        
        print(f"\n{Colors.BRIGHT_GREEN}Character {name} ({gender}) created!{Colors.RESET}")
        self.wait_for_input()
        return name, gender

    def display_game_over(self):
        """Displays the game over screen."""
        self.clear_screen()
        game_over_art = f"""
{Colors.RED}
 ██████╗  █████╗ ███╗   ███╗███████╗    ██████╗ ██╗   ██╗███████╗██████╗ 
██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔══██╗██║   ██║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗      ██║  ██║██║   ██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║  ██║██║   ██║██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ██████╔╝╚██████╔╝███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
{Colors.RESET}
"""
        print(game_over_art)
        self.show_message("Your journey ends here... but perhaps another will begin?", Colors.BRIGHT_YELLOW)
        self.wait_for_input("Press Enter to return to the main menu...")

    def display_main_menu(self) -> str:
        """Displays the main menu and returns the user's choice."""
        self.clear_screen()
        self.show_title()
        # show_menu now returns Optional[int]. The caller needs to map this int to an action.
        # For simplicity, this example assumes the game loop handles the int.
        # If the return type of display_main_menu needs to be str (e.g. "1", "2"),
        # then convert the int back to str here.
        choice_num = self.show_menu("Main Menu", self.MAIN_MENU_OPTIONS, "Choose an option: ")
        return str(choice_num) if choice_num is not None else "" # Or handle None appropriately

    def display_gameplay_menu(self, player: Player, current_zone: str) -> Optional[int]: # Return type changed
        """Displays the main gameplay menu."""
        self.clear_screen()
        self.show_player_status(player)
        self.show_zone_info(current_zone)
        
        return self.show_menu("What would you like to do?", self.GAMEPLAY_MENU_OPTIONS)

    def display_exploration_options(self) -> Optional[int]: # Return type changed
        """Displays options available during exploration."""
        return self.show_menu("Exploration Actions", self.EXPLORATION_OPTIONS)

    def display_inventory_menu(self, player: Player) -> Optional[int]: # Return type changed
        """Displays inventory options."""
        self.clear_screen()
        self.show_inventory_summary(player.inventory.items)
        return self.show_menu("Inventory", self.INVENTORY_MENU_OPTIONS)

    def display_equipment_slots(self, player: Player) -> Optional[int]: # Return type changed
        """Displays equipment slots for equipping/unequipping items."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}Current Equipment:{Colors.RESET}")
        slots = ["Weapon", "Shield", "Helmet", "Chest", "Legs", "Boots", "Gloves", "Ring1", "Ring2", "Amulet"]
        options = []
        for i, slot in enumerate(slots):
            item_name = player.equipment.get(slot.lower().replace(" ", "_"))
            item_display = item_name if item_name else "Empty"
            options.append(f"{i+1}. {slot}: {item_display}")
        
        options.append(f"{len(slots)+1}. Cancel")
        return self.show_menu("Select Slot", options) # Returns Optional[int]

    def display_items_for_slot(self, items: List[Dict[str, Any]], slot_name: str) -> Optional[Dict[str, Any]]:
        """Displays items suitable for a given slot and returns the chosen item."""
        if not items:
            self.show_message(f"No suitable items for {slot_name}.", Colors.YELLOW)
            self.wait_for_input()
            return None

        options = [f"{i+1}. {item['name']}" for i, item in enumerate(items)]
        options.append(f"{len(items)+1}. Cancel")

        choice_1_indexed = self.show_menu(f"Select item for {slot_name}", options)
        
        if choice_1_indexed is not None:
            choice_0_indexed = choice_1_indexed - 1
            if 0 <= choice_0_indexed < len(items):
                return items[choice_0_indexed]
            elif choice_0_indexed == len(items): # Cancel option
                return None
        return None # choice_1_indexed was None or out of expected range (should be handled by show_menu)

    def display_item_description(self, item_name: str, item_details: Dict[str, Any]):
        """Displays detailed information about an item."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}{item_name}{Colors.RESET}")
        print(self.thin_separator)
        for key, value in item_details.items():
            if key != "name": # Don't repeat the name
                print(f"  {key.replace('_', ' ').title()}: {value}")
        print(self.thin_separator)
        self.wait_for_input()

    def display_crafting_interface(self, player: Player, recipes: List[Dict[str, Any]]):
        """Handles the crafting interface."""
        self.clear_screen()
        self.show_crafting_art()
        print(f"\n{Colors.YELLOW}{Colors.BOLD}--- Crafting Menu ---{Colors.RESET}")
        
        if not recipes:
            self.show_message("You don't know any recipes yet.", Colors.YELLOW)
            self.wait_for_input()
            return

        options = []
        for i, recipe in enumerate(recipes):
            name = recipe.get('name', 'Unknown Recipe')
            materials = recipe.get('materials', {})
            materials_str = ", ".join([f"{qty}x {mat}" for mat, qty in materials.items()])
            
            # Check if player has enough materials
            can_craft = True
            for material, required_qty in materials.items():
                if player.inventory.get_item_quantity(material) < required_qty:
                    can_craft = False
                    break
            
            if can_craft:
                option_text = (
                    f"{i+1}. {Colors.GREEN}{name}{Colors.RESET} "
                    f"(Requires: {materials_str})"
                )
                options.append(option_text)
            else:
                locked_text = (
                    f"{i+1}. {name} (Requires: {materials_str} - "
                    f"Insufficient materials)"
                )
                options.append(self.format_locked_option(locked_text))
        
        options.append(f"{len(recipes)+1}. Back")
        
        choice_1_indexed = self.show_menu("Select a recipe to craft:", options)
        
        if choice_1_indexed is not None:
            choice_0_indexed = choice_1_indexed - 1
            if 0 <= choice_0_indexed < len(recipes):
                 # Check again if can_craft, as show_menu doesn't know about this dynamic state
                selected_recipe = recipes[choice_0_indexed]
                can_craft_selected = True
                for material, required_qty in selected_recipe.get('materials', {}).items():
                    if player.inventory.get_item_quantity(material) < required_qty:
                        can_craft_selected = False
                        break
                if can_craft_selected:
                    return selected_recipe
                else:
                    # This case means user selected a recipe they couldn't craft from the menu.
                    # format_locked_option should make this less likely, but good to be safe.
                    self.show_error("You selected a recipe you cannot craft (insufficient materials).")
                    return None
            elif choice_0_indexed == len(recipes): # "Back" option
                return None
        return None


    def display_storage_menu(self, player_inventory: Dict[str, int], storage_inventory: Dict[str, int]) -> Optional[int]: # Return type changed
        """Displays the storage menu and returns the user's choice."""
        self.clear_screen()
        self.show_storage_art()
        print(f"\n{Colors.YELLOW}{Colors.BOLD}--- Storage ---{Colors.RESET}")

        print(f"\n{Colors.BRIGHT_WHITE}Your Inventory:{Colors.RESET}")
        if player_inventory:
            for item, quantity in player_inventory.items():
                print(f"  - {item}: {quantity}")
        else:
            print("  Your inventory is empty.")

        print(f"\n{Colors.BRIGHT_WHITE}Storage:{Colors.RESET}")
        if storage_inventory:
            for item, quantity in storage_inventory.items():
                print(f"  - {item}: {quantity}")
        else:
            print("  Storage is empty.")
        
        print(self.thin_separator)
        return self.show_menu("Storage Options", self.STORAGE_MENU_OPTIONS)

    def get_item_and_quantity_to_transfer(self, inventory: Dict[str, int], action: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Prompts the user to select an item and quantity for storing or retrieving.
        Args:
            inventory: The inventory to select from (player's or storage's).
            action: "store" or "retrieve".
        Returns:
            A tuple (item_name, quantity) or (None, None) if cancelled or invalid.
        """
        if not inventory:
            self.show_message(f"No items to {action}.", Colors.YELLOW)
            self.wait_for_input()
            return None, None

        item_list = list(inventory.keys())
        options = []
        for i, item in enumerate(item_list):
            option_text = f"{i+1}. {item} (Available: {inventory[item]})"
            options.append(option_text)
        options.append(f"{len(item_list)+1}. Cancel")

        choice_1_indexed = self.show_menu(f"Select item to {action}:", options)

        if choice_1_indexed is not None:
            choice_0_indexed = choice_1_indexed - 1
            if 0 <= choice_0_indexed < len(item_list):
                item_name = item_list[choice_0_indexed]
                max_quantity = inventory[item_name]
                
                qty_prompt = (
                    f"Enter quantity of {item_name} to {action} "
                    f"(max {max_quantity}, or type 'cancel'): " # Adjusted prompt
                )
                # Use _get_validated_numeric_input for quantity
                # Allow empty to cancel to match original behavior of "Enter without typing"
                # Also allow "cancel" keyword for explicit cancellation.
                quantity = self._get_validated_numeric_input(
                    prompt=qty_prompt,
                    min_val=1, # Assuming quantity must be at least 1
                    max_val=max_quantity,
                    allow_cancel_keyword=True,
                    cancel_keyword="cancel",
                    allow_empty_to_cancel=True
                )

                if quantity is not None:
                    return item_name, quantity
                else:
                    return None, None # Cancelled quantity input
            elif choice_0_indexed == len(item_list): # "Cancel" option from item list
                return None, None
        
        return None, None # Item selection failed or was cancelled

    def display_stat_allocation(self, player: Player, points_to_allocate: int) -> Dict[str, int]:
        """Allows the player to allocate stat points."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Allocate Stat Points ---{Colors.RESET}")
        print(f"You have {Colors.BRIGHT_GREEN}{points_to_allocate}{Colors.RESET} points to allocate.\n")

        stats_to_increase = {
            "strength": 0,
            "vitality": 0,
            "wisdom": 0,
            "intelligence": 0,
            "agility": 0,
            "dexterity": 0,
            "luck": 0,
            "speed": 0
        }
        
        stat_names = list(stats_to_increase.keys())
        points_remaining = points_to_allocate

        while points_remaining > 0:
            self.show_player_stats(player) # Show current stats
            print(f"\n{Colors.BRIGHT_WHITE}Points remaining: {points_remaining}{Colors.RESET}")
            
            options = []
            for i, stat_name in enumerate(stat_names):
                current_value = getattr(player.main_stats, stat_name)
                added_value = stats_to_increase[stat_name]
                option_text = (
                    f"{i+1}. {stat_name.capitalize()}: {current_value} "
                    f"(+{added_value})"
                )
                options.append(option_text)
            options.append(f"{len(stat_names)+1}. Done Allocating")

            choice_1_indexed = self.show_menu("Choose a stat to increase:", options)

            if choice_1_indexed is not None:
                choice_0_indexed = choice_1_indexed - 1
                if 0 <= choice_0_indexed < len(stat_names):
                    stat_to_increase = stat_names[choice_0_indexed]
                    stats_to_increase[stat_to_increase] += 1
                    points_remaining -= 1
                    # Temporarily update player stats for display, will be properly updated later
                    setattr(player.main_stats, stat_to_increase, getattr(player.main_stats, stat_to_increase) + 1)
                    self.clear_screen()
                elif choice_0_indexed == len(stat_names): # "Done Allocating" option
                    if points_remaining > 0:
                        if not self.confirm(f"You still have {points_remaining} points unspent. Are you sure you want to finish?"):
                            # To re-show the menu, the outer loop needs to continue
                            # The current structure with show_menu handling re-prompt for its own input
                            # means we don't need `continue` here to re-show the menu.
                            # If confirm is 'no', we just loop again in the `while points_remaining > 0`.
                            pass # Let the outer loop continue
                        else: # Confirmed to finish despite unspent points
                            break # Done allocating
                    else: # No points remaining, and "Done Allocating" chosen
                        break # Done allocating
            # else: choice_1_indexed is None (e.g. show_menu failed - unlikely if options exist)
            # or choice out of range (handled by show_menu). Loop continues.
        
        # Revert temporary stat changes before returning the allocated points
        for stat_name, added_value in stats_to_increase.items():
            setattr(player.main_stats, stat_name, getattr(player.main_stats, stat_name) - added_value)
            
        return stats_to_increase

    def display_shop_menu(self, shop_name: str, items_for_sale: List[Dict[str, Any]], player_gold: int) -> Optional[Dict[str, Any]]:
        """Displays shop inventory and allows player to buy items."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Welcome to {shop_name}! ---{Colors.RESET}")
        print(f"You have {Colors.YELLOW}{player_gold} Gold{Colors.RESET}.\n")

        if not items_for_sale:
            self.show_message("Sorry, we're out of stock right now.", Colors.YELLOW)
            self.wait_for_input()
            return None

        options = []
        for i, item in enumerate(items_for_sale):
            option_text = f"{i+1}. {item['name']} - {item['cost']} Gold"
            options.append(option_text)
        options.append(f"{len(items_for_sale)+1}. Leave Shop")

        choice_1_indexed = self.show_menu("What would you like to buy?", options)

        if choice_1_indexed is not None:
            choice_0_indexed = choice_1_indexed - 1
            if 0 <= choice_0_indexed < len(items_for_sale):
                selected_item = items_for_sale[choice_0_indexed]
                if player_gold >= selected_item['cost']:
                    return selected_item
                else:
                    self.show_error("You don't have enough gold for that item.")
                    self.wait_for_input()
                    return None # Indicate no purchase was made
            elif choice_0_indexed == len(items_for_sale): # "Leave Shop" option
                return None
        return None # choice_1_indexed was None or out of expected range

    def display_sell_menu(self, player_inventory: Dict[str, int], item_values: Dict[str, int]) -> Optional[Tuple[str, int]]:
        """Displays player's inventory for selling items."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Sell Items ---{Colors.RESET}\n")

        if not player_inventory:
            self.show_message("Your inventory is empty. Nothing to sell.", Colors.YELLOW)
            self.wait_for_input()
            return None

        sellable_items = {item: quantity for item, quantity in player_inventory.items() if item in item_values}
        
        if not sellable_items:
            self.show_message("You have no items that can be sold here.", Colors.YELLOW)
            self.wait_for_input()
            return None

        item_list = list(sellable_items.keys())
        options = []
        for i, item_name in enumerate(item_list):
            value = item_values.get(item_name, 0) # Default to 0 if not found
            qty = sellable_items[item_name]
            option_text = (
                f"{i+1}. {item_name} (Qty: {qty}, Value: {value} Gold each)"
            )
            options.append(option_text)
        
        options.append(f"{len(item_list)+1}. Cancel")

        choice_1_indexed = self.show_menu("Select an item to sell:", options)
        
        if choice_1_indexed is not None:
            choice_0_indexed = choice_1_indexed - 1
            if 0 <= choice_0_indexed < len(item_list):
                item_to_sell = item_list[choice_0_indexed]
                max_quantity = sellable_items[item_to_sell]
                
                # Quantity input loop remains custom due to "all" keyword.
                # _get_validated_numeric_input is for purely numeric input or simple keyword/empty cancels.
                while True:
                    try:
                        prompt_text = (
                            f"How many {item_to_sell} do you want to sell? "
                            f"(Available: {max_quantity}, or type 'all', or 'cancel'): " # Added 'cancel'
                        )
                        quantity_str = self.get_input(prompt_text)
                        if quantity_str.lower() == 'all':
                            quantity_to_sell = max_quantity
                            break
                        if quantity_str.lower() == 'cancel': # Explicit cancel for quantity
                            return None # Cancelled selling this item
                            
                        quantity_to_sell = int(quantity_str)
                        if 0 < quantity_to_sell <= max_quantity:
                            break
                        else:
                            self.show_error(f"Invalid quantity. Must be between 1 and {max_quantity}.")
                    except ValueError:
                        self.show_error("Invalid input. Please enter a number, 'all', or 'cancel'.")
                return item_to_sell, quantity_to_sell
                
            elif choice_0_indexed == len(item_list): # "Cancel" option from item list
                return None
        return None

    def display_dialogue(self, character_name: str, lines: List[str], color: str = Colors.WHITE):
        """Displays dialogue from a character."""
        print(f"\n{color}{Colors.BOLD}{character_name}:{Colors.RESET}")
        for line in lines:
            print(f"{color}  \"{line}\"{Colors.RESET}")
        self.wait_for_input()

    def display_quest_info(self, quest_name: str, description: str, objectives: List[str], status: str):
        """Displays information about a quest."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}Quest: {quest_name}{Colors.RESET}")
        print(self.thin_separator)
        print(f"{Colors.BRIGHT_WHITE}Status: {status}{Colors.RESET}")
        print(f"\n{Colors.BRIGHT_WHITE}Description:{Colors.RESET}\n  {description}")
        if objectives:
            print(f"\n{Colors.BRIGHT_WHITE}Objectives:{Colors.RESET}")
            for obj in objectives:
                print(f"  - {obj}")
        print(self.thin_separator)
        self.wait_for_input()

    def display_skill_tree(self, player: Player):
        """Displays the player's skill tree (placeholder)."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Skill Tree ---{Colors.RESET}")
        # This is a placeholder. A real skill tree would be more complex.
        print("  Skill tree feature is not yet fully implemented.")
        print(f"  {player.name} has {player.skill_points} skill points available.")
        # Example: List some skills and their status (learned/available)
        # for skill_name, skill_data in player.skills.items():
        #     status = "Learned" if skill_data.get('learned') else "Available"
        #     print(f"  - {skill_name}: {status}")
        self.wait_for_input()

    def display_help(self):
        """Displays a help screen with game commands or information."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Help ---{Colors.RESET}")
        print(self.thin_separator)
        print("  Welcome to the RPG Adventure!")
        print("  Navigate menus using the numbers corresponding to options.")
        print("  During combat, choose your actions wisely.")
        print("  Explore different zones to find items, enemies, and quests.")
        print("  Manage your inventory and equipment to become stronger.")
        print("  Save your game frequently!")
        print(self.thin_separator)
        self.wait_for_input()

    def display_settings_menu(self) -> str:
        """Displays the settings menu."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Settings ---{Colors.RESET}")
        return self.show_menu("Settings", self.SETTINGS_MENU_OPTIONS) # Returns Optional[int]

    def display_save_load_message(self, message: str, success: bool):
        """Displays a message for save/load operations."""
        color = Colors.BRIGHT_GREEN if success else Colors.BRIGHT_RED
        print(f"  {color}{message}{Colors.RESET}")
        self.wait_for_input()

    def get_save_game_name(self) -> Optional[str]:
        """Prompts the user for a save game name."""
        name = self.get_input("Enter a name for your save game (or leave blank to cancel): ")
        return name if name else None

    def choose_save_slot(self, saves: List[str]) -> Optional[str]:
        """Allows the player to choose a save slot to load or overwrite."""
        if not saves:
            self.show_message("No save files found.", Colors.YELLOW)
            return None
        
        options = [f"{i+1}. {save_name}" for i, save_name in enumerate(saves)]
        options.append(f"{len(saves)+1}. Cancel")
        
        choice_1_indexed = self.show_menu("Select a save slot:", options)
        if choice_1_indexed is not None:
            choice_0_indexed = choice_1_indexed - 1
            if 0 <= choice_0_indexed < len(saves):
                return saves[choice_0_indexed]
            elif choice_0_indexed == len(saves): # Cancel option
                return None
        return None

    def display_character_creation_stats(self, player: Player):
        """Displays character stats during creation for confirmation."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Character Summary ---{Colors.RESET}")
        self.show_player_stats(player) # This will show base stats
        print(f"\n{Colors.BRIGHT_WHITE}Name: {player.name}{Colors.RESET}")
        print(f"{Colors.BRIGHT_WHITE}Gender: {player.gender.capitalize()}{Colors.RESET}")
        print(f"{Colors.BRIGHT_WHITE}Class: {player.player_class.capitalize()}{Colors.RESET}") # Assuming player_class attribute
        print(self.thin_separator)
        return self.confirm("Is this correct?")

    def choose_class(self) -> str:
        """Allows the player to choose a class."""
        self.clear_screen()
        print(f"{Colors.YELLOW}{Colors.BOLD}--- Choose Your Class ---{Colors.RESET}")
        # Use the class constant for options
        numbered_class_options = [f"{i+1}. {cls}" for i, cls in enumerate(self.CLASS_CHOICE_OPTIONS)]
        
        # The while True loop is removed as show_menu now handles re-prompting.
        choice_1_indexed = self.show_menu("Select your class:", numbered_class_options)
        
        if choice_1_indexed is not None:
            # show_menu ensures choice_1_indexed is within 1 to len(numbered_class_options)
            choice_0_indexed = choice_1_indexed - 1
            # Double check, though show_menu should guarantee this range if it returns non-None
            if 0 <= choice_0_indexed < len(self.CLASS_CHOICE_OPTIONS):
                return self.CLASS_CHOICE_OPTIONS[choice_0_indexed]
        
        # Fallback or error if show_menu returns None (e.g., if CLASS_CHOICE_OPTIONS was empty)
        # This path should ideally not be reached if CLASS_CHOICE_OPTIONS is valid.
        self.show_error("Failed to select a class. Please try again.")
        # Could loop here or raise an exception if class selection is critical and failed.
        # For now, returning a default or prompting again might be needed if None is possible.
        # However, with current show_menu, it will loop until valid input if options exist.
        # So, if CLASS_CHOICE_OPTIONS is not empty, choice_1_indexed should not be None.
        # If it could be None, a loop here would be:
        # selected_class = None
        # while selected_class is None:
        #     choice_1_indexed = self.show_menu(...)
        #     if choice_1_indexed is not None:
        #         ...
        #         selected_class = ...
        # return selected_class
        # But this is now handled by show_menu's internal loop.
        # If execution reaches here, it means show_menu returned None when it shouldn't have
        # (e.g. if CLASS_CHOICE_OPTIONS was empty and show_menu handled that by returning None).
        # Assuming CLASS_CHOICE_OPTIONS is always populated.
        # If show_menu could return None for other reasons (e.g. internal error),
        # this function would need to handle that (e.g. default class, re-prompt, error).
        # For now, we assume show_menu returns a valid int.
        # The return type of choose_class is str, so it must return a valid class name.
        # If show_menu could fail to get a choice, this function needs a robust fallback.
        # Given _get_validated_numeric_input loops, show_menu will also loop.
        # So, a None return from show_menu here implies no options were given to it,
        # which is a programming error if CLASS_CHOICE_OPTIONS is empty.
        # If CLASS_CHOICE_OPTIONS is guaranteed non-empty, show_menu returns int.
        # The current code will error if choice_1_indexed is None and tries arithmetic.
        # Let's assume show_menu returns a valid int here.
        if choice_1_indexed is None: # Should not happen if self.CLASS_CHOICE_OPTIONS is not empty
             self.show_error("Critical error in class selection. No options available.")
             return self.CLASS_CHOICE_OPTIONS[0] # Fallback to first class, or raise error

        choice_0_indexed = choice_1_indexed - 1
        return self.CLASS_CHOICE_OPTIONS[choice_0_indexed] # choice_0_indexed is now guaranteed valid