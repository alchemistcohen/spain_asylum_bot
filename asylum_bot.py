"""
Spanish Asylum Appointment Bot
Automates checking for asylum appointment slots using Playwright
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class AsylumAppointmentBot:
    """Bot for monitoring Spanish asylum appointment availability"""
    
    def __init__(self, telegram_token: str, chat_id: str):
        self.telegram_notifier = TelegramNotifier(telegram_token, chat_id)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
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
        
    async def initialize_browser(self) -> None:
        """Initialize Playwright browser"""
        try:
            playwright = await async_playwright().start()
            
            # Try to use system Chromium first, fallback to bundled
            try:
                self.browser = await playwright.chromium.launch(
                    executable_path='/usr/bin/chromium',
                    headless=True,
                    args=[
                        '--no-sandbox', 
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-extensions',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to use system Chromium: {e}, trying bundled browser")
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox', 
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-extensions',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def close_browser(self) -> None:
        """Close browser and clean up"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def create_new_page(self) -> Page:
        """Create a new page with proper settings"""
        if not self.context:
            await self.initialize_browser()
        
        if not self.context:
            raise Exception("Failed to initialize browser context")
        
        page = await self.context.new_page()
        
        # Set timeouts
        page.set_default_timeout(30000)  # 30 seconds
        page.set_default_navigation_timeout(60000)  # 60 seconds
        
        return page
    
    async def select_province(self, page: Page, province: str) -> bool:
        """Select province from dropdown"""
        try:
            logger.info(f"Selecting province: {province}")
            
            # Wait for the province dropdown to be visible
            await page.wait_for_selector('select[name="provincia"]', timeout=10000)
            
            # Select the province
            await page.select_option('select[name="provincia"]', label=province)
            
            # Click Accept button
            await page.click('input[type="submit"][value="Aceptar"]')
            
            # Wait for navigation
            await page.wait_for_url('**/citar?p=4&locale=es', timeout=15000)
            
            logger.info(f"Successfully selected province: {province}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select province {province}: {e}")
            return False
    
    async def select_service_type(self, page: Page) -> bool:
        """Select police service and asylum request"""
        try:
            logger.info("Selecting service type...")
            
            # Wait for the service selection page
            await page.wait_for_selector('input[type="radio"]', timeout=10000)
            
            # Select "TRÁMITES POLICÍA NACIONAL"
            police_radio = page.locator('input[type="radio"][value*="POLICIA"]').first
            await police_radio.check()
            
            # Click Accept to go to next step
            await page.click('input[type="submit"][value="Aceptar"]')
            
            # Wait for asylum service selection
            await page.wait_for_selector('input[type="radio"]', timeout=10000)
            
            # Select "POLICIA – SOLICITUD ASILO"
            asylum_radio = page.locator('input[type="radio"][value*="ASILO"]').first
            await asylum_radio.check()
            
            # Click Accept
            await page.click('input[type="submit"][value="Aceptar"]')
            
            # Wait for info page
            await page.wait_for_url('**/acInfo', timeout=15000)
            
            logger.info("Successfully selected service type")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select service type: {e}")
            return False
    
    async def proceed_to_entry_form(self, page: Page) -> bool:
        """Click Enter button to proceed to entry form"""
        try:
            logger.info("Proceeding to entry form...")
            
            # Click "Entrar" button
            await page.click('input[type="submit"][value="Entrar"]')
            
            # Wait for entry form page
            await page.wait_for_url('**/acEntrada', timeout=15000)
            
            logger.info("Successfully reached entry form")
            return True
            
        except Exception as e:
            logger.error(f"Failed to proceed to entry form: {e}")
            return False
    
    async def fill_user_data(self, page: Page) -> bool:
        """Fill user data in the entry form"""
        try:
            logger.info("Filling user data...")
            
            # Wait for form elements
            await page.wait_for_selector('select[name="rdbTipoDoc"]', timeout=10000)
            
            # Select document type: Pasaporte
            await page.select_option('select[name="rdbTipoDoc"]', label='Pasaporte')
            
            # Fill passport number
            await page.fill('input[name="txtIdCitado"]', self.user_data['passport_number'])
            
            # Fill name and surname
            await page.fill('input[name="txtDesCitado"]', self.user_data['full_name'])
            
            # Fill birth year
            await page.fill('input[name="txtAnnoCitado"]', self.user_data['birth_year'])
            
            # Select nationality
            await page.select_option('select[name="txtPaisNac"]', label=self.user_data['nationality'])
            
            # Submit the form
            await page.click('input[type="submit"][value="Aceptar"]')
            
            # Wait for next page
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            logger.info("Successfully filled user data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill user data: {e}")
            return False
    
    async def check_appointment_availability(self, page: Page) -> Tuple[bool, Optional[Dict]]:
        """Check if appointments are available"""
        try:
            logger.info("Checking appointment availability...")
            
            # Wait for the page to load
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Look for appointment slots or error messages
            page_content = await page.content()
            
            # Check for common "no appointments" messages
            no_appointment_indicators = [
                "No hay citas disponibles",
                "no hay citas libres",
                "En este momento no hay citas disponibles",
                "No quedan citas libres"
            ]
            
            for indicator in no_appointment_indicators:
                if indicator.lower() in page_content.lower():
                    logger.info("No appointments available")
                    return False, None
            
            # Look for appointment calendar or selection
            calendar_selectors = [
                'table.calendario',
                '.calendar',
                'input[type="radio"][name*="fecha"]',
                'select[name*="fecha"]'
            ]
            
            for selector in calendar_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # Extract appointment details
                        appointment_info = await self.extract_appointment_details(page)
                        logger.info("Appointments found!")
                        return True, appointment_info
                except:
                    continue
            
            logger.info("No appointment indicators found")
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking appointment availability: {e}")
            return False, None
    
    async def extract_appointment_details(self, page: Page) -> Dict:
        """Extract available appointment details"""
        try:
            appointment_details = {
                'province': '',
                'dates': [],
                'office': '',
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to extract available dates
            try:
                date_elements = await page.query_selector_all('input[type="radio"][name*="fecha"]')
                for element in date_elements:
                    value = await element.get_attribute('value')
                    if value:
                        appointment_details['dates'].append(value)
            except:
                pass
            
            # Try to extract office information
            try:
                office_element = await page.query_selector('.oficina, .office, [contains(text(), "Oficina")]')
                if office_element:
                    appointment_details['office'] = await office_element.text_content()
            except:
                pass
            
            return appointment_details
            
        except Exception as e:
            logger.error(f"Error extracting appointment details: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def auto_select_appointment(self, page: Page) -> bool:
        """Attempt to automatically select and book an appointment"""
        try:
            logger.info("Attempting to auto-select appointment...")
            
            # Look for the first available appointment slot
            first_appointment = await page.query_selector('input[type="radio"][name*="fecha"]:first-of-type')
            if first_appointment:
                await first_appointment.check()
                
                # Click continue/next button
                continue_button = await page.query_selector('input[type="submit"][value*="Siguiente"], input[type="submit"][value*="Continuar"]')
                if continue_button:
                    await continue_button.click()
                    
                    # Wait for contact form
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Fill contact information
                    try:
                        await page.fill('input[name*="email"], input[type="email"]', self.user_data['email'])
                        await page.fill('input[name*="telefono"], input[name*="phone"]', self.user_data['phone'])
                        
                        # Submit the booking
                        submit_button = await page.query_selector('input[type="submit"][value*="Enviar"], input[type="submit"][value*="Confirmar"]')
                        if submit_button:
                            await submit_button.click()
                            logger.info("Appointment booking submitted!")
                            return True
                    except Exception as e:
                        logger.warning(f"Could not fill contact form: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error auto-selecting appointment: {e}")
            return False
    
    async def check_province_appointments(self, province: str) -> Optional[Dict]:
        """Check appointments for a specific province"""
        page = None
        try:
            logger.info(f"Checking appointments for {province}")
            
            page = await self.create_new_page()
            
            # Navigate to starting URL
            await page.goto(self.base_url, wait_until='networkidle')
            
            # Step 1: Select province
            if not await self.select_province(page, province):
                return None
            
            # Step 2: Select service type
            if not await self.select_service_type(page):
                return None
            
            # Step 3: Proceed to entry form
            if not await self.proceed_to_entry_form(page):
                return None
            
            # Step 4: Fill user data
            if not await self.fill_user_data(page):
                return None
            
            # Step 5: Check appointment availability
            has_appointments, appointment_info = await self.check_appointment_availability(page)
            
            if has_appointments and appointment_info:
                appointment_info['province'] = province
                
                # Try to auto-select appointment
                booking_success = await self.auto_select_appointment(page)
                appointment_info['booking_attempted'] = booking_success
                
                return appointment_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking {province}: {e}")
            return None
        finally:
            if page:
                await page.close()
    
    async def run_single_check(self) -> None:
        """Run a single check cycle for all provinces"""
        try:
            logger.info("Starting appointment check cycle...")
            
            if not self.browser:
                await self.initialize_browser()
            
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
            else:
                logger.info("No appointments found in any province")
                
        except Exception as e:
            logger.error(f"Error in check cycle: {e}")
    
    async def run_continuous_monitoring(self) -> None:
        """Run continuous monitoring every 5 minutes"""
        try:
            await self.initialize_browser()
            
            while True:
                try:
                    await self.run_single_check()
                    logger.info("Check cycle completed. Waiting 5 minutes...")
                    await asyncio.sleep(300)  # 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
                    
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            await self.close_browser()
