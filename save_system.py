"""
Save and load system for the Python console RPG
Handles game state persistence
"""

import json
import os
from typing import Dict, Any, Optional

SAVE_FILE_NAME = "savegame.json"
SAVE_DIRECTORY = "saves"

class SaveSystem:
    """Handles saving and loading game data"""

    def __init__(self, save_dir: str = SAVE_DIRECTORY, save_file: str = SAVE_FILE_NAME):
        self.save_dir = save_dir
        self.save_file_path = os.path.join(self.save_dir, save_file)
        self._ensure_save_directory_exists()

    def _ensure_save_directory_exists(self):
        """Create the save directory if it doesn't exist"""
        if not os.path.exists(self.save_dir):
            try:
                os.makedirs(self.save_dir)
            except OSError as e:
                # Handle potential race condition or permission issues
                print(f"Error creating save directory {self.save_dir}: {e}")


    def save_game(self, game_data: Dict[str, Any]) -> bool:
        """Save the game data to a file"""
        try:
            with open(self.save_file_path, 'w') as f:
                json.dump(game_data, f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving game to {self.save_file_path}: {e}")
            return False
        except TypeError as e:
            print(f"Error serializing game data: {e}")
            return False

    def load_game(self) -> Optional[Dict[str, Any]]:
        """Load game data from a file"""
        if not os.path.exists(self.save_file_path):
            return None

        try:
            with open(self.save_file_path, 'r') as f:
                game_data = json.load(f)
            return game_data
        except IOError as e:
            print(f"Error loading game from {self.save_file_path}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding save file {self.save_file_path}: {e}")
            return None

    def has_save_file(self) -> bool:
        """Check if a save file exists"""
        return os.path.exists(self.save_file_path)

    def delete_save_file(self) -> bool:
        """Delete the save file"""
        if self.has_save_file():
            try:
                os.remove(self.save_file_path)
                return True
            except OSError as e:
                print(f"Error deleting save file {self.save_file_path}: {e}")
                return False
        return False # No file to delete