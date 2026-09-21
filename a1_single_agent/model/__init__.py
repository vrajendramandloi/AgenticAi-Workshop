import sys

# Prevent __pycache__ bytecode generation in this project
sys.dont_write_bytecode = True

from .location_object import LocationObject

__all__ = ["LocationObject"]
