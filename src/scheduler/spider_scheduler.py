"""
Spider Scheduler using APScheduler for running Scrapy spiders on schedule.

This module provides scheduled execution of:
- RBA Tables spider: Weekly on Saturday at 01:00 UTC+10
- XR API Currencies spider: Daily at 01:00 UTC+10
"""

import logging
import os
import signal
import sys
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Timezone for Australia/Brisbane (UTC+10)
TIMEZONE = pytz.timezone('Australia/Brisbane')

# Lock to prevent concurrent spider execution
spider_lock = Lock()

# Track running spiders
running_spiders: Dict[str, bool] = {
    'rba_tables': False,
    'xrapi-currencies': False
}


class SpiderScheduler:
    """Main scheduler class for managing Scrapy spider execution."""
    
    def __init__(self):
        self.scheduler = BlockingScheduler(timezone=TIMEZONE)
        self.project_dir = Path(__file__).parent.parent / 'econdata'
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.shutdown()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def get_scrapy_settings(self) -> Dict:
        """Get Scrapy project settings."""
        # Change to the Scrapy project directory
        original_dir = os.getcwd()
        try:
            os.chdir(self.project_dir)
            settings = get_project_settings()
            return settings
        finally:
            os.chdir(original_dir)
            
    def run_spider(self, spider_name: str, spider_kwargs: dict = None) -> None:
        """
        Run a single spider with proper error handling and concurrency control.
        
        Args:
            spider_name: Name of the spider to run ('rba_tables', 'xrapi-currencies', 'abs_gfs')
            spider_kwargs: Additional arguments to pass to the spider
        """
        # Check if spider is already running
        if running_spiders.get(spider_name, False):
            logger.warning(f"Spider '{spider_name}' is already running, skipping this execution")
            return
            
        # Acquire lock to prevent concurrent executions
        if not spider_lock.acquire(blocking=False):
            logger.warning(f"Could not acquire lock for spider '{spider_name}', another spider may be running")
            return
            
        try:
            running_spiders[spider_name] = True
            logger.info(f"Starting spider: {spider_name}")
            
            # Change to the Scrapy project directory
            original_dir = os.getcwd()
            os.chdir(self.project_dir)
            
            try:
                # Use subprocess to run scrapy command - more reliable for scheduled execution
                import subprocess
                
                # Build the scrapy command
                cmd = ['scrapy', 'crawl', spider_name]
                
                # Add spider arguments if provided
                if spider_kwargs:
                    for key, value in spider_kwargs.items():
                        cmd.extend(['-a', f'{key}={value}'])
                
                # Set up environment with correct Python path
                env = os.environ.copy()
                # Add src/econdata directory to PYTHONPATH so econdata package can be found
                econdata_parent_dir = str(self.project_dir)
                if 'PYTHONPATH' in env:
                    env['PYTHONPATH'] = f"{econdata_parent_dir}:{env['PYTHONPATH']}"
                else:
                    env['PYTHONPATH'] = econdata_parent_dir
                
                logger.debug(f"Running command: {' '.join(cmd)}")
                logger.debug(f"Working directory: {self.project_dir}")
                logger.debug(f"PYTHONPATH: {env.get('PYTHONPATH', 'Not set')}")
                
                # Run the spider as a subprocess
                result = subprocess.run(
                    cmd,
                    cwd=self.project_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
                
                if result.returncode == 0:
                    logger.info(f"Spider '{spider_name}' completed successfully")
                    if result.stdout:
                        logger.debug(f"Spider output: {result.stdout}")
                else:
                    logger.error(f"Spider '{spider_name}' failed with return code {result.returncode}")
                    if result.stderr:
                        logger.error(f"Spider error: {result.stderr}")
                    raise RuntimeError(f"Spider execution failed: {result.stderr}")
                
            except Exception as e:
                logger.error(f"Error running spider '{spider_name}': {str(e)}", exc_info=True)
                raise
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            logger.error(f"Failed to run spider '{spider_name}': {str(e)}", exc_info=True)
        finally:
            running_spiders[spider_name] = False
            spider_lock.release()
            
    def run_rba_spider(self):
        """Run the RBA Tables spider."""
        logger.info("Scheduled execution: RBA Tables spider")
        self.run_spider('rba_tables')
        
    def run_xrapi_spider(self):
        """Run the XR API Currencies spider."""
        logger.info("Scheduled execution: XR API Currencies spider")
        self.run_spider('xrapi-currencies')
        
    def setup_schedules(self):
        """Setup the scheduled jobs."""
        # RBA Tables spider: Weekly on Saturday at 01:00 UTC+10
        self.scheduler.add_job(
            func=self.run_rba_spider,
            trigger=CronTrigger(
                day_of_week='sat',  # Saturday
                hour=1,             # 01:00
                minute=0,           # :00
                timezone=TIMEZONE
            ),
            id='rba_tables_weekly',
            name='RBA Tables Weekly Spider',
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
            coalesce=True     # Combine missed executions
        )
        
        # XR API Currencies spider: Daily at 01:00 UTC+10
        self.scheduler.add_job(
            func=self.run_xrapi_spider,
            trigger=CronTrigger(
                hour=1,             # 01:00
                minute=0,           # :00
                timezone=TIMEZONE
            ),
            id='xrapi_currencies_daily',
            name='XR API Currencies Daily Spider',
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
            coalesce=True     # Combine missed executions
        )
        
        logger.info("Scheduled jobs configured:")
        logger.info("- RBA Tables: Weekly on Saturday at 01:00 UTC+10")
        logger.info("- XR API Currencies: Daily at 01:00 UTC+10")
        
    def start(self):
        """Start the scheduler."""
        logger.info("Starting Spider Scheduler...")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Scrapy project directory: {self.project_dir}")
        
        # Verify the Scrapy project directory exists
        if not self.project_dir.exists():
            raise FileNotFoundError(f"Scrapy project directory not found: {self.project_dir}")
            
        # Setup scheduled jobs
        self.setup_schedules()
        
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
            self.shutdown()
            
    def shutdown(self):
        """Gracefully shutdown the scheduler."""
        logger.info("Shutting down scheduler...")
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown complete")
        
    def run_spider_now(self, spider_name: str, spider_kwargs: dict = None):
        """
        Run a spider immediately (for testing purposes).
        
        Args:
            spider_name: Name of the spider to run
            spider_kwargs: Additional arguments to pass to the spider
        """
        logger.info(f"Running spider '{spider_name}' immediately")
        if spider_name == 'rba_tables':
            self.run_rba_spider()
        elif spider_name == 'xrapi-currencies':
            self.run_xrapi_spider()
        elif spider_name == 'abs_gfs':
            self.run_spider(spider_name, spider_kwargs)
        else:
            logger.error(f"Unknown spider: {spider_name}")
            

def main():
    """Main entry point for the scheduler."""
    scheduler = SpiderScheduler()
    
    # Handle command line arguments for immediate execution
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'test-rba':
            scheduler.run_spider_now('rba_tables')
        elif command == 'test-xrapi':
            scheduler.run_spider_now('xrapi-currencies')
        elif command == 'start':
            scheduler.start()
        else:
            print("Usage:")
            print("  python spider_scheduler.py start      - Start the scheduler")
            print("  python spider_scheduler.py test-rba   - Test RBA spider immediately")
            print("  python spider_scheduler.py test-xrapi - Test XR API spider immediately")
    else:
        # Default to starting the scheduler
        scheduler.start()


if __name__ == '__main__':
    main()