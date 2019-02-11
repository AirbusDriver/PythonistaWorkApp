from math import degrees, radians
import math
from collections import namedtuple
import cmd
from string import Template

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

    out = {}

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


class WindCalculator():
    def __init__(self):
        self._runway_heading = 000
        self.max_crosswind = MAX_XWIND
        self.max_to_tailwind = MAX_TO_TAILWIND
        self.max_ldg_tailwind = MAX_LAND_TAILWIND

    @property
    def runway_heading(self):
        return round(self._runway_heading % 360, 1)

    @runway_heading.setter
    def runway_heading(self, val):
        self._runway_heading = float(val)

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


class WindShell(cmd.Cmd):
    intro = ('Welcome to the wind calculator, \n'
             'Enter "help" for more info.\n'
             '=================================')
    prompt = '-> '

    def preloop(self):
        self.wind_calc = WindCalculator()

    def do_r(self, line):
        """r(runway) heading

        Show runway if no argument provided, or set runway heading"""
        if line:
            self.wind_calc.runway_heading = float(line)
        print(f'Runway set to: {self.wind_calc.runway_heading:3.1f}°')

    def emptyline(self):
        self.do_show(None)

    def do_set(self, line):
        """set [r[unway] | x[wind] | to[tail] | ldg[tail] value
        set runway, xwind, takeoff tailwind, or landing tailwind limits
        """
        args = self._parse_line(line)
        props = {
            'r': 'runway_heading',
            'x': 'max_crosswind',
            'to': 'max_to_tailwind',
            'ldg': 'max_ldg_tailwind',
        }
        try:
            attr = props[args[0]]
            val = args[1]
        except IndexError:
            print(f'invalid args')
            self.onecmd('?set')
        except KeyError:
            print(f'invalid entry, nothing changed')
            self.do_show('')
        else:
            try:
                setattr(self.wind_calc, attr, val)
            except Exception as e:
                print(f'ERROR!! {e}')
            finally:
                print(f'NO CHANGES MADE')
                self.do_show('')

    def do_show(self, line):
        """show

        display the runway heading, max xwind, max takeoff tailwind, max landing tailwind"""

        s = f"""
        RWY HDG [set r]:        {self.wind_calc.runway_heading}º
        MAX XWIND [set x]:      {self.wind_calc.max_crosswind}kts
        MAX TO TAIL [set to]:   {self.wind_calc.max_to_tailwind}kts 
        MAX LDG TAIL [set ldg]:  {self.wind_calc.max_ldg_tailwind}kts
        """
        print(s)

    def do_x(self, line):
        """x(crosswind) wind_direction velocity
        calculate crosswind component in reference to runway angle"""
        args = self._cast_float(line)
        try:
            result = self.wind_calc.calculate_crosswind(*args)
        except Exception as e:
            print(e)
            print(f'args -> {args}')
        else:
            prefix = 'L' if result < 0 else 'R'
            print(f'{prefix} {abs(result):.1f}kts')

    def do_h(self, line):
        """h(eadwind) wind_direction velocity
        calculate head/tailwind component in reference to runway"""
        args = self._cast_float(line)
        try:
            result = self.wind_calc.calculate_headwind(*args)
        except Exception as e:
            print(e)
            print(f'args -> {args}')
        else:
            flag = 'TAILWIND' if result < 0 else 'HEADWIND'
            print(f'{flag} {abs(result):.1f}kts')

    def do_maxt(self, line):
        """maxt(ailwind) wind_dir [l]"""
        try:
            args = line.split()
            landing_calc = True if args[-1] == 'l' else False
            wind_dir = float(args[0])
            calc_type = f'Landing Calculation (limit: {self.wind_calc.max_ldg_tailwind:1.1f} kts)' if landing_calc \
                else f'Takeoff Calculation (limit: {self.wind_calc.max_to_tailwind:1.1f} kts)'
        except IndexError as e:
            self.onecmd('?maxt')
            return
        try:
            result = self.wind_calc.calculate_max_tailwind_velocity(wind_dir, landing=landing_calc)
            print(calc_type)
            if result == -1:
                raise ValueError
        except ValueError as e:
            print(
                f'No maximum tailwind from {args[0]}° in reference to runway/angle {self.wind_calc.runway_heading}°'
            )
        except Exception as e:
            print(e)
            print(f'args -> {args}')
        else:
            print(
                f'Max Tailwind from {args[0]}° for reference angle {self.wind_calc.runway_heading}° -> {result:.1f}'
            )

    def do_winds(self, line):
        """winds wind_direction velocity"""
        args = self._cast_float(line)
        try:
            result = self.wind_calc.winds(*args)
        except Exception as e:
            print(e)
            print(f'args -> {args}')
        else:
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

    @staticmethod
    def _parse_line(line):
        return tuple(line.split())

    @staticmethod
    def _cast_float(line):
        return tuple(float(arg) for arg in line.split())


if __name__ == '__main__':
    shell = WindShell()
    shell.cmdloop()
