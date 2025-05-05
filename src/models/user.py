"""
User models for the Slack Support Bot.
"""
from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel


class UserLevel(str, Enum):
    """User priority levels."""

    VIP = "vip"
    STANDARD = "standard"
    REGULAR = "regular"


class User(BaseModel):
    """User model representing a Slack user."""

    slack_id: str
    name: str
    email: Optional[str] = None
    level: UserLevel = UserLevel.REGULAR
    tags: List[str] = []

    @classmethod
    def from_slack_user(cls, slack_user: Dict) -> "User":
        """Create a User from Slack API user data."""
        return cls(
            slack_id=slack_user["id"],
            name=slack_user.get("real_name", slack_user.get("name", "Unknown")),
            email=slack_user.get("profile", {}).get("email"),
            # Default to regular level, will be updated from user_levels database
            level=UserLevel.REGULAR,
            tags=[],
        )


class UserLevelDatabase:
    """Manages user level data."""

    def __init__(self, user_levels: Dict[str, Dict] = None):
        """Initialize with optional user levels data."""
        self.user_levels = user_levels or {}

    def get_user_level(self, user_id: str) -> UserLevel:
        """Get the level for a user."""
        if user_id in self.user_levels:
            level_str = self.user_levels[user_id].get("level", "regular")
            return UserLevel(level_str.lower())
        return UserLevel.REGULAR

    def get_user_tags(self, user_id: str) -> List[str]:
        """Get tags for a user."""
        if user_id in self.user_levels:
            return self.user_levels[user_id].get("tags", [])
        return []

    def update_user(self, user: User) -> User:
        """Update user with data from database."""
        user.level = self.get_user_level(user.slack_id)
        user.tags = self.get_user_tags(user.slack_id)
        return user 