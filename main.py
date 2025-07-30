#!/usr/bin/env python3
"""
Spanish Asylum Appointment Bot - Main Entry Point
Monitors appointment availability and sends Telegram notifications
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from asylum_bot_requests import AsylumAppointmentBotRequests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('asylum_bot.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the asylum appointment bot"""
    try:
        # Initialize the bot
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not telegram_token or not chat_id:
            logger.error("Missing required environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
            raise ValueError("Telegram credentials not configured")
        
        bot = AsylumAppointmentBotRequests(telegram_token, chat_id)
        
        logger.info("Starting Spanish Asylum Appointment Bot...")
        logger.info("Monitoring provinces: Almería, Cádiz, Albacete")
        logger.info("Check interval: 5 minutes")
        
        # Run the bot continuously
        await bot.run_continuous_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
