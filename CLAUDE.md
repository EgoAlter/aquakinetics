# AquaKinetics — CLAUDE.md (`feat/python-dash` branch)

> **This is the Python parallel branch.** The canonical R + Shiny version lives on `main`.
> The R constraints below do NOT apply here.

Aquaponic biofilter health calculator — Python rebuild for side-by-side comparison with the R/Shiny version.

## Stack

- **Runtime:** Python 3.x
- **UI framework:** Dash 2.18+
- **Plots:** Matplotlib (rendered to base64 PNG, embedded via `html.Img`)
- **Numerics:** NumPy
- **Dependencies:** declared in `requirements.txt`
- **Tests:** pytest

## Project structure

```
app.py              # Single-file Dash app — layout and callbacks combined
kinetics.py         # Monod model: ammonia production, nitrification rate,
                    #   72-hr Euler simulation, health classifier
assets/
  styles.css        # Flat CSS theming (Dash auto-serves the assets/ folder)
requirements.txt    # Pinned dependency versions
conftest.py         # pytest path setup
tests/
  test_kinetics.py  # pytest tests for kinetics.py
```

## Running the app

```bash
pip install -r requirements.txt
python app.py
```

## Running tests

```bash
pytest tests/
```

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
