"""Rauchtests der Streamlit-Oberfläche per AppTest: Standard, jedes Preset, Randgrößen, Permalink, Auswahl, Experimente auf Abruf, Exakt-Knopf mit deaktiviertem Zustand."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import hub_constants as C
from hub_presets import PRESET_KEYS

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"


def _run(setup=None, timeout=300):
    at = AppTest.from_file(str(APP), default_timeout=timeout)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    if setup is not None:
        setup(at)
        at.run()
        assert not at.exception, [e.value for e in at.exception]
    return at


def _apply(at, p):
    for key, state_key in PRESET_KEYS.items():
        at.session_state[state_key] = p[key]


def _metric(at, label):
    return [m.value for m in at.metric if m.label == label]


def _texts(at):
    return [e.value for e in list(at.success) + list(at.warning) + list(at.info) + list(at.error)]


def _button(at, key):
    return next(b for b in at.button if b.key == key)


def test_default_renders_and_names_the_headline_numbers():
    at = _run()
    assert any("um **4,5 %** teurer" in m.value for m in at.markdown)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_renders(name):
    at = _run(lambda a: _apply(a, C.PRESETS[name]))
    assert not at.error


def test_extreme_sizes_render():
    for vals in ((("n_slider", C.N_MIN), ("p_slider", C.P_MIN), ("alpha_slider", 0)),
                 (("n_slider", C.N_MAX), ("p_slider", C.P_MAX), ("alpha_slider", 100))):
        def setup(at, vals=vals):
            for key, value in vals:
                at.session_state[key] = value
        at = _run(setup)
        assert not at.error


def test_selection_must_have_exactly_p_hubs():
    at = _run()
    at.multiselect(key="pick_multi").set_value([0])
    at.run()
    assert not at.exception and any("Wählen Sie genau 2 Knoten" in t for t in _texts(at))
    at.multiselect(key="pick_multi").set_value([0, 1])
    at.run()
    assert not at.exception and _metric(at, "Gesamtkosten")


def test_selection_resets_when_p_changes():
    at = _run()
    at.multiselect(key="pick_multi").set_value([0, 1])
    at.run()
    at.sidebar.slider(key="p_slider").set_value(3)
    at.run()
    assert not at.exception and len(at.multiselect(key="pick_multi").value) == 3


def test_permalink_settings_are_loaded_clamped_and_snapped_to_the_grid():
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.query_params["n"] = "999"
    at.query_params["alpha"] = "47"
    at.run()
    assert not at.exception
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX and at.sidebar.slider(key="alpha_slider").value == 50


def test_invalid_permalink_values_fall_back_to_the_defaults():
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.query_params["alpha"] = "viel"
    at.query_params["seed"] = "x"
    at.run()
    assert not at.exception and at.sidebar.slider(key="alpha_slider").value == C.DEFAULT_ALPHA and at.sidebar.number_input(key="seed_input").value == C.DEFAULT_SEED


def test_experiments_run_on_demand(monkeypatch):
    import hub_evaluation as ev
    d_o, a_o = ev.distribution, ev.alpha_series
    monkeypatch.setattr(ev, "distribution", lambda p: d_o(p, seeds=C.SWEEP_SEEDS[:3]))
    monkeypatch.setattr(ev, "alpha_series", lambda p: a_o(p, grid=(0, 50, 100)))
    at = _run()
    for key in ("alpha_start", "dist_start"):
        _button(at, key).click().run()
        assert not at.exception, key
    assert any("Die bloße Neuzuordnung der Kunden schließt im Mittel nur" in c.value for c in at.caption)


def test_exact_button_is_disabled_for_large_nets_and_works_for_small_ones():
    at = _run()
    assert _button(at, "exact_start").disabled
    at = _run(lambda a: _apply(a, C.PRESETS["🧮 Kleinnetz mit exaktem Optimum"]), timeout=90)
    assert not _button(at, "exact_start").disabled
    _button(at, "exact_start").click().run(timeout=90)
    assert not at.exception and any("trifft das Optimum" in t for t in _texts(at))


def test_source_has_explicit_chart_keys_and_locked_axes():
    app = APP.read_text(encoding="utf-8")
    assert all(re.search(r"plotly_chart\(.*key=", line) for line in app.splitlines() if "st.plotly_chart(" in line)
    viz = (ROOT / "hub_visualization.py").read_text(encoding="utf-8")
    assert viz.count("_base(fig") >= 4 and "def lock_axes" in viz
