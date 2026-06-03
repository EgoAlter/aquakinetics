import numpy as np


def ammonia_production_rate(feed_g, volume_l):
    """Estimate ammonia production rate (mg NH3-N / L / hr).
    ~3 % of feed mass becomes TAN."""
    tan_per_day_mg = feed_g * 0.03 * 1000
    return tan_per_day_mg / 24 / volume_l


def monod_nitrification_rate(nh3_conc, temp_c, ph):
    """Monod nitrification rate (mg NH3-N / L / hr).

    mu_max tuned for Nitrosomonas established biofilm.
    Temperature correction: Q10 = 2 (reference 30 °C).
    pH correction: Gaussian optimum at 7.8, σ = 1.2.
    """
    mu_max = 0.80
    Ks = 1.0
    temp_factor = 2 ** ((temp_c - 30) / 10)
    ph_factor = np.exp(-0.5 * ((ph - 7.8) / 1.2) ** 2)
    return mu_max * temp_factor * ph_factor * (nh3_conc / (Ks + nh3_conc))


def simulate_ammonia_curve(feed_g, volume_l, temp_c, ph, hours=72, dt=1):
    """Euler integration over `hours` with step `dt`.

    Returns a dict with NumPy arrays 'hour' and 'nh3_mg_l'.
    """
    prod_rate = ammonia_production_rate(feed_g, volume_l)
    times = np.arange(0, hours + dt, dt)
    nh3 = np.zeros(len(times))
    nh3[0] = 0.1  # small initial seed concentration

    for i in range(1, len(times)):
        nitrif = monod_nitrification_rate(nh3[i - 1], temp_c, ph)
        delta = (prod_rate - nitrif) * dt
        nh3[i] = max(0.0, nh3[i - 1] + delta)

    return {"hour": times, "nh3_mg_l": nh3}


def health_status(final_nh3):
    """Classify 72-hr final NH3-N concentration into health status."""
    if final_nh3 < 1.0:
        return {
            "status": "Safe",
            "color": "#2ecc71",
            "message": "Biofilter is keeping up with ammonia load.",
        }
    elif final_nh3 < 3.0:
        return {
            "status": "Warning",
            "color": "#f39c12",
            "message": "Ammonia is elevated — monitor closely and reduce feeding.",
        }
    else:
        return {
            "status": "Critical",
            "color": "#e74c3c",
            "message": "Ammonia dangerously high — immediate action required.",
        }
