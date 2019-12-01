"""
Module containing the WindShell command loop
"""
import cmd
from functools import wraps

from .calculator import WindCalculator


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

        s = ("""
        RWY HDG [set r]:        {0.runway_heading}º
        MAX XWIND [set x]:      {0.max_crosswind} kts
        MAX TO TAIL [set to]:   {0.max_to_tailwind} kts 
        MAX LDG TAIL [set ldg]: {0.max_ldg_tailwind} kts""".format(self.wind_calc))
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

