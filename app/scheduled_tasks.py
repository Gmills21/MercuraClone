"""
Scheduled Tasks Configuration
Setup automated backups and monitoring collection.

Usage:
    from app.scheduled_tasks import setup_scheduled_tasks
    setup_scheduled_tasks()
"""

import os
from datetime import datetime
from typing import Callable
import threading
import time

from loguru import logger

# Try to import APScheduler, fall back to simple threading if not available
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    # Use logger only if already configured
    import logging
    logging.warning("APScheduler not installed. Using simple threading scheduler.")


class SimpleScheduler:
    """Simple threading-based scheduler as fallback."""
    
    def __init__(self):
        self.jobs = []
        self.running = False
        self.thread = None
    
    def add_job(self, func: Callable, trigger: str, **kwargs):
        """Add a job to the scheduler."""
        if trigger == "cron":
            hour = kwargs.get("hour", 0)
            minute = kwargs.get("minute", 0)
            self.jobs.append({
                "func": func,
                "hour": hour,
                "minute": minute,
                "last_run": None
            })
    
    def start(self):
        """Start the scheduler."""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """Main scheduler loop."""
        while self.running:
            now = datetime.now()
            for job in self.jobs:
                if (now.hour == job["hour"] and 
                    now.minute == job["minute"] and
                    (job["last_run"] is None or 
                     job["last_run"].date() != now.date() or
                     job["last_run"].hour != now.hour)):
                    try:
                        job["func"]()
                        job["last_run"] = now
                    except Exception as e:
                        logger.error(f"Scheduled job failed: {e}")
            
            time.sleep(30)  # Check every 30 seconds
    
    def shutdown(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)


# Global scheduler instance
_scheduler = None


def setup_scheduled_tasks():
    """
    Setup all scheduled tasks.
    
    Scheduled tasks:
    - Daily backup at 2 AM
    - Hourly metrics collection
    - Daily cleanup of old backups
    - Daily cleanup of expired tokens/invites
    """
    global _scheduler
    
    if APSCHEDULER_AVAILABLE:
        _scheduler = BackgroundScheduler()
    else:
        _scheduler = SimpleScheduler()
    
    # Daily backup at 2 AM
    _scheduler.add_job(
        _run_daily_backup,
        trigger="cron",
        hour=2,
        minute=0,
        id="daily_backup",
        replace_existing=True
    )
    
    # Hourly metrics collection
    _scheduler.add_job(
        _collect_metrics,
        trigger="cron",
        minute=0,
        id="hourly_metrics",
        replace_existing=True
    )
    
    # Daily cleanup at 3 AM
    _scheduler.add_job(
        _run_daily_cleanup,
        trigger="cron",
        hour=3,
        minute=0,
        id="daily_cleanup",
        replace_existing=True
    )
    
    _scheduler.start()
    logger.info("Scheduled tasks started")
    
    return _scheduler


def shutdown_scheduled_tasks():
    """Shutdown the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        logger.info("Scheduled tasks stopped")


def _run_daily_backup():
    """Run daily backup task."""
    logger.info("Running scheduled daily backup...")
    try:
        from app.services.backup_service import run_scheduled_backup
        result = run_scheduled_backup()
        if result["success"]:
            logger.info(f"Daily backup completed: {result['backup']['filename']}")
        else:
            logger.error(f"Daily backup failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Daily backup task error: {e}")


def _collect_metrics():
    """Collect system metrics."""
    try:
        from app.services.monitoring_service import monitoring_service
        metrics = monitoring_service.collect_metrics()
        logger.debug(f"Metrics collected: CPU {metrics.cpu_percent:.1f}%, "
                    f"Memory {metrics.memory_percent:.1f}%")
    except Exception as e:
        logger.error(f"Metrics collection error: {e}")


def _run_daily_cleanup():
    """Run daily cleanup tasks."""
    logger.info("Running daily cleanup tasks...")
    
    # Cleanup old backups
    try:
        from app.services.backup_service import backup_service
        result = backup_service.cleanup_old_backups()
        logger.info(f"Backup cleanup: {result['deleted_count']} old backups removed")
    except Exception as e:
        logger.error(f"Backup cleanup error: {e}")
    
    # Cleanup expired password reset tokens
    try:
        from app.services.password_reset_service import PasswordResetService
        deleted = PasswordResetService.cleanup_expired_tokens()
        logger.info(f"Password reset cleanup: {deleted} expired tokens removed")
    except Exception as e:
        logger.error(f"Token cleanup error: {e}")
    
    # Cleanup expired invitations
    try:
        from app.services.team_invitation_service import TeamInvitationService
        expired = TeamInvitationService.cleanup_expired_invitations()
        logger.info(f"Invitation cleanup: {expired} expired invitations marked")
    except Exception as e:
        logger.error(f"Invitation cleanup error: {e}")
    
    # Cleanup old rate limit entries (in-memory, will auto-expire)
    logger.info("Daily cleanup completed")


# For manual execution
if __name__ == "__main__":
    print("Running scheduled tasks manually...")
    _run_daily_backup()
    _collect_metrics()
    _run_daily_cleanup()
    print("Done!")
