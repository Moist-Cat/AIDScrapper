import functools
import logging
import logging.config
from typing import List, Callable, Type

from aids.app.settings import LOGGERS

logging.config.dictConfig(LOGGERS)

def logged(methods: List[str] = None) -> Callable:
    """Decorator to log certain methods of each class while giving
    each clas its own logger."""
    def log_class(cls) -> Type:
        cls.logger = logging.getLogger("user_info." + cls.__qualname__)
        cls.logger_err = logging.getLogger("audit." + cls.__qualname__)

        def log_method(method):

            @functools.wraps(method)
            def wrapper(cls, *args, **kwargs) -> Callable:
                cls.logger.info("Starting method...")

                ret_val = method(cls, *args, **kwargs)

                cls.logger.info("Concluding method...")

                return ret_val
            return wrapper

        for method in methods:
            # Here we decorate every method listen in the "methods" argument.
            setattr(cls, method, log_method(getattr(cls, method)))
        return cls
    return log_class
