# AquaKinetics — CLAUDE.md

Aquaponic biofilter health calculator. R + Shiny only. No Python, Flask, or JavaScript frameworks — ever.

## Stack

- **Runtime:** R 4.6.0
- **UI framework:** Shiny 1.10.0
- **Plots:** base R graphics (`plot`, `par`, `abline`, `legend`) — no ggplot2
- **Dependencies:** declared in `renv.lock`; add new packages there before using them
- **Deployment:** shinyapps.io via `rsconnect::deployApp()`

## Project structure

```
app.R               # Single-file Shiny app — UI and server combined
R/
  kinetics.R        # Monod model: ammonia production, nitrification rate,
                    #   72-hr Euler simulation, health classifier
  ui_helpers.R      # status_badge() — coloured HTML badge component
www/
  styles.css        # Flat CSS theming, no frameworks
renv.lock           # Pinned dependency versions
```

`app.R` calls `source("R/kinetics.R")` and `source("R/ui_helpers.R")` at the top.

## Science model

All biology lives in `R/kinetics.R`. Do not inline model logic in `app.R`.

**Ammonia production**
- TAN (Total Ammonia Nitrogen) = 3% of daily feed mass
- Rate (mg NH₃-N / L / hr) = `feed_g × 0.03 × 1000 / 24 / volume_l`

**Monod nitrification rate**
```
rate = mu_max × temp_factor × ph_factor × (S / (Ks + S))
```
| Parameter | Value | Notes |
|---|---|---|
| `mu_max` | 0.80 mg/L/hr | Established biofilm capacity |
| `Ks` | 1.0 mg/L | Half-saturation constant |
| `temp_factor` | `2^((T - 30) / 10)` | Q10 = 2, reference 30 °C |
| `ph_factor` | `exp(-0.5 × ((pH - 7.8) / 1.2)²)` | Gaussian; optimum 7.8, suppressed below 6.5 |

**Simulation:** Euler integration, 1-hour steps over 72 hours. Initial seed concentration 0.1 mg/L.

**Health thresholds (72-hr final NH₃-N)**
| Status | Threshold | Colour |
|---|---|---|
| Safe | < 1.0 mg/L | `#2ecc71` |
| Warning | 1.0 – 3.0 mg/L | `#f39c12` |
| Critical | > 3.0 mg/L | `#e74c3c` |

If you change any threshold, constant, or formula, update this table.

## Inputs / outputs

**User inputs:** tank volume (L), daily feed (g), water temperature (°C), pH.

**Outputs:**
1. 72-hour ammonia curve plot with Warning and Critical threshold lines
2. Health status badge (Safe / Warning / Critical)
3. Status message string
4. Production rate readout (mg NH₃-N / L / hr)
5. Peak NH₃ readout (mg/L)

## Running the app

```bash
Rscript -e "shiny::runApp('.')"
```

Or open `app.R` in RStudio and click **Run App**.

## Branching and commits

- Branch from `main` using `feat/<slug>` or `fix/<slug>`
- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- PRs merge back to `main`; `main` is the deployment branch

## Constraints

- **No Python.** No Flask, FastAPI, Plumber, or any non-R backend.
- **No JS frameworks.** Vanilla CSS in `www/styles.css` only; no React, Vue, or jQuery plugins.
- **No ggplot2** unless the user explicitly requests it — base R graphics keep the dependency footprint small.
- Model logic stays in `R/kinetics.R`. Server callbacks in `app.R` call functions; they do not implement biology inline.
- Keep `renv.lock` in sync whenever a package is added or removed.
