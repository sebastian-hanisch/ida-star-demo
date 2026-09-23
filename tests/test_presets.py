"""Presets: Vollständigkeit, gültige Werte, Expansions-Faktor bleibt in der gemessenen Spannweite über die 5 festen
Sweep-Instanzen (vollständig deterministisch), IDA* ist in jedem gelösten Preset optimal."""

import pytest

import idastar_constants as C
import idastar_evaluation as ev
import idastar_presets as P


def _settings(p, seed=None):
    return ev.Settings(network=p["network"], side=p["side"], obstacle_pct=p["obstacle_pct"], seed=p["seed"] if seed is None else seed, cap=p["cap"])


def test_every_preset_has_help_and_a_band():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_EXPECTED_BANDS)
    assert len(C.PRESETS) == 6
    for name, p in C.PRESETS.items():
        assert set(p) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]


def test_preset_values_are_valid():
    for p in C.PRESETS.values():
        assert p["network"] in P.NETWORKS and p["cap"] in C.CAPS
        assert C.SIDE_MIN <= p["side"] <= C.SIDE_MAX and C.OBSTACLE_MIN <= p["obstacle_pct"] <= C.OBSTACLE_MAX


def test_default_preset_equals_the_default_settings():
    assert _settings(C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_factor_stays_in_its_measured_band_and_solved_runs_are_optimal(name):
    p = C.PRESETS[name]
    lo, hi = C.PRESET_EXPECTED_BANDS[name]
    seeds = C.SWEEP_SEEDS if p["network"] == "grid" else (p["seed"],)
    for seed in seeds:
        a = ev.analyse(_settings(p, seed=seed))
        assert lo <= a.factor <= hi, (seed, a.factor)
        if a.solved:
            assert abs(a.gap) < 1e-9


def test_small_cap_preset_is_capped_on_every_sweep_instance():
    p = C.PRESETS["Kleine Obergrenze (Abbruch)"]
    assert all(not ev.analyse(_settings(p, seed=s)).solved for s in C.SWEEP_SEEDS)


def test_the_seed_35_instance_of_the_size_ten_preset_is_still_solvable():
    assert ev.analyse(_settings(C.PRESETS["Größe 10 (Obergrenze wird knapp)"])).solved


def test_many_obstacles_preset_is_much_cheaper_than_the_open_field_preset():
    open_field = ev.run_config(_settings(C.PRESETS["Offenes Feld (viele Transpositionen)"]))
    many = ev.run_config(_settings(C.PRESETS["Viele Hindernisse (40 %)"]))
    assert open_field["factor"] > 5 * many["factor"]


def test_bounds_and_permalink_constants():
    assert P.bounds("side_slider") == (C.SIDE_MIN, C.SIDE_MAX) and P.bounds("seed_input") == (0, C.SEED_MAX)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)
    assert C.DEFAULT_CAP in C.CAPS


def test_network_and_cap_permalink_casters():
    assert P._network_from_str("trap") == "trap"
    with pytest.raises(ValueError):
        P._network_from_str("nope")
    assert P.SETTING_SPECS["cap_select"].caster("100000") == 100000
    with pytest.raises(ValueError):
        P.SETTING_SPECS["cap_select"].caster("12345")
