import logging
import os
from rich.logging import RichHandler
from rich import print as pprint

def _logger(flag: str = "", format: str = ""):
    if format == "" or format is None:
        format = "%(levelname)s|%(name)s| %(message)s"

    # message
    logger = logging.getLogger(__name__)

    if os.environ.get(flag) is not None:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    # # create formatter
    # # add formatter to ch
    # formatter = logging.Formatter(format)
    # ch.setFormatter(formatter)

    # # add ch to logger
    # logger.addHandler(ch)
    handler = RichHandler(log_time_format="")
    logger.addHandler(handler)
    return logger


# message
# export LOG_LEVEL=true
logger = _logger("LOG_LEVEL")


def resolve_env_variable(value: str, field_name: str = "field") -> str:
    """
    Resolve environment variable from a string value.

    If the value is in the format ${VAR_NAME}, it will be replaced with
    the value of the environment variable VAR_NAME.

    Args:
        value: The string value that may contain ${VAR_NAME}
        field_name: Name of the field (for error messages)

    Returns:
        The resolved value (either the env var value or original value)

    Raises:
        ValueError: If the environment variable is not set

    Example:
        >>> os.environ['DB_PASSWORD'] = 'secret123'
        >>> resolve_env_variable('${DB_PASSWORD}')
        'secret123'
        >>> resolve_env_variable('plaintext')
        'plaintext'
    """
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        env_value = os.getenv(env_var)
        if env_value is None:
            raise ValueError(
                f"Environment variable '{env_var}' for {field_name} is not set"
            )
        return env_value
    return value
