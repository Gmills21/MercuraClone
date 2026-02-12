"""
PostHog analytics utility for backend event tracking.
"""

import posthog
from app.config import settings
from loguru import logger
from typing import Dict, Any, Optional

# Initialize PostHog
if settings.posthog_api_key:
    posthog.project_api_key = settings.posthog_api_key
    posthog.host = settings.posthog_host
    logger.info("PostHog initialized for backend tracking.")
else:
    # Disable PostHog if no API key is provided (prevents crashes)
    posthog.disabled = True
    logger.warning("PostHog API key missing. Backend tracking disabled.")

def capture_event(
    distinct_id: str,
    event_name: str,
    properties: Optional[Dict[str, Any]] = None,
    groups: Optional[Dict[str, Any]] = None
):
    """
    Capture an event in PostHog.
    
    Args:
        distinct_id: Unique identifier for the user or organization.
        event_name: Name of the event (e.g., 'quote_created').
        properties: Additional metadata for the event.
        groups: Group identifiers (e.g., {'organization': 'org_123'}).
    """
    try:
        posthog.capture(
            distinct_id=distinct_id,
            event=event_name,
            properties=properties or {},
            groups=groups or {}
        )
    except Exception as e:
        logger.error(f"Failed to capture PostHog event '{event_name}': {e}")

def identify_user(distinct_id: str, properties: Dict[str, Any]):
    """Identify a user with specific properties."""
    try:
        posthog.identify(distinct_id, properties)
    except Exception as e:
        logger.error(f"Failed to identify user in PostHog: {e}")

def group_identify(group_type: str, group_key: str, properties: Dict[str, Any]):
    """Identify a group (e.g., an organization) with specific properties."""
    try:
        posthog.group_identify(group_type, group_key, properties)
    except Exception as e:
        logger.error(f"Failed to identify group in PostHog: {e}")
