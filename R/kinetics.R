# Monod kinetics and ammonia curve calculations

#' Estimate ammonia production rate (mg NH3-N / L / hr)
#' Based on feed input and tank volume; ~3% of feed becomes TAN.
ammonia_production_rate <- function(feed_g, volume_l) {
  tan_per_day_mg <- feed_g * 0.03 * 1000  # 3% of feed as TAN, converted to mg
  tan_per_hour_mg_per_l <- tan_per_day_mg / 24 / volume_l
  tan_per_hour_mg_per_l
}

#' Monod nitrification rate (mg NH3-N / L / hr)
#' mu_max tuned for Nitrosomonas, Ks ~1 mg/L NH3-N.
#' Temperature correction: Q10 ≈ 2 (halves per 10°C drop from 30°C).
#' pH penalty: nitrifiers optimum ~7.5–8.0; drops off outside that band.
monod_nitrification_rate <- function(nh3_conc, temp_c, ph) {
  mu_max  <- 0.80   # max volumetric nitrification rate for established biofilm, mg/L/hr
  Ks      <- 1.0    # half-saturation constant, mg/L

  # Temperature correction (reference 30°C)
  temp_factor <- 2^((temp_c - 30) / 10)

  # pH correction: Gaussian-like penalty centred at 7.8
  ph_factor <- exp(-0.5 * ((ph - 7.8) / 1.2)^2)

  mu_max * temp_factor * ph_factor * (nh3_conc / (Ks + nh3_conc))
}

#' Simulate a 72-hour ammonia concentration curve (mg/L)
#' Simple Euler integration with 1-hour steps.
simulate_ammonia_curve <- function(feed_g, volume_l, temp_c, ph,
                                   hours = 72, dt = 1) {
  prod_rate <- ammonia_production_rate(feed_g, volume_l)
  times     <- seq(0, hours, by = dt)
  nh3       <- numeric(length(times))
  nh3[1]    <- 0.1  # small initial seed concentration

  for (i in seq_along(times)[-1]) {
    nitrif <- monod_nitrification_rate(nh3[i - 1], temp_c, ph)
    delta  <- (prod_rate - nitrif) * dt
    nh3[i] <- max(0, nh3[i - 1] + delta)
  }

  data.frame(hour = times, nh3_mg_l = nh3)
}

#' Classify final (72-hr) ammonia concentration into health status
health_status <- function(final_nh3) {
  if (final_nh3 < 1.0) {
    list(status = "Safe",     color = "#2ecc71",
         message = "Biofilter is keeping up with ammonia load.")
  } else if (final_nh3 < 3.0) {
    list(status = "Warning",  color = "#f39c12",
         message = "Ammonia is elevated — monitor closely and reduce feeding.")
  } else {
    list(status = "Critical", color = "#e74c3c",
         message = "Ammonia dangerously high — immediate action required.")
  }
}
