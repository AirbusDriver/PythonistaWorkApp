import pytest

from winds import (get_headwind, get_crosswind, get_winds, Wind, get_max_crosswind_velocity,
                   get_max_tailwind_velocity)


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
def test_get_max_tailwind_returns_neg_one_for_lessthan_ninety(max_tailwind, wind_dir, runway):
    assert -1 == get_max_tailwind_velocity(max_tailwind, wind_dir, runway)


@pytest.mark.parametrize('max_tailwind, wind_dir, runway, expected', [
    (10, 120, 360, 20),
    (10, 240, 360, 20),
    (10, 180, 360, 10)
])
def test_get_max_tailwind_returns_correct_velocity(max_tailwind, wind_dir, runway, expected):
    result = get_max_tailwind_velocity(max_tailwind, wind_dir, runway)
    assert result == pytest.approx(expected, abs=.05)
