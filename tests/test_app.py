"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt, beide Instanz-Typen, abgebrochene Läufe,
Randwerte, Würfel-Knopf, Permalink-Grenzen, Sweeps auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import idastar_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(idastar_step=1, **state):
    at = AppTest.from_file(APP, default_timeout=120)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if idastar_step != 1:
        at.select_slider(key="idastar_step").set_value(idastar_step).run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def test_default_run_has_no_exception_and_shows_four_metrics():
    at = _run()
    _ok(at)
    assert {"Speicher-Verhältnis", "Expansions-Faktor", "Iterationen", "Status"} <= {m.label for m in at.metric}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["network_select"] == p["network"] and at.session_state["cap_select"] == p["cap"]
    assert at.metric


@pytest.mark.parametrize("step", [1, 2, 3])
def test_every_step_runs_for_both_networks(step):
    for network in ("grid", "trap"):
        at = _run(network_select=network, idastar_step=step)
        _ok(at)
        assert at.get("plotly_chart") and at.session_state["idastar_step"] == step


@pytest.mark.parametrize("step", [2, 3])
def test_capped_runs_render_in_every_step(step):
    at = _run(cap_select=10000, idastar_step=step)
    _ok(at)
    status = next(m.value for m in at.metric if m.label == "Status")
    assert status == "Abbruch"
    factor = next(m.value for m in at.metric if m.label == "Expansions-Faktor")
    assert factor.startswith("≥")


@pytest.mark.parametrize("kw", [
    dict(side_slider=C.SIDE_MIN), dict(side_slider=9), dict(obstacle_slider=C.OBSTACLE_MIN), dict(obstacle_slider=C.OBSTACLE_MAX),
    dict(cap_select=C.CAPS[0]), dict(cap_select=C.CAPS[-1], side_slider=7),
])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_dice_button_changes_the_seed():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old


def test_permalink_values_are_clamped_and_invalid_caps_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=120)
    at.query_params["side"] = "9999"
    at.query_params["obstacle"] = "9999"
    at.query_params["cap"] = "12345"
    at.query_params["network"] = "trap"
    at.run()
    _ok(at)
    assert at.session_state["side_slider"] == C.SIDE_MAX and at.session_state["obstacle_slider"] == C.OBSTACLE_MAX
    assert at.session_state["cap_select"] == C.DEFAULT_CAP and at.session_state["network_select"] == "trap"


def test_sidebar_hides_grid_only_controls_for_the_trap_network():
    at = _run(network_select="trap")
    _ok(at)
    assert not any(s.key == "side_slider" for s in at.slider)
    assert not any(s.key == "cap_select" for s in at.select_slider)


def test_changing_the_instance_while_on_step_two_does_not_crash():
    at = _run(idastar_step=2, side_slider=9)
    _ok(at)
    at.session_state["side_slider"] = C.SIDE_MIN
    at.run()
    _ok(at)
    at.session_state["network_select"] = "trap"
    at.run()
    _ok(at)


@pytest.mark.parametrize("metric", ["factor", "memory_ratio", "iterations", "capped"])
def test_sweeps_run_on_demand_for_every_metric(metric):
    at = _run(side_slider=6, sweep_metric=metric)
    at.selectbox(key="sweep_select").set_value("obstacle_pct").run()
    next(b for b in at.button if b.key == "sweep_start").click().run()
    _ok(at)
    assert at.get("plotly_chart")


def test_footer_and_grenzen_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Speicher zu akzeptablen Zeitkosten" in m.value for m in at.markdown)
