"""
Spanish Asylum Appointment Bot - Selenium Version
Alternative implementation using Selenium for better compatibility
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class AsylumAppointmentBotSelenium:
    """Bot for monitoring Spanish asylum appointment availability using Selenium"""
    
    def __init__(self, telegram_token: str, chat_id: str):
        self.telegram_notifier = TelegramNotifier(telegram_token, chat_id)
        self.driver: Optional[webdriver.Chrome] = None
        
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
        
    def initialize_driver(self) -> None:
        """Initialize Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--window-size=1280,720')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Try system Chrome first
            try:
                chrome_options.binary_location = '/usr/bin/chromium'
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                logger.warning(f"System Chrome not available: {e}, trying default")
                chrome_options.binary_location = None
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def close_driver(self) -> None:
        """Close WebDriver and clean up"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            logger.info("WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {e}")
    
    def select_province(self, province: str) -> bool:
        """Select province from dropdown"""
        try:
            logger.info(f"Selecting province: {province}")
            
            if not self.driver:
                self.initialize_driver()
            
            # Navigate to starting URL
            self.driver.get(self.base_url)
            
            # Wait for the province dropdown
            wait = WebDriverWait(self.driver, 15)
            province_dropdown = wait.until(
                EC.presence_of_element_located((By.NAME, "provincia"))
            )
            
            # Select the province
            select = Select(province_dropdown)
            select.select_by_visible_text(province)
            
            # Click Accept button
            accept_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Aceptar"]')
            accept_button.click()
            
            # Wait for navigation
            wait.until(EC.url_contains('citar?p=4&locale=es'))
            
            logger.info(f"Successfully selected province: {province}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select province {province}: {e}")
            return False
    
    def select_service_type(self) -> bool:
        """Select police service and asylum request"""
        try:
            logger.info("Selecting service type...")
            
            wait = WebDriverWait(self.driver, 15)
            
            # Wait for the service selection page
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="radio"]')))
            
            # Select "TRÁMITES POLICÍA NACIONAL"
            police_radios = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            for radio in police_radios:
                parent = radio.find_element(By.XPATH, '..')
                if 'POLICIA' in parent.text.upper():
                    radio.click()
                    break
            
            # Click Accept to go to next step
            accept_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Aceptar"]')
            accept_button.click()
            
            # Wait for asylum service selection
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="radio"]')))
            
            # Select "POLICIA – SOLICITUD ASILO"
            asylum_radios = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            for radio in asylum_radios:
                parent = radio.find_element(By.XPATH, '..')
                if 'ASILO' in parent.text.upper():
                    radio.click()
                    break
            
            # Click Accept
            accept_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Aceptar"]')
            accept_button.click()
            
            # Wait for info page
            wait.until(EC.url_contains('acInfo'))
            
            logger.info("Successfully selected service type")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select service type: {e}")
            return False
    
    def proceed_to_entry_form(self) -> bool:
        """Click Enter button to proceed to entry form"""
        try:
            logger.info("Proceeding to entry form...")
            
            wait = WebDriverWait(self.driver, 15)
            
            # Click "Entrar" button
            enter_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"][value="Entrar"]'))
            )
            enter_button.click()
            
            # Wait for entry form page
            wait.until(EC.url_contains('acEntrada'))
            
            logger.info("Successfully reached entry form")
            return True
            
        except Exception as e:
            logger.error(f"Failed to proceed to entry form: {e}")
            return False
    
    def fill_user_data(self) -> bool:
        """Fill user data in the entry form"""
        try:
            logger.info("Filling user data...")
            
            wait = WebDriverWait(self.driver, 15)
            
            # Wait for form elements
            wait.until(EC.presence_of_element_located((By.NAME, "rdbTipoDoc")))
            
            # Select document type: Pasaporte
            doc_type_dropdown = Select(self.driver.find_element(By.NAME, "rdbTipoDoc"))
            doc_type_dropdown.select_by_visible_text('Pasaporte')
            
            # Fill passport number
            passport_field = self.driver.find_element(By.NAME, "txtIdCitado")
            passport_field.clear()
            passport_field.send_keys(self.user_data['passport_number'])
            
            # Fill name and surname
            name_field = self.driver.find_element(By.NAME, "txtDesCitado")
            name_field.clear()
            name_field.send_keys(self.user_data['full_name'])
            
            # Fill birth year
            year_field = self.driver.find_element(By.NAME, "txtAnnoCitado")
            year_field.clear()
            year_field.send_keys(self.user_data['birth_year'])
            
            # Select nationality
            nationality_dropdown = Select(self.driver.find_element(By.NAME, "txtPaisNac"))
            nationality_dropdown.select_by_visible_text(self.user_data['nationality'])
            
            # Submit the form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Aceptar"]')
            submit_button.click()
            
            # Wait for next page
            time.sleep(3)
            
            logger.info("Successfully filled user data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill user data: {e}")
            return False
    
    def check_appointment_availability(self) -> Tuple[bool, Optional[Dict]]:
        """Check if appointments are available"""
        try:
            logger.info("Checking appointment availability...")
            
            # Wait for the page to load
            time.sleep(3)
            
            # Get page content
            page_source = self.driver.page_source
            
            # Check for common "no appointments" messages
            no_appointment_indicators = [
                "No hay citas disponibles",
                "no hay citas libres",
                "En este momento no hay citas disponibles",
                "No quedan citas libres"
            ]
            
            for indicator in no_appointment_indicators:
                if indicator.lower() in page_source.lower():
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
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Extract appointment details
                        appointment_info = self.extract_appointment_details()
                        logger.info("Appointments found!")
                        return True, appointment_info
                except:
                    continue
            
            logger.info("No appointment indicators found")
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking appointment availability: {e}")
            return False, None
    
    def extract_appointment_details(self) -> Dict:
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
                date_elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"][name*="fecha"]')
                for element in date_elements:
                    value = element.get_attribute('value')
                    if value:
                        appointment_details['dates'].append(value)
            except:
                pass
            
            # Try to extract office information
            try:
                office_elements = self.driver.find_elements(By.CSS_SELECTOR, '.oficina, .office')
                if office_elements:
                    appointment_details['office'] = office_elements[0].text
            except:
                pass
            
            return appointment_details
            
        except Exception as e:
            logger.error(f"Error extracting appointment details: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def auto_select_appointment(self) -> bool:
        """Attempt to automatically select and book an appointment"""
        try:
            logger.info("Attempting to auto-select appointment...")
            
            # Look for the first available appointment slot
            date_radios = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"][name*="fecha"]')
            if date_radios:
                date_radios[0].click()
                
                # Click continue/next button
                continue_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"][value*="Siguiente"], input[type="submit"][value*="Continuar"]')
                if continue_buttons:
                    continue_buttons[0].click()
                    
                    # Wait for contact form
                    time.sleep(3)
                    
                    # Fill contact information
                    try:
                        email_fields = self.driver.find_elements(By.CSS_SELECTOR, 'input[name*="email"], input[type="email"]')
                        if email_fields:
                            email_fields[0].clear()
                            email_fields[0].send_keys(self.user_data['email'])
                        
                        phone_fields = self.driver.find_elements(By.CSS_SELECTOR, 'input[name*="telefono"], input[name*="phone"]')
                        if phone_fields:
                            phone_fields[0].clear()
                            phone_fields[0].send_keys(self.user_data['phone'])
                        
                        # Submit the booking
                        submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"][value*="Enviar"], input[type="submit"][value*="Confirmar"]')
                        if submit_buttons:
                            submit_buttons[0].click()
                            logger.info("Appointment booking submitted!")
                            return True
                    except Exception as e:
                        logger.warning(f"Could not fill contact form: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error auto-selecting appointment: {e}")
            return False
    
    def check_province_appointments(self, province: str) -> Optional[Dict]:
        """Check appointments for a specific province"""
        try:
            logger.info(f"Checking appointments for {province}")
            
            # Step 1: Select province
            if not self.select_province(province):
                return None
            
            # Step 2: Select service type
            if not self.select_service_type():
                return None
            
            # Step 3: Proceed to entry form
            if not self.proceed_to_entry_form():
                return None
            
            # Step 4: Fill user data
            if not self.fill_user_data():
                return None
            
            # Step 5: Check appointment availability
            has_appointments, appointment_info = self.check_appointment_availability()
            
            if has_appointments and appointment_info:
                appointment_info['province'] = province
                
                # Try to auto-select appointment
                booking_success = self.auto_select_appointment()
                appointment_info['booking_attempted'] = booking_success
                
                return appointment_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking {province}: {e}")
            return None
        finally:
            self.close_driver()
    
    async def run_single_check(self) -> None:
        """Run a single check cycle for all provinces"""
        try:
            logger.info("Starting appointment check cycle...")
            
            found_appointments = []
            
            for province in self.provinces:
                try:
                    appointment_info = self.check_province_appointments(province)
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
        """Run continuous monitoring with 5-minute intervals"""
        try:
            # Send startup notification
            await self.telegram_notifier.send_status_update(
                "🤖 Asylum Bot started monitoring!\n"
                f"📍 Provinces: {', '.join(self.provinces)}\n"
                f"⏱️ Check interval: 5 minutes"
            )
            
            while True:
                try:
                    await self.run_single_check()
                    
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
            self.close_driver()