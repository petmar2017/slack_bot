"""
Main application for the Atlas Support Bot.
"""
import os
import logging
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.config.settings import settings
from src.models.user import User, UserLevel, UserLevelDatabase
from src.models.sme import SMEDatabase, SubjectMatterExpert
from src.models.ticket import Ticket, TicketStatus, TicketPriority
from src.services.llm_service import LLMService, QueryType, ResponseType
from src.services.hunt_service import HuntService
from src.utils.storage import JsonStorage, SMEDataStore, UserLevelDataStore

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the Slack app
app = App(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret,
)

# Initialize services
def init_services():
    """Initialize all services and databases."""
    # Load SME database
    sme_data_store = SMEDataStore(settings.sme_database_path)
    sme_data = sme_data_store.load_experts()
    sme_database = SMEDatabase(sme_data)
    
    # Load user levels database
    user_level_store = UserLevelDataStore(settings.user_levels_path)
    user_levels = user_level_store.load_users()
    user_level_database = UserLevelDatabase(user_levels)
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Initialize hunt service
    hunt_service = HuntService(sme_database)
    hunt_service.start()
    
    return {
        "sme_database": sme_database,
        "user_level_database": user_level_database,
        "llm_service": llm_service,
        "hunt_service": hunt_service,
        "sme_data_store": sme_data_store,
        "user_level_store": user_level_store,
    }


# Global services dict that will be populated in main()
services = {}


@app.event("app_mention")
def handle_app_mentions(body, say):
    """Handle app mentions in channels."""
    event = body["event"]
    channel_id = event["channel"]
    user_id = event["user"]
    text = event["text"]
    thread_ts = event.get("thread_ts", event["ts"])
    
    # Remove the bot mention from the text
    query = text.split(">", 1)[1].strip() if ">" in text else text
    
    # Process the message
    process_message(user_id, query, channel_id, thread_ts, say)


@app.event("message")
def handle_direct_messages(body, say):
    """Handle direct messages to the bot."""
    event = body["event"]
    
    # Skip bot messages and messages in channels (which are handled by app_mention)
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return
        
    # Only process DMs (im = direct message channel)
    if event.get("channel_type") != "im":
        return
    
    user_id = event["user"]
    text = event["text"]
    channel_id = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])
    
    # Process the message
    process_message(user_id, text, channel_id, thread_ts, say)


def process_message(user_id: str, text: str, channel_id: str, thread_ts: str, say):
    """
    Process a message from a user.
    
    Args:
        user_id: The ID of the user who sent the message
        text: The text of the message
        channel_id: The ID of the channel where the message was sent
        thread_ts: The timestamp of the thread or message
        say: Function to reply with a message
    """
    # Get user info
    user_info = app.client.users_info(user=user_id)["user"]
    user = User.from_slack_user(user_info)
    
    # Update user with level info
    services["user_level_database"].update_user(user)
    
    # First, acknowledge message receipt
    say(
        text="I'm analyzing your request...",
        thread_ts=thread_ts,
        channel=channel_id,
    )
    
    # Analyze the query using LLM
    query_type, extracted_info, urgency_score = services["llm_service"].analyze_query(text)
    
    # Generate initial response
    response_text, response_type = services["llm_service"].generate_initial_response(
        text, query_type, extracted_info
    )
    
    # Create a ticket for tracking
    ticket = create_ticket(user, text, query_type, extracted_info, urgency_score, channel_id, thread_ts)
    
    # Send the response
    say(
        text=response_text,
        thread_ts=thread_ts,
        channel=channel_id,
    )
    
    # If urgent or needs escalation, start hunt for SME
    if query_type == QueryType.URGENT_ISSUE or response_type == ResponseType.ESCALATE_TO_HUMAN:
        start_sme_hunt(ticket, extracted_info, say)


def create_ticket(
    user: User,
    text: str,
    query_type: QueryType,
    extracted_info: Dict,
    urgency_score: float,
    channel_id: str,
    thread_ts: str,
) -> Ticket:
    """
    Create a ticket for the user's request.
    
    Args:
        user: The user who made the request
        text: The text of the request
        query_type: The type of query
        extracted_info: Extracted information from the query
        urgency_score: The urgency score (0-1)
        channel_id: The channel ID where the request was made
        thread_ts: The thread timestamp
        
    Returns:
        The created ticket
    """
    # Generate a unique ID for the ticket
    ticket_id = f"ticket-{uuid.uuid4().hex[:8]}"
    
    # Determine priority based on urgency score and user level
    priority = TicketPriority.HIGH if urgency_score > 0.7 else (
        TicketPriority.MEDIUM if urgency_score > 0.3 else TicketPriority.LOW
    )
    
    # VIP users get higher priority
    if user.level == UserLevel.VIP and priority != TicketPriority.HIGH:
        priority = TicketPriority.MEDIUM if priority == TicketPriority.LOW else TicketPriority.HIGH
    
    # Create the ticket
    ticket = Ticket(
        id=ticket_id,
        title=extracted_info.get("topic", text[:50] + ("..." if len(text) > 50 else "")),
        description=text,
        status=TicketStatus.NEW,
        priority=priority,
        user=user,
        category=extracted_info.get("category"),
        tags=extracted_info.get("tags", []),
        thread_ts=thread_ts,
        channel_id=channel_id,
        additional_info=extracted_info,
    )
    
    # Store the ticket (in a real implementation, you would save this to a database)
    # For now, we'll just log it
    logger.info(f"Created ticket: {ticket_id} - {ticket.title}")
    
    return ticket


def start_sme_hunt(ticket: Ticket, extracted_info: Dict, say):
    """
    Start hunting for an SME to handle the ticket.
    
    Args:
        ticket: The ticket to find an SME for
        extracted_info: Extracted information from the query
        say: Function to send messages
    """
    # Get expertise areas from extracted info
    expertise_areas = extracted_info.get("expertise_areas", [])
    if not expertise_areas and "topic" in extracted_info:
        expertise_areas = [extracted_info["topic"]]
    
    # Define callbacks for hunt
    def on_accept_callback(expert_id, expert_name):
        ticket.assign_to_sme(expert_id)
        say(
            text=f"Good news! {expert_name} will be assisting you with this request.",
            thread_ts=ticket.thread_ts,
            channel=ticket.channel_id,
        )
    
    def on_timeout_callback():
        say(
            text="I'm still looking for the best team member to assist you. Someone will respond as soon as possible.",
            thread_ts=ticket.thread_ts,
            channel=ticket.channel_id,
        )
    
    # Start the hunt
    hunt = services["hunt_service"].start_hunt(
        ticket=ticket,
        required_expertise=expertise_areas,
        on_accept_callback=on_accept_callback,
        on_timeout_callback=on_timeout_callback,
    )
    
    # In a real implementation, you would notify SMEs here
    # For this demo, we'll just log it
    logger.info(
        f"Started hunt for ticket {ticket.id} with expertise areas: {expertise_areas}"
    )
    logger.info(f"Notified {len(hunt.notified_experts)} experts")
    
    # Inform the user
    say(
        text="I've notified our support team. A subject matter expert will assist you shortly.",
        thread_ts=ticket.thread_ts,
        channel=ticket.channel_id,
    )


# Command for SMEs to claim tickets
@app.command("/claim")
def handle_claim_command(ack, command, say):
    """Handle the /claim command for SMEs to claim tickets."""
    ack()
    
    user_id = command["user_id"]
    user_name = command["user_name"]
    text = command["text"].strip()
    
    if not text:
        say(
            text="Please provide a ticket ID. Usage: `/claim ticket-id`",
            channel=command["channel_id"],
        )
        return
    
    ticket_id = text
    
    # In a real implementation, you would retrieve the ticket and validate
    # For now, we'll just simulate accepting the hunt
    success = services["hunt_service"].accept_hunt(ticket_id, user_id, user_name)
    
    if success:
        say(
            text=f"You have successfully claimed ticket {ticket_id}.",
            channel=command["channel_id"],
        )
    else:
        say(
            text=f"Failed to claim ticket {ticket_id}. It may already be claimed or does not exist.",
            channel=command["channel_id"],
        )


def main():
    """Main entry point for the application."""
    global services
    
    # Validate required settings
    settings.validate()
    
    # Initialize services
    services = init_services()
    
    # Start the Socket Mode handler
    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()


if __name__ == "__main__":
    main() 