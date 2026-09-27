"""Presets: vollständig, in den Grenzen, auf dem Raster der Regler, und jedes Beispiel zeigt, was sein Name verspricht (die Zahlen selbst belegt test_claims.py)."""

import pytest

import hub_constants as C
import hub_evaluation as ev
import hub_presets as P

KEYS = set(P.PRESET_KEYS)


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 5
    assert all(C.PRESET_HELP[name].strip() for name in C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_values_are_inside_the_bounds_and_on_the_slider_grid(name):
    p = C.PRESETS[name]
    for key, state_key in P.PRESET_KEYS.items():
        spec = P.SETTING_SPECS[state_key]
        assert spec.lo <= p[key] <= spec.hi, (name, key)
        if state_key in P.STEPS:
            assert (p[key] - spec.lo) % P.STEPS[state_key] == 0, (name, key)


def test_setting_specs_have_room_to_move():
    assert all(spec.lo < spec.hi for spec in P.SETTING_SPECS.values())


def test_each_preset_shows_the_effect_its_name_promises():
    a = {name: ev.analyse(ev.Params(**p)) for name, p in C.PRESETS.items()}
    assert a["🚫 Kein Rabatt"]["gap"] > a["🗺️ Standardnetz"]["gap"] > a["💸 Starker Rabatt"]["gap"] == pytest.approx(0.0)
    assert set(a["☝️ Ein Hub"]["naive"].hubs) == set(a["☝️ Ein Hub"]["joint"].hubs)
    small = ev.Params(**C.PRESETS["🧮 Kleinnetz mit exaktem Optimum"])
    assert ev.exact_allowed(small) and a["🧮 Kleinnetz mit exaktem Optimum"]["gap"] > 15


def test_the_standard_preset_is_the_default_configuration():
    assert C.PRESETS["🗺️ Standardnetz"] == {"n": C.DEFAULT_N, "p": C.DEFAULT_P, "alpha": C.DEFAULT_ALPHA, "seed": C.DEFAULT_SEED}
    assert ev.Params() == ev.Params(**C.PRESETS["🗺️ Standardnetz"])
