"""
Configuration settings module for the Slack Support Bot.
Handles loading environment variables and providing configuration options.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Configuration settings class."""

    def __init__(self):
        """Initialize Settings with values from environment variables."""
        # Slack API credentials
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.slack_app_token = os.getenv("SLACK_APP_TOKEN")

        # OpenAI API credentials
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Bot configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.bot_name = os.getenv("BOT_NAME", "Atlas Support")
        self.default_response_channel = os.getenv(
            "DEFAULT_RESPONSE_CHANNEL", "support-requests"
        )
        self.hunt_timeout_minutes = int(os.getenv("HUNT_TIMEOUT_MINUTES", 30))
        self.sme_database_path = os.getenv(
            "SME_DATABASE_PATH", "data/sme_database.json"
        )
        self.user_levels_path = os.getenv("USER_LEVELS_PATH", "data/user_levels.json")

        # Configure logging
        self._configure_logging()

    def _configure_logging(self):
        """Configure logging based on settings."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def validate(self):
        """
        Validate required settings are present.
        Raises ValueError if any required settings are missing.
        """
        required_settings = [
            ("SLACK_BOT_TOKEN", self.slack_bot_token),
            ("SLACK_SIGNING_SECRET", self.slack_signing_secret),
            ("OPENAI_API_KEY", self.openai_api_key),
        ]

        missing = [name for name, value in required_settings if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )


# Create a singleton instance
settings = Settings() 