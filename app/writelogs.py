import functools
import logging
import logging.config
from typing import List, Callable, Type

from aids.app.settings import LOGGERS

logging.config.dictConfig(LOGGERS)

def logged(cls) -> Callable:
    """Decorator to log certain methods of each class while giving
    each clas its own logger."""
    cls.logger = logging.getLogger("user_info." + cls.__qualname__)
    cls.logger_err = logging.getLogger("audit." + cls.__qualname__)

    return cls
