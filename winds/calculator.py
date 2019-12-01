"""
Module containing the WindCalculator class
"""
import winds


# TODO: make headings Direction instances with property access methods
class WindCalculator:

    def __init__(self):
        self._runway_heading = 000
        self._max_ldg_tailwind = 0
        self._max_to_tailwind = 0
        self._max_crosswind = 0
        self.reset_all()

    @property
    def runway_heading(self):
        return round(self._runway_heading % 360, 1)

    @runway_heading.setter
    def runway_heading(self, val):
        self._runway_heading = float(val)

    @property
    def max_crosswind(self):
        return self._max_crosswind

    @max_crosswind.setter
    def max_crosswind(self, val):
        self._max_crosswind = float(val)

    @property
    def max_to_tailwind(self):
        return self._max_to_tailwind

    @max_to_tailwind.setter
    def max_to_tailwind(self, val):
        self._max_to_tailwind = float(val)

    @property
    def max_ldg_tailwind(self):
        return self._max_ldg_tailwind

    @max_ldg_tailwind.setter
    def max_ldg_tailwind(self, val):
        self._max_ldg_tailwind = float(val)

    def calculate_crosswind(self, wind_dir, velocity):
        result = winds.get_crosswind(wind_dir, velocity, self.runway_heading)
        return result

    def calculate_headwind(self, wind_dir, velocity):
        return winds.get_headwind(wind_dir, velocity, self.runway_heading)

    def calculate_max_tailwind_velocity(self, wind_dir, landing=False):
        if landing:
            return winds.get_max_tailwind_velocity(self.max_ldg_tailwind, wind_dir,
                                             self.runway_heading)
        return winds.get_max_tailwind_velocity(self.max_to_tailwind, wind_dir,
                                         self.runway_heading)

    def winds(self, wind_dir, velocity):
        return winds.get_winds(wind_dir, velocity, self.runway_heading)

# TODO: max wind components should be passed in
    def reset_all(self):
        DEFAULTABLE = {
            'max_crosswind': winds.MAX_XWIND,
            'max_to_tailwind': winds.MAX_TO_TAILWIND,
            'max_ldg_tailwind': winds.MAX_LAND_TAILWIND
        }
        for attr, val in DEFAULTABLE.items():
            setattr(self, attr, val)

