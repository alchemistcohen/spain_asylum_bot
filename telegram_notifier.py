"""
Telegram Notifier for Asylum Appointment Bot
Sends notifications when appointments are found
"""

import logging
import aiohttp
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Handles Telegram notifications"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, message: str) -> bool:
        """Send a message via Telegram Bot API"""
        try:
            url = f"{self.api_url}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Telegram message sent successfully")
                        return True
                    else:
                        logger.error(f"Failed to send Telegram message: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_appointment_notification(self, province: str, appointment_info: Dict) -> bool:
        """Send appointment found notification"""
        try:
            # Format the message
            message = self.format_appointment_message(province, appointment_info)
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending appointment notification: {e}")
            return False
    
    def format_appointment_message(self, province: str, appointment_info: Dict) -> str:
        """Format appointment information into a readable message"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"🚨 <b>ASYLUM APPOINTMENT AVAILABLE!</b> 🚨\n\n"
            message += f"📍 <b>Province:</b> {province}\n"
            message += f"⏰ <b>Found at:</b> {timestamp}\n\n"
            
            # Add appointment details if available
            if 'dates' in appointment_info and appointment_info['dates']:
                message += f"📅 <b>Available dates:</b>\n"
                for date in appointment_info['dates'][:5]:  # Show max 5 dates
                    message += f"   • {date}\n"
                if len(appointment_info['dates']) > 5:
                    message += f"   • ... and {len(appointment_info['dates']) - 5} more\n"
                message += "\n"
            
            if 'office' in appointment_info and appointment_info['office']:
                message += f"🏢 <b>Office:</b> {appointment_info['office']}\n\n"
            
            # Add user details for reference
            message += f"👤 <b>User Details:</b>\n"
            message += f"   • Name: ALAN DOUGLAS COHEN TELLO\n"
            message += f"   • Passport: 191484632\n"
            message += f"   • Email: alancohen7@gmail.com\n"
            message += f"   • Phone: 692959148\n\n"
            
            if appointment_info.get('booking_attempted'):
                message += "✅ <b>Auto-booking attempted!</b>\n"
            else:
                message += "⚠️ <b>Manual booking required</b>\n"
            
            message += "\n🔗 Visit: https://icp.administracionelectronica.gob.es/icpplus/acOpcDirect"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"🚨 Appointment found in {province} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    async def send_error_notification(self, error_message: str) -> bool:
        """Send error notification"""
        try:
            message = f"❌ <b>Asylum Bot Error</b>\n\n"
            message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"💬 {error_message}"
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
    
    async def send_status_update(self, status: str) -> bool:
        """Send status update notification"""
        try:
            message = f"ℹ️ <b>Asylum Bot Status</b>\n\n"
            message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"📊 {status}"
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False
