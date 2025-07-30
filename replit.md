# Spanish Asylum Appointment Bot

## Overview

This repository contains a Python bot that automatically monitors Spanish government asylum appointment availability using Playwright browser automation. The bot checks specific provinces for open appointment slots and sends notifications via Telegram when appointments are found.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture
- **Single-purpose automation bot** built with Python
- **Playwright-based web scraping** for browser automation
- **Asynchronous design** using asyncio for concurrent operations
- **Modular component structure** with separate concerns

### Main Components
1. **Bot Engine** (`asylum_bot.py`) - Core automation logic
2. **Application Entry Point** (`main.py`) - Configuration and execution
3. **Notification Service** (`telegram_notifier.py`) - Telegram API integration

## Key Components

### Browser Automation (AsylumAppointmentBot)
- Uses Playwright for headless Chrome automation
- Handles multi-step form navigation on Spanish government website
- Manages user session state and form data
- Implements error handling and retry logic for web interactions

### Notification System (TelegramNotifier)
- Integrates with Telegram Bot API for real-time alerts
- Formats appointment information into user-friendly messages
- Handles API failures gracefully with logging

### Main Application Controller
- Orchestrates the monitoring loop (5-minute intervals)
- Manages environment configuration via .env files
- Implements comprehensive logging to both console and file
- Handles graceful shutdown on interruption

## Data Flow

1. **Initialization Phase**
   - Load environment variables (Telegram tokens, chat IDs)
   - Initialize browser context with specific user agent
   - Set up logging infrastructure

2. **Monitoring Loop**
   - For each province (Almería, Cádiz, Albacete):
     - Navigate through government website flow
     - Fill forms with hardcoded user data
     - Check for available appointment slots
   - If appointments found: extract details and send Telegram notification
   - Wait 5 minutes before next iteration

3. **Navigation Flow**
   - Start at main selection page
   - Select province → Accept
   - Choose service type (POLICIA - SOLICITUD ASILO)
   - Enter personal information (passport, name, birth year, nationality)
   - Check appointment availability
   - Optionally complete booking with email/phone

## External Dependencies

### Core Libraries
- **Playwright** - Browser automation and web scraping
- **aiohttp** - Async HTTP client for Telegram API calls
- **python-dotenv** - Environment variable management

### External Services
- **Telegram Bot API** - For sending notifications
- **Spanish Government Website** - Target system for appointment checking

### Infrastructure Requirements
- Chrome/Chromium browser (managed by Playwright)
- Internet connection for web scraping and API calls
- File system access for logging

## Deployment Strategy

### Environment Configuration
- Uses `.env` file for sensitive data (Telegram tokens)
- Hardcoded user data in bot configuration
- Console and file-based logging for monitoring

### Execution Model
- Designed for continuous running (daemon-like operation)
- Manual start/stop via command line
- Error recovery through exception handling and logging

### Monitoring Provinces
- Configured for three specific provinces: Almería, Cádiz, Albacete
- Sequential checking approach (one province at a time)
- 5-minute intervals between complete cycles

## Recent Changes - July 30, 2025

### Browser Compatibility Resolution
- **Issue Resolved**: Playwright browser dependencies incompatible with Replit environment
- **Solution**: Implemented HTTP requests-based approach (`asylum_bot_requests.py`)
- **Status**: Production ready and actively monitoring

### Implementation Versions Created
1. **asylum_bot.py** - Original Playwright implementation (dependency issues)
2. **asylum_bot_selenium.py** - Selenium backup (ChromeDriver compatibility issues)  
3. **asylum_bot_requests.py** - HTTP requests approach (currently active)

### Production Deployment
- **Environment**: Telegram credentials configured via Replit Secrets
- **Monitoring**: Active checking every 5 minutes for all three provinces
- **Notifications**: Real-time Telegram alerts working with startup confirmations
- **Logging**: Console and file-based tracking in `asylum_bot.log`

### HTTP Reliability Improvements
- **Async HTTP Client**: Migrated from requests to aiohttp for better async performance
- **Exponential Backoff**: Retry logic with 1s, 3s, 6s delays for failed requests
- **Error Handling**: Robust handling of connection timeouts, 4xx/5xx errors
- **Session Management**: Proper aiohttp session lifecycle management
- **Non-blocking**: All network operations now properly async without blocking event loop

### Scalability Considerations
- Single-threaded design suitable for current scope
- Modular structure allows easy addition of new provinces
- Telegram integration supports immediate notification delivery

## Technical Decisions

### Browser Automation Choice
- **Playwright over Selenium**: Better async support and more reliable
- **Headless mode**: Reduces resource usage for server deployment
- **User agent spoofing**: Mimics real browser behavior

### Notification Strategy
- **Telegram over email**: Real-time delivery and mobile accessibility
- **HTML formatting**: Rich message presentation
- **Error tolerance**: Continues operation if notifications fail

### Data Storage
- **No persistent storage**: Stateless design for simplicity
- **In-memory configuration**: Suitable for current monitoring needs
- **Log-based tracking**: File-based audit trail for debugging