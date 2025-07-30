"""
Spanish Asylum Appointment Bot - Requests Version
Simple HTTP-based approach to check asylum appointments
"""

import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from telegram_notifier import TelegramNotifier
import time

logger = logging.getLogger(__name__)

class AsylumAppointmentBotRequests:
    """Bot for monitoring Spanish asylum appointment availability using async HTTP requests"""
    
    def __init__(self, telegram_token: str, chat_id: str):
        self.telegram_notifier = TelegramNotifier(telegram_token, chat_id)
        self.session = None
        
        # HTTP headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # User data for form filling
        self.user_data = {
            'passport_number': '191484632',
            'full_name': 'ALAN DOUGLAS COHEN TELLO',
            'birth_year': '1986',
            'nationality': 'Venezuela',
            'email': 'alancohen7@gmail.com',
            'phone': '692959148'
        }
        
        # Provinces to monitor
        self.provinces = ['Almería', 'Cádiz', 'Albacete']
        
        # URLs used in the process
        self.base_url = 'https://icp.administracionelectronica.gob.es/icpplus/acOpcDirect'
        
        # Tracking for connection status
        self.consecutive_failures = 0
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector
            )
        return self.session
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request_with_retry(self, method: str, url: str, max_retries: int = 3, **kwargs) -> Optional[tuple]:
        """Make HTTP request with exponential backoff retry logic"""
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                # Calculate exponential backoff delay: 1s, 3s, 6s
                if attempt > 0:
                    delay = min(2 ** attempt, 6)  # Cap at 6 seconds
                    logger.info(f"Retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(delay)
                
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                async with session.request(method, url, **kwargs) as response:
                    # Check for HTTP errors
                    if response.status >= 500:
                        logger.warning(f"Server error {response.status} on attempt {attempt + 1}")
                        if attempt == max_retries - 1:
                            logger.error(f"All retries failed with server error {response.status}")
                            return None
                        continue
                    elif response.status >= 400:
                        logger.error(f"Client error {response.status}, not retrying")
                        return None
                    
                    # Success - read content and return tuple
                    content = await response.read()
                    logger.debug(f"Request successful with status {response.status}")
                    return (content, str(response.url), response.status)
                    
            except aiohttp.ClientConnectorError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All connection attempts failed: {e}")
                    return None
                    
            except aiohttp.ServerTimeoutError as e:
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts timed out: {e}")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed with unexpected error: {e}")
                    return None
        
        return None
    
    async def check_province_appointments(self, province: str) -> Optional[Dict]:
        """Check appointments for a specific province using async HTTP requests with retry logic"""
        try:
            logger.info(f"Checking appointments for {province} using async HTTP requests...")
            
            # Step 1: Get the initial form with retry logic
            response_data = await self._make_request_with_retry('GET', self.base_url)
            if not response_data:
                logger.error(f"Failed to access initial page for {province}")
                return None
            
            content, url, status = response_data
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find the form and get necessary parameters
            form = soup.find('form')
            if not form:
                logger.error("No form found on initial page")
                return None
            
            # Get form action URL
            action_url = form.get('action', '')
            if action_url.startswith('/'):
                action_url = 'https://icp.administracionelectronica.gob.es' + action_url
            
            # Prepare form data for province selection
            form_data = {}
            
            # Get all form inputs
            for input_tag in form.find_all(['input', 'select']):
                name = input_tag.get('name')
                if name:
                    if input_tag.name == 'select' and name == 'provincia':
                        # Find the option with our province
                        for option in input_tag.find_all('option'):
                            if option.text.strip() == province:
                                form_data[name] = option.get('value', '')
                                break
                    elif input_tag.get('type') == 'hidden':
                        form_data[name] = input_tag.get('value', '')
                    elif input_tag.get('type') == 'submit':
                        continue
                    else:
                        form_data[name] = input_tag.get('value', '')
            
            if 'provincia' not in form_data:
                logger.error(f"Province {province} not found in form options")
                return None
            
            logger.info(f"Submitting province selection for {province}")
            
            # Submit province selection with retry logic
            form_response_data = await self._make_request_with_retry(
                'POST', 
                action_url or self.base_url, 
                data=form_data
            )
            
            if not form_response_data:
                logger.error(f"Failed to submit province selection for {province}")
                return None
            
            # Read the response content
            response_content, response_url, response_status = form_response_data
            
            # Check if we got redirected to the service selection page
            if 'citar?p=4&locale=es' in response_url:
                logger.info("Successfully reached service selection page")
                
                # Parse the service selection page
                soup = BeautifulSoup(response_content, 'html.parser')
                
                # Look for appointment availability indicators
                page_text = soup.get_text().lower()
                
                # Check for "no appointments" messages
                no_appointment_indicators = [
                    "no hay citas disponibles",
                    "no hay citas libres",
                    "en este momento no hay citas disponibles",
                    "no quedan citas libres",
                    "todas las citas están ocupadas"
                ]
                
                for indicator in no_appointment_indicators:
                    if indicator in page_text:
                        logger.info(f"No appointments available in {province}")
                        return None
                
                # Look for positive appointment indicators
                appointment_indicators = [
                    "citas disponibles",
                    "citas libres",
                    "seleccione una fecha",
                    "calendario",
                    "fecha disponible"
                ]
                
                appointment_found = False
                for indicator in appointment_indicators:
                    if indicator in page_text:
                        appointment_found = True
                        break
                
                if appointment_found:
                    logger.info(f"Potential appointments found in {province}!")
                    
                    # Extract more details
                    appointment_info = {
                        'province': province,
                        'timestamp': datetime.now().isoformat(),
                        'page_url': response_url,
                        'found_via': 'Async HTTP requests with retry logic',
                        'status': 'appointments_detected'
                    }
                    
                    # Try to extract calendar or date information
                    calendar_tables = soup.find_all('table', class_=['calendario', 'calendar'])
                    if calendar_tables:
                        appointment_info['calendar_found'] = True
                    
                    # Look for date inputs or selects
                    date_inputs = soup.find_all(['input', 'select'], attrs={'name': lambda x: x and 'fecha' in x.lower()})
                    if date_inputs:
                        appointment_info['date_selection_available'] = True
                    
                    return appointment_info
                else:
                    logger.info(f"No clear appointment indicators found for {province}")
                    return None
            else:
                logger.warning(f"Unexpected redirect for {province}: {response_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error checking {province}: {e}")
            return None
    
    async def run_single_check(self) -> None:
        """Run a single check cycle for all provinces"""
        try:
            logger.info("Starting appointment check cycle...")
            
            found_appointments = []
            
            for province in self.provinces:
                try:
                    appointment_info = await self.check_province_appointments(province)
                    if appointment_info:
                        found_appointments.append(appointment_info)
                        logger.info(f"Found appointments in {province}!")
                        
                        # Send Telegram notification
                        await self.telegram_notifier.send_appointment_notification(
                            province, appointment_info
                        )
                    else:
                        logger.info(f"No appointments available in {province}")
                        
                except Exception as e:
                    logger.error(f"Error checking {province}: {e}")
                
                # Small delay between provinces
                await asyncio.sleep(2)
            
            if found_appointments:
                logger.info(f"Total appointments found: {len(found_appointments)}")
                self.consecutive_failures = 0  # Reset failure counter on success
            else:
                logger.info("No appointments found in any province")
                
                # Track consecutive failures (all provinces timing out)
                all_failed = all(
                    'Failed to access initial page' in str(e) 
                    for e in [logger.handlers[0].buffer if hasattr(logger.handlers[0], 'buffer') else []]
                )
                if all_failed:
                    self.consecutive_failures += 1
                else:
                    self.consecutive_failures = 0
                
        except Exception as e:
            logger.error(f"Error in check cycle: {e}")
    
    async def run_continuous_monitoring(self) -> None:
        """Run continuous monitoring with 5-minute intervals"""
        try:
            # Send startup notification
            await self.telegram_notifier.send_status_update(
                "🤖 Asylum Bot started monitoring!\n"
                f"📍 Provinces: {', '.join(self.provinces)}\n"
                f"⏱️ Check interval: 5 minutes\n"
                f"🔧 Method: Async HTTP with retry logic"
            )
            
            cycle_count = 0
            
            while True:
                try:
                    cycle_count += 1
                    await self.run_single_check()
                    
                    # Send periodic status updates every 12 cycles (1 hour)
                    if cycle_count % 12 == 0:
                        await self.telegram_notifier.send_status_update(
                            f"✅ Bot is active (cycle #{cycle_count})\n"
                            f"⏱️ Last check: {datetime.now().strftime('%H:%M')}\n"
                            f"📊 Monitoring all 3 provinces"
                        )
                    
                    # Wait 5 minutes before next check
                    logger.info("Waiting 5 minutes before next check...")
                    await asyncio.sleep(300)  # 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {e}")
                    # Send error notification
                    await self.telegram_notifier.send_error_notification(f"Monitoring error: {str(e)}")
                    # Wait a bit before retrying
                    await asyncio.sleep(60)
                    
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            await self.telegram_notifier.send_status_update("⏹️ Asylum Bot monitoring stopped")
        except Exception as e:
            logger.error(f"Fatal error in monitoring: {e}")
            await self.telegram_notifier.send_error_notification(f"Fatal error: {str(e)}")
            raise
        finally:
            # Clean up session
            await self._close_session()