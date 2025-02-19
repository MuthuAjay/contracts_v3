from functools import wraps
import logging
from typing import Callable, Any, Type, Union, Optional, Dict
import traceback
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categories of errors"""
    DOCUMENT_PROCESSING = "document_processing"
    DATABASE = "database"
    CONTRACT = "contract"
    VERSION_CONTROL = "version_control"
    AGENT = "agent"
    SYSTEM = "system"

@dataclass
class ErrorDetails:
    """Detailed error information"""
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    traceback: str
    context: Dict[str, Any]

class DocumentProcessError(Exception):
    """Exception for document processing errors"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.message = message
        self.severity = severity
        self.category = ErrorCategory.DOCUMENT_PROCESSING
        super().__init__(message)

class VectorDBError(Exception):
    """Exception for database operations"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH):
        self.message = message
        self.severity = severity
        self.category = ErrorCategory.DATABASE
        super().__init__(message)

class ContractError(Exception):
    """Exception for contract-related operations"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.message = message
        self.severity = severity
        self.category = ErrorCategory.CONTRACT
        super().__init__(message)

class VersionControlError(Exception):
    """Exception for version control operations"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH):
        self.message = message
        self.severity = severity
        self.category = ErrorCategory.VERSION_CONTROL
        super().__init__(message)

class AgentError(Exception):
    """Exception for agent-related operations"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        self.message = message
        self.severity = severity
        self.category = ErrorCategory.AGENT
        super().__init__(message)

def handle_errors(
    error_type: Union[Type[Exception], tuple] = Exception,
    default_return: Any = None,
    logging_level: int = logging.ERROR,
    error_category: Optional[ErrorCategory] = None
) -> Callable:
    """
    Decorator for handling errors in functions
    
    Args:
        error_type: Type of error to catch
        default_return: Value to return on error
        logging_level: Level for logging
        error_category: Category of error
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                error_details = ErrorHandler.create_error_details(
                    e, error_category or ErrorCategory.SYSTEM
                )
                ErrorHandler.log_error(error_details)
                return default_return
        return wrapper
    return decorator

class ErrorHandler:
    """Centralized error handling"""

    _error_history: Dict[str, ErrorDetails] = {}

    @classmethod
    def create_error_details(
        cls,
        error: Exception,
        category: ErrorCategory
    ) -> ErrorDetails:
        """
        Create detailed error information
        
        Args:
            error: Exception that occurred
            category: Error category
            
        Returns:
            ErrorDetails object
        """
        severity = (
            error.severity if hasattr(error, 'severity')
            else ErrorSeverity.MEDIUM
        )
        
        return ErrorDetails(
            message=str(error),
            category=category,
            severity=severity,
            timestamp=datetime.now(),
            traceback=traceback.format_exc(),
            context={
                'error_type': error.__class__.__name__,
                'module': error.__class__.__module__
            }
        )

    @classmethod
    def log_error(cls, error_details: ErrorDetails) -> None:
        """
        Log error with appropriate level and store in history
        
        Args:
            error_details: Details of the error
        """
        error_id = f"{error_details.timestamp.strftime('%Y%m%d_%H%M%S')}_{error_details.category.value}"
        cls._error_history[error_id] = error_details
        
        log_message = (
            f"Error in {error_details.category.value}: {error_details.message}\n"
            f"Severity: {error_details.severity.value}\n"
            f"Context: {error_details.context}\n"
            f"Traceback:\n{error_details.traceback}"
        )
        
        if error_details.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_details.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_details.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    @classmethod
    def get_error_history(
        cls,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None
    ) -> Dict[str, ErrorDetails]:
        """
        Get filtered error history
        
        Args:
            category: Optional category filter
            severity: Optional severity filter
            
        Returns:
            Dictionary of filtered errors
        """
        filtered = cls._error_history.copy()
        
        if category:
            filtered = {
                k: v for k, v in filtered.items()
                if v.category == category
            }
            
        if severity:
            filtered = {
                k: v for k, v in filtered.items()
                if v.severity == severity
            }
            
        return filtered

    @classmethod
    def clear_error_history(cls) -> None:
        """Clear error history"""
        cls._error_history.clear()

    @staticmethod
    def safe_execute(
        func: Callable,
        error_category: ErrorCategory,
        default_return: Any = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Safely execute a function with error handling
        
        Args:
            func: Function to execute
            error_category: Category for potential errors
            default_return: Value to return on error
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Function result or default value
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_details = ErrorHandler.create_error_details(e, error_category)
            ErrorHandler.log_error(error_details)
            return default_return

class RetryHandler:
    """Handles retry logic for operations"""

    @staticmethod
    def retry_operation(
        func: Callable,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Callable:
        """
        Decorator for retrying operations
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            delay: Initial delay between retries
            backoff_factor: Factor to increase delay
            exceptions: Exceptions to catch
            
        Returns:
            Decorated function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        retry_delay = delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} "
                            f"for {func.__name__} after {retry_delay}s"
                        )
                        time.sleep(retry_delay)
                    
            # Log final failure
            logger.error(
                f"All {max_retries} retries failed for {func.__name__}: "
                f"{str(last_exception)}"
            )
            raise last_exception
            
        return wrapper

    @classmethod
    def retry_with_fallback(
        cls,
        func: Callable,
        fallback_func: Callable,
        max_retries: int = 3,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry operation with fallback
        
        Args:
            func: Primary function to execute
            fallback_func: Fallback function
            max_retries: Maximum retries
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        try:
            retry_func = cls.retry_operation(
                func, max_retries=max_retries
            )
            return retry_func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Falling back to alternative for {func.__name__}: {str(e)}"
            )
            return fallback_func(*args, **kwargs)