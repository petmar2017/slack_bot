"""
Utility module for persistent data storage.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class JsonStorage:
    """
    Simple JSON file-based storage utility.
    """

    def __init__(self, file_path: str, create_if_missing: bool = True):
        """
        Initialize with a file path.
        
        Args:
            file_path: Path to the JSON file
            create_if_missing: Whether to create the file if it doesn't exist
        """
        self.file_path = file_path
        self.create_if_missing = create_if_missing
        
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # Create empty file if it doesn't exist and create_if_missing is True
        if self.create_if_missing and not os.path.exists(file_path):
            self.save({})

    def load(self) -> Dict:
        """
        Load data from the JSON file.
        
        Returns:
            The loaded data, or an empty dict if the file doesn't exist
        """
        if not os.path.exists(self.file_path):
            if self.create_if_missing:
                return {}
            else:
                raise FileNotFoundError(f"Storage file not found: {self.file_path}")
                
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {self.file_path}")
            return {}
        except Exception as e:
            logger.error(f"Error loading data from {self.file_path}: {str(e)}")
            return {}

    def save(self, data: Dict) -> bool:
        """
        Save data to the JSON file.
        
        Args:
            data: Data to save
            
        Returns:
            Whether the save was successful
        """
        try:
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving data to {self.file_path}: {str(e)}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the stored data.
        
        Args:
            key: Key to get
            default: Default value if key not found
            
        Returns:
            The stored value or the default
        """
        data = self.load()
        return data.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the stored data.
        
        Args:
            key: Key to set
            value: Value to store
            
        Returns:
            Whether the operation was successful
        """
        data = self.load()
        data[key] = value
        return self.save(data)

    def delete(self, key: str) -> bool:
        """
        Delete a key from the stored data.
        
        Args:
            key: Key to delete
            
        Returns:
            Whether the operation was successful
        """
        data = self.load()
        if key in data:
            del data[key]
            return self.save(data)
        return True  # Key doesn't exist, so technically it's already deleted

    def list_keys(self) -> List[str]:
        """
        List all keys in the stored data.
        
        Returns:
            List of keys
        """
        data = self.load()
        return list(data.keys())


class SMEDataStore:
    """Storage utility for Subject Matter Expert data."""

    def __init__(self, file_path: str):
        """Initialize with a file path."""
        self.storage = JsonStorage(file_path)
        
    def load_experts(self) -> List[Dict]:
        """Load all experts from storage."""
        data = self.storage.load()
        return data.get("experts", [])
        
    def save_experts(self, experts: List[Dict]) -> bool:
        """Save experts to storage."""
        data = self.storage.load()
        data["experts"] = experts
        return self.storage.save(data)
        
    def update_expert(self, expert_id: str, updates: Dict) -> bool:
        """
        Update an expert's data.
        
        Args:
            expert_id: The expert's Slack ID
            updates: Dictionary of fields to update
            
        Returns:
            Whether the update was successful
        """
        experts = self.load_experts()
        
        for expert in experts:
            if expert.get("slack_id") == expert_id:
                expert.update(updates)
                return self.save_experts(experts)
                
        return False  # Expert not found
        
    def get_expert(self, expert_id: str) -> Optional[Dict]:
        """
        Get an expert by Slack ID.
        
        Args:
            expert_id: The expert's Slack ID
            
        Returns:
            The expert's data, or None if not found
        """
        experts = self.load_experts()
        
        for expert in experts:
            if expert.get("slack_id") == expert_id:
                return expert
                
        return None


class UserLevelDataStore:
    """Storage utility for user level data."""

    def __init__(self, file_path: str):
        """Initialize with a file path."""
        self.storage = JsonStorage(file_path)
        
    def load_users(self) -> Dict[str, Dict]:
        """Load all user level data from storage."""
        return self.storage.load()
        
    def save_users(self, users: Dict[str, Dict]) -> bool:
        """Save user level data to storage."""
        return self.storage.save(users)
        
    def get_user_level(self, user_id: str) -> Optional[Dict]:
        """
        Get a user's level data.
        
        Args:
            user_id: The user's Slack ID
            
        Returns:
            The user's level data, or None if not found
        """
        users = self.load_users()
        return users.get(user_id)
        
    def set_user_level(self, user_id: str, level_data: Dict) -> bool:
        """
        Set a user's level data.
        
        Args:
            user_id: The user's Slack ID
            level_data: The level data to set
            
        Returns:
            Whether the operation was successful
        """
        users = self.load_users()
        users[user_id] = level_data
        return self.save_users(users)
        
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user's level data.
        
        Args:
            user_id: The user's Slack ID
            
        Returns:
            Whether the operation was successful
        """
        users = self.load_users()
        if user_id in users:
            del users[user_id]
            return self.save_users(users)
        return True  # User doesn't exist, so technically it's already deleted 