"""SpotiSync Core Module

This module provides the core functionality for the SpotiSync application.
It includes configuration management and scheduling capabilities.
"""

from .config import read_create_config
from .scheduler import run_scheduler

__all__ = ['read_create_config', 'run_scheduler']