from unittest.mock import Mock
from unittest import mock

import pytest

from winds import (get_headwind, get_crosswind, get_winds, Wind, get_max_crosswind_velocity, Direction,
                   get_max_tailwind_velocity, max_wind_grid, WindCalculator, WindShell, catch_and_log_error)


@pytest.fixture('class')
def mock_wind_calc_shell():
    mock_calculator = Mock()

    windshell = WindShell()

    windshell.wind_calc = mock_calculator

    return windshell


@pytest.mark.parametrize('_input, expected', [
    ((120, 20, 90), Wind(17.3, 10)),
    ((60, 20, 90), Wind(17.3, -10)),
    ((30, 20, 360), Wind(17.3, 10)),
    ((-10, 20, -40), Wind(x_wind=10, h_wind=17.3)),
    ((150, 20, 360), Wind(-17.3, 10)),
    ((210, 20, 360), Wind(-17.3, -10)),
    ((30, 20), Wind(17.3, 10)),
    ((360, 20, 360), Wind(20, 0))
], ids=[
    'qtr hd wind right',
    'qtr hd wind left',
    'qtr hd wind left RWY: 360',
    'negative rwy neg wind',
    'qtr right tail wind',
    'qtr left tail wind',
    'qtr right hdwind no runway entered',
    'no wind'
])
def test_get_winds_return_appropriate_values_and_positive_xwinds(_input, expected):
    result = get_winds(*_input)
    assert result.h_wind == pytest.approx(expected.h_wind, abs=.05)
    assert result.x_wind == pytest.approx(expected.x_wind, abs=.05)


@pytest.mark.parametrize('max_xwind, wind_dir, runway, expected', [
    (20, 120, 90, 40),
    (20, 330, 360, 40),
    (20, 360, 150, 40),
    (20, 360, 210, 40),
    (20, -30, None, 40),
    (20, 360, 360, -1)
])
def test_get_max_crosswind_velocity(max_xwind, wind_dir, runway, expected):
    if runway is None:
        runway = 360
    assert get_max_crosswind_velocity(max_xwind, wind_dir, runway) == pytest.approx(expected, abs=.05)


@pytest.mark.parametrize('max_tailwind, wind_dir, runway', [
    (10, 90, 360),
    (10, 270, 360),
    (10, 90, 90),
    (10, 90, 80),
    (10, 340, 360),
])
def test_get_max_tailwind_returns_neg_one_for_less_than_ninety(max_tailwind, wind_dir, runway):
    assert -1 == get_max_tailwind_velocity(max_tailwind, wind_dir, runway)


@pytest.mark.parametrize('max_tailwind, wind_dir, runway, expected', [
    (10, 120, 360, 20),
    (10, 240, 360, 20),
    (10, 180, 360, 10)
])
def test_get_max_tailwind_returns_correct_velocity(max_tailwind, wind_dir, runway, expected):
    result = get_max_tailwind_velocity(max_tailwind, wind_dir, runway)
    assert result == pytest.approx(expected, abs=.05)


@pytest.mark.parametrize('ref_hdg, num, max_tail, max_cross, expected_hdgs', [
    (360, 2, 10, 10, [340, 350, 0, 10, 20]),
    (90, 3, 10, 10, [60, 70, 80, 90, 100, 110, 120])
])
def test_max_wind_grid_makes_proper_wind_buckets(ref_hdg, num, max_tail, max_cross, expected_hdgs):
    result = max_wind_grid(ref_hdg, num, max_tail=max_tail, max_cross=max_cross)
    assert sorted(expected_hdgs) == sorted(list(result.keys()))
    assert result


@pytest.mark.parametrize('ref_hdg, num, max_cross, expected', [
    (90, 2, 10, {
        70: 10.64,
        80: 10.15,
        90: 10,
        100: 10.15,
        110: 10.64
    }),
    (360, 2, 10, {
        340: 29.24,
        350: 57.59,
        0: -1,
        10: 57.59,
        20: 29.24
    })
])
def test_max_wind_grid_makes_proper_wind_returns_when_xwind_exceeded(ref_hdg, num, max_cross, expected):
    result_dict = max_wind_grid(ref_hdg, num, max_cross=max_cross, increment=10)
    assert all([
        expected[k] == pytest.approx(result_dict[k], rel=.01) for k in expected
    ]), result_dict
    assert expected.keys() == result_dict.keys()


@pytest.mark.parametrize('ref_hdg, num, max_tail, expected', [
    (360, 1, 10, {
        350: -1,
        000: -1,
        10: -1
    }),
])
def test_max_wind_grid_returns_neg_one_for_each_incalculable_tail_wind(ref_hdg, num, max_tail, expected):
    results = max_wind_grid(ref_hdg, num, max_tail=max_tail, increment=10)
    assert all([
        expected[k] == pytest.approx(results[k], rel=.01) for k in expected
    ]), results
    assert list(expected.keys()) == list(results.keys())


@pytest.mark.parametrize('ref_hdg, num, max_tail, max_cross, runway, increment, expected', [
    (90, 1, 10, 20, 360, 10, {
        80: 20.31,
        90: 20,
        100: 20.31,
    }),
    (150, 1, 15, 15, 360, 20, {
        130: 19.58,
        150: 17.32,
        170: 15.23,
    }),
    (135, 1, 10, 10, 360, 45, {
        90: 10,
        135: 14.14,
        180: 10,
    }),
    (180, 2, 5, 500, 90, 10, {
        160: 532.09,
        170: 507.7,
        180: 500,
        190: 28.79,
        200: 14.62
    }),
], ids=['xwind limited', 'twind limited', 'range limited by both', 'severely twind limited'])
def test_max_wind_grid_returns_for_both_crosswind_and_tailwind(ref_hdg, num, max_tail, max_cross, runway, increment,
                                                               expected):
    results = max_wind_grid(ref_hdg, num, max_tail=max_tail, max_cross=max_cross, increment=increment,
                            runway_hdg=runway)
    assert all([
        expected[k] == pytest.approx(results[k], rel=.01) for k in expected
    ]), results
    assert list(expected.keys()) == list(results.keys())


@pytest.mark.parametrize('ref_hdg, num, max_tail, max_cross, runway_hdg, increment, expected', [
    (90, 3, 10, -1, 360, 10, {
        60: -1,
        70: -1,
        80: -1,
        90: -1,
        100: 57.59,
        110: 29.24,
        120: 20
    }),

], ids=['only tail calc'])
def test_max_wind_grid_returns_when_only_one_max_wind_specified(ref_hdg, num, max_tail, max_cross, runway_hdg,
                                                                increment,
                                                                expected):
    results = max_wind_grid(ref_hdg, num, max_tail, max_cross, increment, runway_hdg)
    assert all([
        expected[k] == pytest.approx(results[k], rel=.01) for k in expected
    ]), results
    assert list(expected.keys()) == list(results.keys())


class TestWindCalculator:
    @pytest.mark.parametrize('property, setter_val, expected_on_call', [
        ('max_ldg_tailwind', '50', 50.0),
        ('max_to_tailwind', 4, 4.0),
        ('max_crosswind', 25.5, 25.5)
    ])
    def test_wind_calculator_properties(self, property, setter_val, expected_on_call):
        wind_calc = WindCalculator()
        setattr(wind_calc, property, setter_val)
        assert expected_on_call == getattr(wind_calc, property)

    @pytest.mark.parametrize('attr, val, glob', [
        ('max_crosswind', 20, 'MAX_XWIND'),
        ('max_to_tailwind', 5, 'MAX_TO_TAILWIND'),
        ('max_ldg_tailwind', 15, 'MAX_LAND_TAILWIND')
    ])
    def test_wind_calculator_resets_to_module_defaults(self, attr, val, glob):
        with mock.patch('winds.' + glob, val):
            wind_calc = WindCalculator()
            assert val == getattr(wind_calc, attr)
            new_val = val ** 2
            setattr(wind_calc, attr, new_val)
            assert getattr(wind_calc, attr) == new_val
            wind_calc.reset_all()
            assert val == getattr(wind_calc, attr)
            
            
        
class TestDirection:
    def test_can_init(self):
        direction = Direction(0)
     
    @pytest.mark.parametrize('val, exp', [
        (0, 0),
        (90, 90),
        (540, 180),
        (-540, 180)
        ])   
    def test_normalize(self, val, exp):
        assert Direction.normalize(val) == exp
     
    @pytest.mark.parametrize('val, exp', [
        (360.1, 0.1),
        (90.45, 90.5),
        ])
    def test_value_rounding(self, val, exp):
        assert Direction(val).value == exp
        
    def test_can_add(self):
        d3 = Direction(90) + Direction(90)
        assert d3.value == 180          
        
    def test_can_subtract(self):
        d4 = Direction(0) - Direction(90)
        assert d4.value == 270
        
        d4 -= 180
        
        assert d4.value == 90
        
    @pytest.mark.parametrize('d, d2, exp', [
        (90, 91, 1.0),
        (90, 89, 359.0),
        (0, 10, 10.0),
        (0, 350, 350.0)
        ])
    def test_theta(self, d, d2, exp):
        assert Direction(d).theta(d2).value == exp
        
    def test_equality(self):
        d = Direction(90.1)
        
        assert d == Direction(90.1)
        assert d == 90.1
        assert d != 90.0
        assert d == 90.06
        assert d == 90.14
        
        
        
        
            
            
class TestWindVector:
    pass


@pytest.mark.usefixtures('mock_wind_calc_shell')
class TestWindShell:

    @pytest.mark.parametrize('headwind_return, expected_flag', [
        (0, 'H'),
        (-10, 'T'),
        (10, 'H'),
    ], ids=['Zero Wind -> H flag', 'Tailwind -> T flag', 'Headwind -> H flag'])
    def test_do_h_has_proper_flag(self, headwind_return, expected_flag, mock_wind_calc_shell, capsys):
        flags = {
            'H': 'HEADWIND',
            'T': 'TAILWIND'
        }
        line = ' '.join([str(0), str(headwind_return)])
        shell = mock_wind_calc_shell
        shell.wind_calc.calculate_headwind.return_value = headwind_return
        shell.do_h(line)
        shell.wind_calc.calculate_headwind.assert_called_with(0, headwind_return)
        out, err = capsys.readouterr()
        assert flags.get(expected_flag) in out

    def test_do_reset_calls_reset_with_no_args(self, mock_wind_calc_shell):
        shell = mock_wind_calc_shell
        shell.wind_calc.reset_all.return_value = None
        shell.onecmd('reset')
        shell.wind_calc.reset_all.assert_called_with()

