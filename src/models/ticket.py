"""
Ticket models for support requests.
"""
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.user import User


class TicketPriority(str, Enum):
    """Ticket priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(str, Enum):
    """Ticket status types."""

    NEW = "new"
    AWAITING_INFO = "awaiting_info"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_SME = "waiting_for_sme"
    SME_ASSIGNED = "sme_assigned"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Ticket(BaseModel):
    """Support ticket model."""

    id: str
    title: str
    description: str
    status: TicketStatus = TicketStatus.NEW
    priority: TicketPriority = TicketPriority.MEDIUM
    user: User
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    category: Optional[str] = None
    tags: List[str] = []
    assigned_to: Optional[str] = None  # Slack ID of assigned SME
    thread_ts: Optional[str] = None  # Slack thread timestamp
    channel_id: Optional[str] = None  # Slack channel ID
    additional_info: Dict = {}

    def update_status(self, new_status: TicketStatus):
        """Update ticket status and updated_at timestamp."""
        self.status = new_status
        self.updated_at = datetime.now()

    def assign_to_sme(self, sme_slack_id: str):
        """Assign ticket to an SME."""
        self.assigned_to = sme_slack_id
        self.update_status(TicketStatus.SME_ASSIGNED)

    def mark_waiting_for_info(self):
        """Mark ticket as waiting for more information from user."""
        self.update_status(TicketStatus.AWAITING_INFO)

    def mark_in_progress(self):
        """Mark ticket as in progress."""
        self.update_status(TicketStatus.IN_PROGRESS)

    def resolve(self):
        """Mark ticket as resolved."""
        self.update_status(TicketStatus.RESOLVED)

    def close(self):
        """Mark ticket as closed."""
        self.update_status(TicketStatus.CLOSED)

    def is_urgent(self) -> bool:
        """Check if ticket is considered urgent."""
        return self.priority == TicketPriority.HIGH

    def serialize(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "user": {
                "slack_id": self.user.slack_id,
                "name": self.user.name,
                "email": self.user.email,
                "level": self.user.level.value,
                "tags": self.user.tags,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "category": self.category,
            "tags": self.tags,
            "assigned_to": self.assigned_to,
            "thread_ts": self.thread_ts,
            "channel_id": self.channel_id,
            "additional_info": self.additional_info,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Ticket":
        """Create ticket from dictionary."""
        # Convert string dates to datetime
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Create user
        from src.models.user import UserLevel
        user_data = data["user"]
        user = User(
            slack_id=user_data["slack_id"],
            name=user_data["name"],
            email=user_data.get("email"),
            level=UserLevel(user_data["level"]),
            tags=user_data.get("tags", []),
        )
        
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=TicketStatus(data["status"]),
            priority=TicketPriority(data["priority"]),
            user=user,
            created_at=created_at,
            updated_at=updated_at,
            category=data.get("category"),
            tags=data.get("tags", []),
            assigned_to=data.get("assigned_to"),
            thread_ts=data.get("thread_ts"),
            channel_id=data.get("channel_id"),
            additional_info=data.get("additional_info", {}),
        ) 