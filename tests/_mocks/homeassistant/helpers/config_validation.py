from unittest.mock import MagicMock

import voluptuous as vol


def positive_int(value):
    value = int(value)
    if value <= 0:
        raise vol.Invalid("Must be positive")
    return value