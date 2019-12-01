"""
Library module for wind calculations
"""

__version__ = '1.0.0'

from math import radians
import math
from collections import namedtuple, OrderedDict
import cmd
from string import Template
import logging
from functools import wraps
import argparse

Wind = namedtuple('Wind', ['h_wind', 'x_wind'])

# TODO: Add RCAM value mapping
# TODO: Add max x_wind value to grid function header

MAX_XWIND = 38
MAX_TO_TAILWIND = 15
MAX_LAND_TAILWIND = 10


class Direction:
    PRECISION = 1
    def __init__(self, initial):
        self._value = initial
        
    def __repr__(self):
        return f'Direction({self.value})'
       
    @staticmethod
    def normalize(value):
        return value % 360
        
    @property
    def value(self):
        return round(self.normalize(self._value), self.PRECISION)
        
    @value.setter
    def value(self, val):
        if not isinstance(val, (float, int)):
            raise TypeError('val must be int or float')
        self._value = val
        
    def theta(self, other):
        """
        Return the number of degrees clockwise from object's `value` attribute to 
        `other`
        
        Example:
            
            >>> Direction(90).theta(91)
            Direction(1.0)
            >>> Direction(90).theta(89)
            Direction(359.0)
        """
        if isinstance(other, Direction):
            other = other._value
        return Direction(float((other - self._value) % 360))
         
    def __add__(self, other):
        if isinstance(other, Direction):
            other = other._value
        return Direction(self._value + other)
        
    def __sub__(self, other):
        if isinstance(other, Direction):
            other = other._value
        return self + Direction(-1 * other)
        
    def __eq__(self, other):
        """
        Return True if other == self within the precision of `Direction`
        
        Example:
            
            >>> Direction.PRECISION = 1
            >>> Direction(90.04) == 90
            True
            
        """
        if not isinstance(other, Direction):
            other = Direction(other)
        return other.value == self.value
        


class WindVector:
    def __init__(self, direction, strength, strength_unit='kts'):
        self.direction = Direction(direction)
        self.strength = strength
        self.strength_unit = strength_unit
        
    def __repr__(self):
        return f'Wind: {self.direction.value}° @ {self.strength:.1f}{self.strength_unit}'
        
    def to_tuple(self):
        return (self.direction.value, self.strength)
        

def get_winds(wind, velocity, runway=360):
    """Return Wind(h_wind, x_wind) tuple."""
    runway %= 360
    wind %= 360
    theta = (runway - wind) % 360
    x_wind = get_crosswind(wind, velocity, runway)
    h_wind = get_headwind(wind, velocity, runway)
    return Wind(h_wind, x_wind)


def get_headwind(wind, velocity, runway=360):
    """Return headwind component. Positive for headwind, negative for tailwind."""
    runway %= 360
    wind %= 360
    theta = (runway - wind) % 360
    return math.cos(radians(theta)) * velocity


def get_crosswind(wind, velocity, runway=360):
    """Return crosswind component. Positive for right component, Negative for left component."""
    runway %= 360
    wind %= 360
    theta = (runway - wind) % 360
    return math.sin(radians(theta)) * velocity * -1


def get_max_crosswind_velocity(max_component, wind_dir, runway=360):
    """
    Return the maximum velocity for a given wind relative to a runway. Return -1 if ZeroDivisionError occurs and the
    value is incalculable.
    """
    theta = abs(runway - wind_dir) % 360
    try:
        return abs(max_component / math.sin(radians(theta)))
    except ZeroDivisionError:
        return -1


def get_max_tailwind_velocity(max_component, wind_dir, runway=360):
    if not 90 < abs((runway - wind_dir) % 360) < 270:
        return -1
    else:
        try:
            return abs(max_component / math.cos(radians(runway - wind_dir)))
        except ZeroDivisionError:
            return -1


def max_wind_grid(wind_hdg,
                  num,
                  max_tail=-1,
                  max_cross=-1,
                  increment=10,
                  runway_hdg=360):
    try:
        find_xwind = True if max_cross >= 0 else False
        find_twind = True if max_tail >= 0 else False
        assert any([find_twind, find_xwind])
    except AssertionError as e:
        raise ValueError('must provide either max_tail or max_cross')
    left_bucket = (wind_hdg - (num * increment)) % 360
    right_bucket = ((wind_hdg) + (num * increment)) % 360
    buckets = []
    idx = left_bucket - increment
    idx %= 360
    while idx != right_bucket:
        idx += increment
        idx %= 360
        buckets.append(idx)

    out = OrderedDict()

    for theta in buckets:

        if find_xwind:
            max_xwind_velocity = get_max_crosswind_velocity(max_cross, theta, runway_hdg)
            if not find_twind:
                out[theta] = max_xwind_velocity
                continue
        else:
            max_xwind_velocity = -1

        if find_twind:
            max_twind_velocity = get_max_tailwind_velocity(max_tail, theta, runway_hdg)
            if not find_xwind:
                out[theta] = max_twind_velocity
                continue
        else:
            max_twind_velocity = -1

        # both requested both calculable
        if max_twind_velocity != -1 and max_xwind_velocity != -1:
            out[theta] = min(max_xwind_velocity, max_twind_velocity)
            continue
        else:
            out[theta] = max(max_twind_velocity, max_xwind_velocity)

    return out


# TODO: make headings Direction instances with property access methods
