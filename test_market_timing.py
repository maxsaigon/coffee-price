#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Timing System Test Suite
Comprehensive testing for coffee market timing and notification system
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
import pytz
from typing import Dict, Any, List
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from market_config import MarketConfigManager
from market_scheduler import MarketTimingScheduler
from investing_market_scraper import InvestingMarketScraper
from telegram_bot import TelegramBot

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_market_timing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarketTimingTestSuite:
    """
    Comprehensive test suite for market timing system
    """
    
    def __init__(self):
        self.config_manager = MarketConfigManager()
        self.scheduler = MarketTimingScheduler()
        self.scraper = InvestingMarketScraper()
        self.telegram_bot = None
        self.test_results = {}
        
        # Vietnam timezone for consistent reporting
        self.vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        logger.info("🧪 Starting Market Timing System Test Suite")
        logger.info("=" * 60)
        
        test_suites = [
            ("Configuration Tests", self.test_configuration),
            ("Market Status Tests", self.test_market_status),
            ("Scraper Tests", self.test_scraper_functionality),
            ("Telegram Integration Tests", self.test_telegram_integration),
            ("Scheduler Tests", self.test_scheduler_functionality),
            ("Message Formatting Tests", self.test_message_formatting),
            ("Market Event Tests", self.test_market_events)
        ]
        
        overall_results = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'vietnam_time': datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S'),
            'test_suites': {},
            'summary': {
                'total_suites': len(test_suites),
                'passed_suites': 0,
                'failed_suites': 0,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0
            }
        }
        
        for suite_name, test_function in test_suites:
            logger.info(f"\n📋 Running {suite_name}...")
            
            try:
                suite_results = await test_function()
                overall_results['test_suites'][suite_name] = suite_results
                
                # Update summary
                suite_passed = suite_results.get('passed', 0)
                suite_failed = suite_results.get('failed', 0)
                
                overall_results['summary']['total_tests'] += suite_passed + suite_failed
                overall_results['summary']['passed_tests'] += suite_passed
                overall_results['summary']['failed_tests'] += suite_failed
                
                if suite_failed == 0:
                    overall_results['summary']['passed_suites'] += 1
                    logger.info(f"✅ {suite_name} - All tests passed")
                else:
                    overall_results['summary']['failed_suites'] += 1
                    logger.warning(f"⚠️ {suite_name} - {suite_failed} tests failed")
                    
            except Exception as e:
                logger.error(f"❌ {suite_name} - Suite failed: {e}")
                overall_results['test_suites'][suite_name] = {
                    'error': str(e),
                    'passed': 0,
                    'failed': 1,
                    'tests': []
                }
                overall_results['summary']['failed_suites'] += 1
                overall_results['summary']['failed_tests'] += 1
                overall_results['summary']['total_tests'] += 1
        
        overall_results['end_time'] = datetime.now(timezone.utc).isoformat()
        
        # Print final summary
        self.print_test_summary(overall_results)
        
        return overall_results
    
    async def test_configuration(self) -> Dict[str, Any]:
        """Test configuration management"""
        results = {'tests': [], 'passed': 0, 'failed': 0}
        
        # Test 1: Config manager initialization
        try:
            assert self.config_manager is not None
            assert len(self.config_manager.market_schedules) > 0
            results['tests'].append({'name': 'Config Manager Init', 'status': 'passed'})
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({'name': 'Config Manager Init', 'status': 'failed', 'error': str(e)})
            results['failed'] += 1
        
        # Test 2: Active markets
        try:
            active_markets = self.config_manager.get_active_markets()
            assert len(active_markets) > 0
            results['tests'].append({'name': 'Active Markets', 'status': 'passed', 'count': len(active_markets)})
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({'name': 'Active Markets', 'status': 'failed', 'error': str(e)})
            results['failed'] += 1
        
        # Test 3: Notification schedule
        try:
            schedule = self.config_manager.get_notification_schedule()
            assert len(schedule) > 0
            results['tests'].append({'name': 'Notification Schedule', 'status': 'passed', 'events': len(schedule)})
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({'name': 'Notification Schedule', 'status': 'failed', 'error': str(e)})
            results['failed'] += 1
        
        # Test 4: Telegram validation
        try:
            telegram_valid = self.config_manager.validate_telegram_config()
            if telegram_valid:
                results['tests'].append({'name': 'Telegram Config', 'status': 'passed'})
                results['passed'] += 1
            else:
                results['tests'].append({'name': 'Telegram Config', 'status': 'failed', 'error': 'Missing tokens'})
                results['failed'] += 1
        except Exception as e:
            results['tests'].append({'name': 'Telegram Config', 'status': 'failed', 'error': str(e)})
            results['failed'] += 1
        
        return results
    
    async def test_market_status(self) -> Dict[str, Any]:
        """Test market status detection"""
        results = {'tests': [], 'passed': 0, 'failed': 0}
        
        active_markets = self.config_manager.get_active_markets()
        
        for market_id, market_config in active_markets.items():
            try:
                status = self.config_manager.get_market_status_now(market_id)
                valid_statuses = ['open', 'closed', 'pre_market', 'after_hours', 'closed_weekend']
                
                assert status in valid_statuses
                results['tests'].append({
                    'name': f'Market Status - {market_config.name}',
                    'status': 'passed',
                    'market_status': status
                })
                results['passed'] += 1
                
            except Exception as e:
                results['tests'].append({
                    'name': f'Market Status - {market_config.name}',
                    'status': 'failed',
                    'error': str(e)
                })
                results['failed'] += 1
        
        # Test next market events
        try:
            next_events = self.config_manager.get_next_market_events(3)
            assert len(next_events) > 0
            results['tests'].append({
                'name': 'Next Market Events',
                'status': 'passed',
                'events_count': len(next_events)
            })
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({
                'name': 'Next Market Events',
                'status': 'failed',
                'error': str(e)
            })
            results['failed'] += 1
        
        return results
    
    async def test_scraper_functionality(self) -> Dict[str, Any]:
        """Test coffee price scraper"""
        results = {'tests': [], 'passed': 0, 'failed': 0}
        
        # Test 1: Scraper initialization
        try:
            assert self.scraper is not None
            assert len(self.scraper.markets) > 0
            results['tests'].append({'name': 'Scraper Init', 'status': 'passed'})
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({'name': 'Scraper Init', 'status': 'failed', 'error': str(e)})
            results['failed'] += 1
        
        # Test 2: Market data scraping
        try:
            market_data = self.scraper.scrape_coffee_prices()
            assert market_data is not None
            assert 'markets' in market_data
            
            success_count = market_data.get('success_count', 0)
            total_markets = market_data.get('total_markets', 0)
            
            results['tests'].append({
                'name': 'Market Data Scraping',
                'status': 'passed' if success_count > 0 else 'warning',
                'success_count': success_count,
                'total_markets': total_markets
            })
            
            if success_count > 0:
                results['passed'] += 1
            else:
                results['failed'] += 1
                
        except Exception as e:
            results['tests'].append({
                'name': 'Market Data Scraping',
                'status': 'failed',
                'error': str(e)
            })
            results['failed'] += 1
        
        # Test 3: Individual market scraping
        for coffee_type in ['robusta', 'arabica']:
            try:
                status = self.scraper.get_market_status(coffee_type)
                assert status is not None
                
                results['tests'].append({
                    'name': f'{coffee_type.title()} Market Status',
                    'status': 'passed',
                    'market_status': status
                })
                results['passed'] += 1
                
            except Exception as e:
                results['tests'].append({
                    'name': f'{coffee_type.title()} Market Status',
                    'status': 'failed',
                    'error': str(e)
                })
                results['failed'] += 1
        
        return results
    
    async def test_telegram_integration(self) -> Dict[str, Any]:
        """Test Telegram bot integration"""
        results = {'tests': [], 'passed': 0, 'failed': 0}
        
        # Test 1: Bot initialization
        try:
            if self.config_manager.validate_telegram_config():
                self.telegram_bot = TelegramBot(
                    self.config_manager.telegram.bot_token,
                    self.config_manager.telegram.chat_id
                )
                results['tests'].append({'name': 'Bot Initialization', 'status': 'passed'})
                results['passed'] += 1
                
                # Test 2: Bot connection
                try:
                    connection_test = await self.telegram_bot.test_connection()
                    if connection_test:
                        results['tests'].append({'name': 'Bot Connection', 'status': 'passed'})
                        results['passed'] += 1
                        
                        # Test 3: Chat access
                        try:
                            chat_info = await self.telegram_bot.get_chat_info()
                            if chat_info:
                                results['tests'].append({
                                    'name': 'Chat Access',
                                    'status': 'passed',
                                    'chat_type': chat_info.get('type', 'unknown')
                                })
                                results['passed'] += 1
                            else:
                                results['tests'].append({'name': 'Chat Access', 'status': 'failed', 'error': 'No chat info'})
                                results['failed'] += 1
                                
                        except Exception as e:
                            results['tests'].append({'name': 'Chat Access', 'status': 'failed', 'error': str(e)})
                            results['failed'] += 1
                    else:
                        results['tests'].append({'name': 'Bot Connection', 'status': 'failed', 'error': 'Connection failed'})
                        results['failed'] += 1
                        
                except Exception as e:
                    results['tests'].append({'name': 'Bot Connection', 'status': 'failed', 'error': str(e)})
                    results['failed'] += 1
            else:
                results['tests'].append({'name': 'Bot Initialization', 'status': 'skipped', 'reason': 'No tokens configured'})
                results['tests'].append({'name': 'Bot Connection', 'status': 'skipped', 'reason': 'Bot not initialized'})
                results['tests'].append({'name': 'Chat Access', 'status': 'skipped', 'reason': 'Bot not initialized'})
                
        except Exception as e:
            results['tests'].append({'name': 'Bot Initialization', 'status': 'failed', 'error': str(e)})
            results['failed'] += 1
        
        return results
    
    async def test_scheduler_functionality(self) -> Dict[str, Any]:
        """Test market timing scheduler"""
        results = {'tests': [], 'passed': 0, 'failed': 0}
        
        # Test 1: Scheduler initialization
        try:
            assert self.scheduler is not None
            assert len(self.scheduler.market_schedules) > 0
            results['tests'].append({'name': 'Scheduler Init', 'status': 'passed'})
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({'name': 'Scheduler Init', 'status': 'failed', 'error': str(e)})
            results['failed'] += 1
        
        # Test 2: Market event information
        try:
            next_events = self.scheduler.get_next_market_events()
            assert next_events is not None
            assert 'upcoming_events' in next_events
            
            results['tests'].append({
                'name': 'Market Events Info',
                'status': 'passed',
                'events_count': len(next_events['upcoming_events'])
            })
            results['passed'] += 1
        except Exception as e:
            results['tests'].append({
                'name': 'Market Events Info',
                'status': 'failed',
                'error': str(e)
            })
            results['failed'] += 1
        
        # Test 3: Telegram integration (if available)
        if self.telegram_bot:
            try:
                test_result = await self.scheduler.send_test_message("system_test")
                
                if test_result:
                    results['tests'].append({'name': 'Scheduler-Telegram Integration', 'status': 'passed'})
                    results['passed'] += 1
                else:
                    results['tests'].append({'name': 'Scheduler-Telegram Integration', 'status': 'failed', 'error': 'Test message failed'})
                    results['failed'] += 1
                    
            except Exception as e:
                results['tests'].append({
                    'name': 'Scheduler-Telegram Integration',
                    'status': 'failed',
                    'error': str(e)
                })
                results['failed'] += 1
        else:
            results['tests'].append({
                'name': 'Scheduler-Telegram Integration',
                'status': 'skipped',
                'reason': 'Telegram bot not available'
            })
        
        return results
    
    async def test_message_formatting(self) -> Dict[str, Any]:
        """Test message formatting functionality"""
        results = {'tests': [], 'passed': 0, 'failed': 0}
        
        # Get sample market data
        try:
            market_data = self.scraper.scrape_coffee_prices()
        except:
            market_data = {
                'markets': {
                    'robusta': {'current_price': 4250.0, 'market_status': 'open'},
                    'arabica': {'current_price': 245.5, 'market_status': 'open'}
                },
                'success_count': 2,
                'total_markets': 2
            }
        
        # Test different message types
        message_types = ['market_open', 'market_close', 'pre_market', 'update']
        
        for msg_type in message_types:
            try:
                message = self.scraper.format_market_telegram_message(market_data, msg_type)
                
                assert message is not None
                assert len(message) > 50  # Reasonable message length
                assert 'CÀ PHÊ' in message.upper()
                
                results['tests'].append({
                    'name': f'Message Format - {msg_type}',
                    'status': 'passed',
                    'message_length': len(message)
                })
                results['passed'] += 1
                
            except Exception as e:
                results['tests'].append({
                    'name': f'Message Format - {msg_type}',
                    'status': 'failed',
                    'error': str(e)
                })
                results['failed'] += 1
        
        return results
    
    async def test_market_events(self) -> Dict[str, Any]:
        """Test market event handling"""
        results = {'tests': [], 'passed': 0, 'failed': 0}
        
        # Test market status for different coffee types
        coffee_types = ['robusta', 'arabica']
        
        for coffee_type in coffee_types:
            try:
                status = self.scraper.get_market_status(coffee_type)
                valid_statuses = ['open', 'closed', 'pre_market', 'after_hours', 'closed_weekend']
                
                assert status in valid_statuses
                
                results['tests'].append({
                    'name': f'Market Event - {coffee_type.title()} Status',
                    'status': 'passed',
                    'current_status': status
                })
                results['passed'] += 1
                
            except Exception as e:
                results['tests'].append({
                    'name': f'Market Event - {coffee_type.title()} Status',
                    'status': 'failed',
                    'error': str(e)
                })
                results['failed'] += 1
        
        # Test pre-market time calculation
        try:
            test_open_time = "09:00"
            pre_market_time = self.scheduler.calculate_pre_market_time(test_open_time, 30)
            
            assert pre_market_time == "08:30"
            
            results['tests'].append({
                'name': 'Pre-market Time Calculation',
                'status': 'passed',
                'calculated_time': pre_market_time
            })
            results['passed'] += 1
            
        except Exception as e:
            results['tests'].append({
                'name': 'Pre-market Time Calculation',
                'status': 'failed',
                'error': str(e)
            })
            results['failed'] += 1
        
        return results
    
    def print_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary"""
        logger.info("\n" + "="*60)
        logger.info("🏁 MARKET TIMING SYSTEM TEST SUMMARY")
        logger.info("="*60)
        
        summary = results['summary']
        
        logger.info(f"📊 Overall Results:")
        logger.info(f"   • Test Suites: {summary['passed_suites']}/{summary['total_suites']} passed")
        logger.info(f"   • Individual Tests: {summary['passed_tests']}/{summary['total_tests']} passed")
        logger.info(f"   • Success Rate: {(summary['passed_tests']/summary['total_tests']*100):.1f}%" if summary['total_tests'] > 0 else "   • Success Rate: N/A")
        
        logger.info(f"\n⏰ Test Duration:")
        start_time = datetime.fromisoformat(results['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(results['end_time'].replace('Z', '+00:00'))
        duration = end_time - start_time
        logger.info(f"   • Duration: {duration.total_seconds():.2f} seconds")
        logger.info(f"   • Vietnam Time: {results['vietnam_time']}")
        
        # Detailed suite results
        logger.info(f"\n📋 Suite Details:")
        for suite_name, suite_results in results['test_suites'].items():
            if 'error' in suite_results:
                logger.error(f"   ❌ {suite_name}: ERROR - {suite_results['error']}")
            else:
                passed = suite_results.get('passed', 0)
                failed = suite_results.get('failed', 0)
                total = passed + failed
                status_emoji = "✅" if failed == 0 else "⚠️"
                logger.info(f"   {status_emoji} {suite_name}: {passed}/{total} passed")
        
        # Overall status
        if summary['failed_tests'] == 0:
            logger.info(f"\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        elif summary['passed_tests'] > summary['failed_tests']:
            logger.warning(f"\n⚠️ Most tests passed with some failures. Review failed tests.")
        else:
            logger.error(f"\n❌ Major issues detected. System needs attention.")

async def main():
    """Run the test suite"""
    print("🧪 Market Timing System Test Suite")
    print("=" * 60)
    print("Testing coffee market timing and notification system...")
    print()
    
    try:
        test_suite = MarketTimingTestSuite()
        results = await test_suite.run_all_tests()
        
        # Save detailed results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"\n📄 Detailed results saved to: {results_file}")
        
        # Return appropriate exit code
        if results['summary']['failed_tests'] == 0:
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())