#! /usr/local/bin/python3.6

from math import radians
import math
from collections import namedtuple, OrderedDict
import cmd
from string import Template
import logging
from functools import wraps
import argparse

Wind = namedtuple('Wind', ['h_wind', 'x_wind'])

MAX_XWIND = 38
MAX_TO_TAILWIND = 15
MAX_LAND_TAILWIND = 10


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


def catch_and_log_error(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Error in `{func.__name__}(args: {args}, kwargs: {kwargs})`")
            logger.debug(f'Exc info: {str(e)}')
            print(f'Error Occurred!!')
            try:
                stripped_cmd = func.__name__.replace('do_', '')
                print(f"Showing help for {stripped_cmd}")
                args[0].onecmd(f"?{stripped_cmd}")
            except Exception:
                pass
        else:
            return result

    return _wrapper


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
        result = get_crosswind(wind_dir, velocity, self.runway_heading)
        return result

    def calculate_headwind(self, wind_dir, velocity):
        return get_headwind(wind_dir, velocity, self.runway_heading)

    def calculate_max_tailwind_velocity(self, wind_dir, landing=False):
        if landing:
            return get_max_tailwind_velocity(self.max_ldg_tailwind, wind_dir,
                                             self.runway_heading)
        return get_max_tailwind_velocity(self.max_to_tailwind, wind_dir,
                                         self.runway_heading)

    def winds(self, wind_dir, velocity):
        return get_winds(wind_dir, velocity, self.runway_heading)

    def reset_all(self):
        DEFAULTABLE = {
            'max_crosswind': MAX_XWIND,
            'max_to_tailwind': MAX_TO_TAILWIND,
            'max_ldg_tailwind': MAX_LAND_TAILWIND
        }
        for attr, val in DEFAULTABLE.items():
            setattr(self, attr, val)


class WindShell(cmd.Cmd):
    intro = """
            Welcome to the wind calculator!
            
            Enter "help [command]" for more info..
            ======================================
            """
    prompt = '-> '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wind_calc = WindCalculator()

    def __repr__(self):
        return f"WindShell Instance"

    @catch_and_log_error
    def do_r(self, line):
        """
        r(runway) heading

        Show runway if no argument provided, or set runway heading
        """
        if line:
            self.wind_calc.runway_heading = float(line)
        print(f'Runway set to: {self.wind_calc.runway_heading:3.1f}°')

    @catch_and_log_error
    def emptyline(self):
        self.do_show('')

    @catch_and_log_error
    def do_set(self, line):
        """
        set [r[unway] | x[wind] | to[tail] | ldg[tail] value

        set runway, xwind, takeoff tailwind, or landing tailwind limits

        Example:

            `set x 15`

                Set the maximum value for all future crosswind calculations to 15.
        """
        try:
            args = self._parse_line(line)
            props = {
                'r': 'runway_heading',
                'x': 'max_crosswind',
                'to': 'max_to_tailwind',
                'ldg': 'max_ldg_tailwind',
            }
            attr = props[args[0]]
            val = float(args[1])

            setattr(self.wind_calc, attr, val)
        except Exception as e:
            print(f'NO CHANGE OCCURED DUE TO ERROR!!!')
            raise e
        finally:
            print(f"CURRENT SETTINGS")
            self.do_show(None)

    @catch_and_log_error
    def do_show(self, line):
        """
        show

        display the runway heading, max xwind, max takeoff tailwind, max landing tailwind
        """

        s = f"""
        RWY HDG [set r]:        {self.wind_calc.runway_heading}º
        MAX XWIND [set x]:      {self.wind_calc.max_crosswind} kts
        MAX TO TAIL [set to]:   {self.wind_calc.max_to_tailwind} kts 
        MAX LDG TAIL [set ldg]: {self.wind_calc.max_ldg_tailwind} kts
        """
        print(s)

    @catch_and_log_error
    def do_reset(self, line):
        """
        reset

        reset all maximum wind velocities to their original values
        """
        self.wind_calc.reset_all()

    @catch_and_log_error
    def do_x(self, line):
        """x(crosswind) wind_direction velocity
        calculate crosswind component in reference to runway angle"""
        args = self._cast_float(line)
        result = self.wind_calc.calculate_crosswind(*args)
        prefix = 'L' if result < 0 else 'R'
        print(f'{prefix} {abs(result):.1f}kts')

    @catch_and_log_error
    def do_h(self, line):
        """
        h(eadwind) wind_direction velocity

        calculate head/tailwind component in reference to runway

        Example:

            `h 70 20` -> "HEADWIND 6.8 kts"
        """
        args = self._cast_float(line)
        result = self.wind_calc.calculate_headwind(*args)
        flag = 'TAILWIND' if result < 0 else 'HEADWIND'
        print(f'{flag} {abs(result):.1f} kts')

    @catch_and_log_error
    def do_maxt(self, line):
        """
        maxt(ailwind) wind_dir [l]

        Calculate the maximum wind velocity acceptable without exceeding tailwind limit. If `l` is passed,
        used the landing tailwind limitation.
        """
        args = line.split()
        landing_calc = True if args[-1] == 'l' else False
        wind_dir = float(args[0])
        calc_type = f'Landing Calculation (limit: {self.wind_calc.max_ldg_tailwind:1.1f} kts)' if landing_calc \
            else f'Takeoff Calculation (limit: {self.wind_calc.max_to_tailwind:1.1f} kts)'
        try:
            result = self.wind_calc.calculate_max_tailwind_velocity(wind_dir, landing=landing_calc)
            print(calc_type)
            if result == -1:
                raise ValueError
        except ValueError:
            print(
                f'No maximum tailwind from {args[0]}° in reference to runway/angle {self.wind_calc.runway_heading}°'
            )
        else:
            print(
                f'Max Tailwind from {args[0]}° for reference angle {self.wind_calc.runway_heading}° -> {result:.1f}'
            )

    @catch_and_log_error
    def do_winds(self, line):
        """
        winds wind_direction velocity

        Use the current runway heading and calculate both the headwind/tailwind and the crosswind values
        from a given wind direction and velocity.

        Example:

            (runway 360º)

            `winds 40 20`

            Crosswind: R 12.9
            Headwind: 15.3
        """
        args = self._cast_float(line)
        result = self.wind_calc.winds(*args)
        results = self.wind_calc.winds(*args)
        s = Template(
            '\nWind Components for $wind_dir° @ ${velocity}kts from HDG: $hdg\n\n'
            'Crosswind: $l_or_r $xwind\n'
            '${h_or_t}wind: $hwind\n')
        vals = {
            'wind_dir': args[0],
            'velocity': args[1],
            'hdg': self.wind_calc.runway_heading,
            'xwind': round(abs(results.x_wind), 1),
            'hwind': round(abs(results.h_wind), 1),
            'h_or_t': 'Tail' if results.h_wind < 0 else 'Head',
            'l_or_r': 'L' if results.x_wind < 0 else 'R'
        }
        print(s.safe_substitute(vals))

    @catch_and_log_error
    def do_grid(self, line):
        """
        grid wind_dir [l(anding calculation]

        Show max wind with respect to both x-wind and t/h-wind limits for a range of wind
        directions around 'wind_dir'. If 'l' is passed, use the landing limitation for the
        calculations.

            -> r 90 l
            Runway set to: 90º
            -> grid 200 l

                RWY HDG [set r]:        90º
                MAX XWIND [set x]:      38kts
                MAX TO TAIL [set to]:   15kts
                MAX LDG TAIL [set ldg]: 10kts

            Using Landing (10 kts) for calculation

        |   180º  |   190º   |   200º   |   210º  |   220º   |
        ------------------------------------------------------
        |38.0 kts | 38.6 kts | 29.2 kts | 20.0 kts|  15.6 kts|
        """
        args = line.split(' ')
        landing_calc = 'l' in args

        wind_dir = int(args[0])

        ldg_or_head = f'Landing ({self.wind_calc.max_ldg_tailwind} kts)' if landing_calc \
            else f'Takeoff ({self.wind_calc.max_to_tailwind} kts)'
        self.onecmd('show')
        print('{: ^50}'.format(f'Using {ldg_or_head} for calculation'))
        print()

        t_wind_limit = self.wind_calc.max_ldg_tailwind if landing_calc else self.wind_calc.max_to_tailwind
        max_cross = self.wind_calc.max_crosswind
        rwy_hdg = self.wind_calc.runway_heading
        grid = max_wind_grid(wind_dir, 2, t_wind_limit, max_cross, 10, rwy_hdg)

        def make_col(hdg, val, left_most=False):
            first_char = '|' if left_most else ' '
            header = f'{first_char}  {str(hdg).zfill(3)}º  |'
            if isinstance(val, (float, int)):
                val_str = f'{first_char}{val: ^4.1f} kts|'
            else:
                val_str = f"{first_char}{val: ^8}|"
            out = '\n'.join([header, val_str])
            return header, val_str

        headers = []
        val_strs = []

        for i, h_v in enumerate(grid.items()):
            hdg, val = h_v
            out_val = val if val != -1 else 'N/A'
            first = (i == 0)
            header, val_str = make_col(hdg, val, first)
            headers.append(header)
            val_strs.append(val_str)

        hdr_str = ''.join(headers)
        print(hdr_str)
        print('-' * len(hdr_str))
        print(''.join(val_strs))

    @catch_and_log_error
    def do_exit(self, line):
        """
        Quit using this stupid thing.
        """
        return True

    @staticmethod
    def _parse_line(line):
        return tuple(line.split())

    @staticmethod
    def _cast_float(line):
        return tuple(float(arg) for arg in line.split())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='run CLI tool with DEBUG_MODE=TRUE', action='store_true', default=False)

    args = parser.parse_args()

    DEBUG_MODE = args.debug

    log_level = logging.DEBUG if DEBUG_MODE else logging.ERROR

    logger = logging.getLogger('WIND CLI')
    console_handler = logging.StreamHandler()

    log_formatter = logging.Formatter('[{asctime!s}]-[{name!s}]-[{levelname!s}]: {message!s}', style='{')
    console_handler.setFormatter(log_formatter)

    logger.addHandler(console_handler)

    logger.setLevel(log_level)

    shell = WindShell()
    shell.cmdloop()
