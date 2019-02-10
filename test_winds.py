import pytest

from winds import (get_headwind, get_crosswind, get_winds, Wind, get_max_crosswind_velocity,
                   get_max_tailwind_velocity, max_wind_grid)


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
        70: 29.24,
        80: 57.59,
        90: -1,
        100: 57.59,
        110: 29.24
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
    max_tail = 1000
    result_dict = max_wind_grid(ref_hdg, num, max_tail=max_tail, max_cross=max_cross, increment=10)
    assert all([
        expected[k] == pytest.approx(result_dict[k], rel=.01) for k in expected
    ])
    assert expected.keys() == result_dict.keys()
