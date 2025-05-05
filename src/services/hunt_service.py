"""
Hunt service for finding and notifying Subject Matter Experts (SMEs).
"""
import logging
import time
import threading
import json
from typing import Dict, List, Optional, Set, Callable
from datetime import datetime, timedelta

from src.models.sme import SMEDatabase, SubjectMatterExpert
from src.models.user import User, UserLevel
from src.models.ticket import Ticket
from src.config.settings import settings

logger = logging.getLogger(__name__)


class HuntRequest:
    """Represents a request to find an SME."""

    def __init__(
        self,
        ticket: Ticket,
        required_expertise: List[str],
        on_accept_callback: Callable[[str, str], None],
        on_timeout_callback: Callable[[], None],
        timeout_minutes: int = None,
    ):
        """
        Initialize a hunt request.
        
        Args:
            ticket: The support ticket
            required_expertise: List of expertise areas needed
            on_accept_callback: Function to call when an SME accepts the request
            on_timeout_callback: Function to call when request times out
            timeout_minutes: Minutes before request times out (default from settings)
        """
        self.ticket = ticket
        self.required_expertise = required_expertise
        self.on_accept_callback = on_accept_callback
        self.on_timeout_callback = on_timeout_callback
        self.timeout_minutes = timeout_minutes or settings.hunt_timeout_minutes
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(minutes=self.timeout_minutes)
        self.notified_experts: Set[str] = set()  # Slack IDs of notified experts
        self.accepted_by: Optional[str] = None  # Slack ID of accepting expert
        self.is_expired = False
        
    def is_timed_out(self) -> bool:
        """Check if the hunt request has timed out."""
        return datetime.now() > self.expires_at
        
    def mark_notified(self, expert_id: str):
        """Mark an expert as notified about this request."""
        self.notified_experts.add(expert_id)
        
    def accept(self, expert_id: str, expert_name: str):
        """Accept the hunt request (by an expert)."""
        if self.is_expired:
            return False
            
        if self.accepted_by:
            return False  # Already accepted by someone else
            
        self.accepted_by = expert_id
        if self.on_accept_callback:
            self.on_accept_callback(expert_id, expert_name)
        return True
        
    def expire(self):
        """Mark the hunt request as expired and trigger the timeout callback."""
        if not self.is_expired and not self.accepted_by:
            self.is_expired = True
            if self.on_timeout_callback:
                self.on_timeout_callback()


class HuntService:
    """Service for finding and notifying SMEs based on expertise needed."""

    def __init__(self, sme_database: SMEDatabase):
        """
        Initialize the hunt service.
        
        Args:
            sme_database: Database of Subject Matter Experts
        """
        self.sme_database = sme_database
        self.active_hunts: Dict[str, HuntRequest] = {}  # ticket ID -> HuntRequest
        self._timeout_thread = None
        self._running = False
        
    def start(self):
        """Start the hunt service timeout monitoring thread."""
        if self._timeout_thread is not None:
            return
            
        self._running = True
        self._timeout_thread = threading.Thread(target=self._monitor_timeouts, daemon=True)
        self._timeout_thread.start()
        
    def stop(self):
        """Stop the hunt service timeout monitoring thread."""
        self._running = False
        if self._timeout_thread:
            self._timeout_thread.join(timeout=1.0)
            self._timeout_thread = None
    
    def _monitor_timeouts(self):
        """Thread function that monitors active hunts for timeouts."""
        while self._running:
            expired_hunts = []
            
            # Check for expired hunts
            for ticket_id, hunt in list(self.active_hunts.items()):
                if hunt.is_timed_out() and not hunt.is_expired:
                    logger.info(f"Hunt for ticket {ticket_id} has timed out")
                    hunt.expire()
                    expired_hunts.append(ticket_id)
            
            # Remove expired hunts
            for ticket_id in expired_hunts:
                self.active_hunts.pop(ticket_id, None)
                
            # Sleep for a bit
            time.sleep(10)
    
    def start_hunt(
        self,
        ticket: Ticket,
        required_expertise: List[str],
        on_accept_callback: Callable[[str, str], None],
        on_timeout_callback: Callable[[], None],
        timeout_minutes: int = None,
    ) -> HuntRequest:
        """
        Start a hunt for an SME with the required expertise.
        
        Args:
            ticket: The support ticket
            required_expertise: List of expertise areas needed
            on_accept_callback: Function to call when an SME accepts the request
            on_timeout_callback: Function to call when request times out
            timeout_minutes: Minutes before request times out
            
        Returns:
            The created hunt request
        """
        # Create hunt request
        hunt = HuntRequest(
            ticket=ticket,
            required_expertise=required_expertise,
            on_accept_callback=on_accept_callback,
            on_timeout_callback=on_timeout_callback,
            timeout_minutes=timeout_minutes,
        )
        
        # Store in active hunts
        self.active_hunts[ticket.id] = hunt
        
        # Find experts with the required expertise
        experts = self._find_experts_for_hunt(
            ticket.user, required_expertise, ticket.priority
        )
        
        # Mark as notified
        for expert in experts:
            hunt.mark_notified(expert.slack_id)
            
        return hunt
    
    def _find_experts_for_hunt(
        self, user: User, required_expertise: List[str], priority=None
    ) -> List[SubjectMatterExpert]:
        """
        Find suitable experts for a hunt based on user level and expertise needed.
        
        Args:
            user: The user who initiated the request
            required_expertise: List of expertise areas needed
            priority: Optional ticket priority to consider
            
        Returns:
            List of suitable experts, ordered by appropriateness
        """
        # Find available experts with required expertise
        experts = self.sme_database.find_experts_by_expertise(
            required_expertise, available_only=True
        )
        
        # If this is a VIP user, prioritize experts with higher ratings
        if user.level == UserLevel.VIP:
            experts.sort(
                key=lambda e: (
                    sum(e.get_rating_for_expertise(exp) for exp in required_expertise),
                    -e.current_load,
                ),
                reverse=True,
            )
        
        # If no experts found, look for unavailable experts too
        if not experts:
            experts = self.sme_database.find_experts_by_expertise(
                required_expertise, available_only=False
            )
        
        return experts
    
    def accept_hunt(self, ticket_id: str, expert_id: str, expert_name: str) -> bool:
        """
        Mark a hunt as accepted by an expert.
        
        Args:
            ticket_id: ID of the ticket being hunted
            expert_id: Slack ID of the accepting expert
            expert_name: Name of the accepting expert
            
        Returns:
            Whether the acceptance was successful
        """
        if ticket_id not in self.active_hunts:
            logger.warning(f"No active hunt found for ticket {ticket_id}")
            return False
            
        hunt = self.active_hunts[ticket_id]
        success = hunt.accept(expert_id, expert_name)
        
        if success:
            # Remove from active hunts
            self.active_hunts.pop(ticket_id, None)
            
        return success
    
    def cancel_hunt(self, ticket_id: str):
        """
        Cancel an active hunt.
        
        Args:
            ticket_id: ID of the ticket to cancel hunt for
        """
        if ticket_id in self.active_hunts:
            self.active_hunts.pop(ticket_id, None)
            logger.info(f"Cancelled hunt for ticket {ticket_id}")
            
    def get_active_hunt(self, ticket_id: str) -> Optional[HuntRequest]:
        """
        Get the active hunt for a ticket.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            The hunt request if active, None otherwise
        """
        return self.active_hunts.get(ticket_id) 