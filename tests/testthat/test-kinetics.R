# Tests for R/kinetics.R — all four exported functions

# ── ammonia_production_rate ──────────────────────────────────────────────────

test_that("ammonia_production_rate matches manual formula", {
  expected <- 80 * 0.03 * 1000 / 24 / 600
  expect_equal(ammonia_production_rate(80, 600), expected)
})

test_that("ammonia_production_rate is zero when feed is zero", {
  expect_equal(ammonia_production_rate(0, 600), 0)
})

test_that("ammonia_production_rate scales linearly with feed and volume", {
  base <- ammonia_production_rate(80, 600)
  expect_equal(ammonia_production_rate(160, 600), 2 * base)   # double feed
  expect_equal(ammonia_production_rate(80, 1200), 0.5 * base) # double volume
})

# ── monod_nitrification_rate ─────────────────────────────────────────────────

test_that("monod_nitrification_rate is zero at zero substrate", {
  expect_equal(monod_nitrification_rate(0, 25, 7.5), 0)
})

test_that("monod_nitrification_rate equals mu_max/2 at Ks under optimal conditions", {
  # temp=30 → temp_factor=1; pH=7.8 → ph_factor=1; nh3=Ks=1.0 → Monod term=0.5
  expect_equal(monod_nitrification_rate(1.0, 30, 7.8), 0.40, tolerance = 1e-9)
})

test_that("monod_nitrification_rate increases with temperature", {
  expect_gt(
    monod_nitrification_rate(2, 30, 7.8),
    monod_nitrification_rate(2, 20, 7.8)
  )
})

test_that("monod_nitrification_rate is maximised at pH 7.8", {
  optimal <- monod_nitrification_rate(5, 30, 7.8)
  expect_gt(optimal, monod_nitrification_rate(5, 30, 6.0))
  expect_gt(optimal, monod_nitrification_rate(5, 30, 9.0))
})

test_that("monod_nitrification_rate is symmetric around pH 7.8", {
  delta <- 0.8
  expect_equal(
    monod_nitrification_rate(5, 30, 7.8 - delta),
    monod_nitrification_rate(5, 30, 7.8 + delta),
    tolerance = 1e-9
  )
})

# ── simulate_ammonia_curve ───────────────────────────────────────────────────

test_that("simulate_ammonia_curve returns a data.frame with correct shape", {
  df <- simulate_ammonia_curve(80, 600, 25, 7.5)
  expect_s3_class(df, "data.frame")
  expect_named(df, c("hour", "nh3_mg_l"))
  expect_equal(nrow(df), 73)   # hours 0..72 inclusive
  expect_equal(df$hour[1],  0)
  expect_equal(df$hour[73], 72)
})

test_that("simulate_ammonia_curve seeds at 0.1 mg/L", {
  df <- simulate_ammonia_curve(80, 600, 25, 7.5)
  expect_equal(df$nh3_mg_l[1], 0.1)
})

test_that("simulate_ammonia_curve concentrations are non-negative", {
  df <- simulate_ammonia_curve(1, 10000, 25, 7.5) # weak load, biofilter dominates
  expect_true(all(df$nh3_mg_l >= 0))
})

test_that("simulate_ammonia_curve reaches Critical under heavy overload", {
  # 1000 g feed into 100 L at 10 °C — biofilter cannot keep up
  df <- simulate_ammonia_curve(1000, 100, 10, 7.8)
  expect_gt(tail(df$nh3_mg_l, 1), 3.0)
})

# ── health_status ────────────────────────────────────────────────────────────

test_that("health_status returns all three required fields", {
  result <- health_status(0.5)
  expect_true(all(c("status", "color", "message") %in% names(result)))
})

test_that("health_status Safe below 1 mg/L", {
  result <- health_status(0.999)
  expect_equal(result$status, "Safe")
  expect_equal(result$color,  "#2ecc71")
})

test_that("health_status Warning at and above 1 mg/L, below 3 mg/L", {
  expect_equal(health_status(1.0)$status, "Warning")
  expect_equal(health_status(2.0)$status, "Warning")
  expect_equal(health_status(2.999)$status, "Warning")
  expect_equal(health_status(1.0)$color, "#f39c12")
})

test_that("health_status Critical at and above 3 mg/L", {
  expect_equal(health_status(3.0)$status, "Critical")
  expect_equal(health_status(5.0)$status, "Critical")
  expect_equal(health_status(3.0)$color, "#e74c3c")
})
