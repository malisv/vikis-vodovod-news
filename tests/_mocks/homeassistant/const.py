from enum import Enum


class Platform(str, Enum):
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"