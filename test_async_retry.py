#!/usr/bin/env python3
"""
Test the improved async retry logic for the asylum bot
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from asylum_bot_requests import AsylumAppointmentBotRequests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_async_retry():
    """Test the async retry logic"""
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not chat_id:
        print("❌ Missing Telegram credentials")
        return False
    
    print("🧪 Testing improved async retry logic...")
    
    bot = AsylumAppointmentBotRequests(telegram_token, chat_id)
    
    try:
        # Test HTTP session creation
        session = await bot._get_session()
        print(f"✅ Session created: {session}")
        
        # Test basic HTTP request
        print("🔄 Testing HTTP request with retry logic...")
        result = await bot._make_request_with_retry('GET', 'https://httpbin.org/get')
        
        if result:
            content, url, status = result
            print(f"✅ Request successful: status={status}, url={url}")
        else:
            print("❌ Request failed")
        
        # Test timeout handling (this should fail gracefully)
        print("🔄 Testing timeout handling...")
        result = await bot._make_request_with_retry('GET', 'https://httpbin.org/delay/10', max_retries=2)
        
        if not result:
            print("✅ Timeout handled correctly")
        else:
            print("⚠️ Unexpected success on timeout test")
        
        # Clean up
        await bot._close_session()
        print("✅ Session closed successfully")
        
        print("\n🎉 Async retry logic test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        await bot._close_session()
        return False

if __name__ == "__main__":
    asyncio.run(test_async_retry())