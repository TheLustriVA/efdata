#!/usr/bin/env python3
"""
Startup script for the Spider Scheduler with daemon capabilities.
"""

import argparse
import atexit
import os
import signal
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from scheduler.spider_scheduler import SpiderScheduler


class SchedulerDaemon:
    """Daemon wrapper for the Spider Scheduler."""
    
    def __init__(self, pidfile: str = None):
        self.pidfile = pidfile or str(Path(__file__).parent / 'scheduler.pid')
        self.scheduler = None
        
    def daemonize(self):
        """Daemonize the current process."""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit first parent
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)
            
        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit second parent
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)
            
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Write pidfile
        atexit.register(self.delete_pid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w') as f:
            f.write(f"{pid}\n")
            
    def delete_pid(self):
        """Delete the PID file."""
        try:
            os.remove(self.pidfile)
        except OSError:
            pass
            
    def start(self, daemon: bool = False):
        """Start the scheduler."""
        if daemon:
            # Check for existing pidfile
            if os.path.exists(self.pidfile):
                with open(self.pidfile, 'r') as f:
                    pid = int(f.read().strip())
                try:
                    os.kill(pid, 0)  # Check if process exists
                    print(f"Scheduler already running with PID {pid}")
                    return
                except OSError:
                    # Process doesn't exist, remove stale pidfile
                    os.remove(self.pidfile)
                    
            print("Starting scheduler as daemon...")
            self.daemonize()
            
        # Start the scheduler
        self.scheduler = SpiderScheduler()
        self.scheduler.start()
        
    def stop(self):
        """Stop the scheduler daemon."""
        if not os.path.exists(self.pidfile):
            print("Scheduler is not running")
            return
            
        try:
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
                
            # Terminate the process
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to terminate
            for _ in range(30):  # Wait up to 30 seconds
                try:
                    os.kill(pid, 0)
                    time.sleep(1)
                except OSError:
                    break
            else:
                # Force kill if still running
                os.kill(pid, signal.SIGKILL)
                
            # Remove pidfile
            os.remove(self.pidfile)
            print(f"Scheduler stopped (PID {pid})")
            
        except (OSError, ValueError) as e:
            print(f"Error stopping scheduler: {e}")
            
    def status(self):
        """Check scheduler status."""
        if not os.path.exists(self.pidfile):
            print("Scheduler is not running")
            return False
            
        try:
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
                
            # Check if process exists
            os.kill(pid, 0)
            print(f"Scheduler is running (PID {pid})")
            return True
            
        except (OSError, ValueError):
            print("Scheduler is not running (stale pidfile)")
            os.remove(self.pidfile)
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Spider Scheduler Management')
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'status', 'foreground', 'test-rba', 'test-xrapi'],
                      help='Command to execute')
    parser.add_argument('--pidfile', help='PID file location')
    
    args = parser.parse_args()
    
    daemon = SchedulerDaemon(args.pidfile)
    
    if args.command == 'start':
        daemon.start(daemon=True)
    elif args.command == 'foreground':
        daemon.start(daemon=False)
    elif args.command == 'stop':
        daemon.stop()
    elif args.command == 'restart':
        daemon.stop()
        time.sleep(2)
        daemon.start(daemon=True)
    elif args.command == 'status':
        daemon.status()
    elif args.command == 'test-rba':
        scheduler = SpiderScheduler()
        scheduler.run_spider_now('rba_tables')
        print("Test command completed, exiting...")
        sys.exit(0)
    elif args.command == 'test-xrapi':
        scheduler = SpiderScheduler()
        scheduler.run_spider_now('xrapi-currencies')
        print("Test command completed, exiting...")
        sys.exit(0)


if __name__ == '__main__':
    main()