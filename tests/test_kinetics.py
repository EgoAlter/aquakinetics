import numpy as np
import pytest
from kinetics import (
    ammonia_production_rate,
    monod_nitrification_rate,
    simulate_ammonia_curve,
    health_status,
)

# ── ammonia_production_rate ──────────────────────────────────────────────────

def test_ammonia_production_rate_formula():
    expected = 80 * 0.03 * 1000 / 24 / 600
    assert ammonia_production_rate(80, 600) == pytest.approx(expected)

def test_ammonia_production_rate_zero_feed():
    assert ammonia_production_rate(0, 600) == 0.0

def test_ammonia_production_rate_linear_feed():
    base = ammonia_production_rate(80, 600)
    assert ammonia_production_rate(160, 600) == pytest.approx(2 * base)

def test_ammonia_production_rate_linear_volume():
    base = ammonia_production_rate(80, 600)
    assert ammonia_production_rate(80, 1200) == pytest.approx(0.5 * base)

# ── monod_nitrification_rate ─────────────────────────────────────────────────

def test_monod_zero_substrate():
    assert monod_nitrification_rate(0, 25, 7.5) == 0.0

def test_monod_half_saturation():
    # temp=30 → temp_factor=1; pH=7.8 → ph_factor=1; nh3=Ks=1.0 → Monod term=0.5
    # rate = 0.80 * 1 * 1 * 0.5 = 0.40
    assert monod_nitrification_rate(1.0, 30, 7.8) == pytest.approx(0.40, abs=1e-9)

def test_monod_increases_with_temperature():
    assert monod_nitrification_rate(2, 30, 7.8) > monod_nitrification_rate(2, 20, 7.8)

def test_monod_ph_optimum_at_7_8():
    optimal = monod_nitrification_rate(5, 30, 7.8)
    assert optimal > monod_nitrification_rate(5, 30, 6.0)
    assert optimal > monod_nitrification_rate(5, 30, 9.0)

def test_monod_ph_gaussian_symmetry():
    delta = 0.8
    assert monod_nitrification_rate(5, 30, 7.8 - delta) == pytest.approx(
        monod_nitrification_rate(5, 30, 7.8 + delta), abs=1e-9
    )

# ── simulate_ammonia_curve ───────────────────────────────────────────────────

def test_simulate_returns_expected_keys():
    result = simulate_ammonia_curve(80, 600, 25, 7.5)
    assert "hour" in result and "nh3_mg_l" in result

def test_simulate_correct_length():
    result = simulate_ammonia_curve(80, 600, 25, 7.5)
    assert len(result["hour"]) == 73    # 0 .. 72 inclusive
    assert len(result["nh3_mg_l"]) == 73

def test_simulate_hour_range():
    result = simulate_ammonia_curve(80, 600, 25, 7.5)
    assert result["hour"][0] == 0
    assert result["hour"][-1] == 72

def test_simulate_seed_value():
    result = simulate_ammonia_curve(80, 600, 25, 7.5)
    assert result["nh3_mg_l"][0] == pytest.approx(0.1)

def test_simulate_non_negative():
    result = simulate_ammonia_curve(1, 10000, 25, 7.5)  # weak load; biofilter wins
    assert np.all(result["nh3_mg_l"] >= 0)

def test_simulate_critical_under_overload():
    # 1000 g feed into 100 L at 10 °C — biofilter cannot keep up
    result = simulate_ammonia_curve(1000, 100, 10, 7.8)
    assert result["nh3_mg_l"][-1] > 3.0

# ── health_status ────────────────────────────────────────────────────────────

def test_health_status_has_required_fields():
    result = health_status(0.5)
    assert all(k in result for k in ("status", "color", "message"))

def test_health_status_safe():
    result = health_status(0.999)
    assert result["status"] == "Safe"
    assert result["color"] == "#2ecc71"

def test_health_status_warning_at_boundary():
    assert health_status(1.0)["status"] == "Warning"
    assert health_status(2.0)["status"] == "Warning"
    assert health_status(2.999)["status"] == "Warning"
    assert health_status(1.0)["color"] == "#f39c12"

def test_health_status_critical():
    assert health_status(3.0)["status"] == "Critical"
    assert health_status(5.0)["status"] == "Critical"
    assert health_status(3.0)["color"] == "#e74c3c"
