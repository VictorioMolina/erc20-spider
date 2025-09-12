"""
Centralised logging system for the ERC-20 Spider Bot.
Implements singleton pattern for consistent logging across modules.
"""

import sys
import logging
from typing import Optional

from utils.config import LOG_LEVEL, LOG_FORMAT

# todo - Check


class Logger:
    """
    Singleton logger providing consistent logging throughout the application.
    Ensures all modules use the same logging configuration and format.
    """
    
    _instance: Optional["Logger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> "Logger":
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialise logger if not already configured."""
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure logging with professional formatting and output."""
        self._logger = logging.getLogger("eth_spider_bot")
        
        # Convert string log level to logging constant
        numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        self._logger.setLevel(numeric_level)

        # Prevent duplicate handlers if logger already exists
        if self._logger.handlers:
            return

        # Create console handler with professional formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        # Professional formatter with timestamps and context
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        # Add colour coding for different log levels
        self._add_colour_support(console_handler)
        
        self._logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False

    def _add_colour_support(self, handler: logging.StreamHandler) -> None:
        """Add colour support for different log levels (Unix systems)."""
        try:
            import colorama
            from colorama import Fore, Style
            colorama.init(autoreset=True)
            
            class ColourFormatter(logging.Formatter):
                """Custom formatter with colour support."""
                
                COLOURS = {
                    'DEBUG': Fore.CYAN,
                    'INFO': Fore.GREEN,
                    'WARNING': Fore.YELLOW,
                    'ERROR': Fore.RED,
                    'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
                }

                def format(self, record):
                    # Apply colour to log level
                    log_colour = self.COLOURS.get(record.levelname, '')
                    record.levelname = f"{log_colour}{record.levelname}{Style.RESET_ALL}"
                    return super().format(record)
            
            colour_formatter = ColourFormatter(LOG_FORMAT)
            handler.setFormatter(colour_formatter)
            
        except ImportError:
            # Colour support not available, use standard formatter
            pass

    def get_logger(self) -> logging.Logger:
        """Retrieve the configured logger instance."""
        if self._logger is None:
            self._setup_logger()
        return self._logger

    def set_level(self, level: str) -> None:
        """
        Update logging level for all handlers.
        
        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if self._logger:
            numeric_level = getattr(logging, level.upper(), logging.INFO)
            self._logger.setLevel(numeric_level)
            
            for handler in self._logger.handlers:
                handler.setLevel(numeric_level)

    def add_file_handler(self, filename: str, level: str = "INFO") -> None:
        """
        Add file logging handler for persistent log storage.
        
        Args:
            filename: Path to log file
            level: Logging level for file handler
        """
        if not self._logger:
            self._setup_logger()
            
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        file_handler = logging.FileHandler(filename, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        
        # Use clean format for file logs (no colours)
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        self._logger.addHandler(file_handler)

    def log_system_info(self) -> None:
        """Log system startup information."""
        import sys
        import platform
        
        logger = self.get_logger()
        logger.info("=" * 60)
        logger.info("ERC-20 SPIDER BOT - INITIALISING")
        logger.info("=" * 60)
        logger.info(f"Python Version: {sys.version.split()[0]}")
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        logger.info(f"Log Level: {LOG_LEVEL}")
        logger.info("System ready for blockchain monitoring")
        logger.info("=" * 60)

    def log_performance_metrics(self, events_processed: int, 
                              uptime_seconds: float) -> None:
        """
        Log performance metrics for monitoring system health.
        
        Args:
            events_processed: Total events processed since startup
            uptime_seconds: System uptime in seconds
        """
        logger = self.get_logger()
        
        # Calculate events per second
        eps = events_processed / uptime_seconds if uptime_seconds > 0 else 0
        
        # Convert uptime to human readable format
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        logger.info(f"Performance Metrics - Events: {events_processed}, "
                   f"Uptime: {uptime_str}, Rate: {eps:.2f} events/sec")
