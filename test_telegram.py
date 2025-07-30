#!/usr/bin/env python3
"""
Simple test script to verify Telegram notifications work
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from telegram_notifier import TelegramNotifier

# Load environment variables
load_dotenv()

async def test_telegram():
    """Test Telegram notification functionality"""
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not telegram_token or not chat_id:
            print("❌ Missing Telegram credentials in environment variables")
            return False
        
        print("🔄 Testing Telegram connection...")
        
        notifier = TelegramNotifier(telegram_token, chat_id)
        
        # Test basic message
        test_message = "🧪 <b>Test Message</b>\n\nAsylum Bot is working correctly!\n📅 " + str(asyncio.get_event_loop().time())
        
        success = await notifier.send_message(test_message)
        
        if success:
            print("✅ Telegram test successful! Check your Telegram for the test message.")
            return True
        else:
            print("❌ Telegram test failed. Check your bot token and chat ID.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Telegram: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_telegram())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Test error: {e}")
        sys.exit(1)