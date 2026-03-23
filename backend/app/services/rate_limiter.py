from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import HTTPException, Request
import logging

logger = logging.getLogger(__name__)

# In-memory storage for rate limiting (IP -> (attempt_count, window_start))
# In production, use Redis for distributed rate limiting
rate_limit_storage: Dict[str, Tuple[int, datetime]] = {}


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(ip: str, max_attempts: int = 5, window_minutes: int = 15) -> None:
    """
    Check if the IP has exceeded rate limit.
    Raises HTTPException if limit exceeded.
    
    Args:
        ip: Client IP address
        max_attempts: Maximum attempts allowed (default: 5)
        window_minutes: Time window in minutes (default: 15)
    """
    now = datetime.utcnow()
    
    if ip in rate_limit_storage:
        attempts, window_start = rate_limit_storage[ip]
        
        # Check if window has expired
        if now - window_start > timedelta(minutes=window_minutes):
            # Reset the window
            rate_limit_storage[ip] = (1, now)
            return
        
        # Check if limit exceeded
        if attempts >= max_attempts:
            time_remaining = timedelta(minutes=window_minutes) - (now - window_start)
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            raise HTTPException(
                status_code=429,
                detail=f"Too many attempts. Please try again in {minutes_remaining} minutes."
            )
        
        # Increment attempts
        rate_limit_storage[ip] = (attempts + 1, window_start)
    else:
        # First attempt
        rate_limit_storage[ip] = (1, now)


def reset_rate_limit(ip: str) -> None:
    """Reset rate limit for an IP (e.g., after successful login)."""
    if ip in rate_limit_storage:
        del rate_limit_storage[ip]
