# Millikan Oil Drop Analysis

Pipeline for measuring the electron charge `e` from oil drop velocities:

```
rawdata.csv  ->  dropdata.csv  ->  charges.csv  ->  e (weighted average)
 (measured)     (+ uncertainties)   (Q per drop)     (integer fit of Q/n)
```

## Layout

```
MillikanOilDrop/
├── data/
│   ├── rawdata.csv        # enter these manually
│   ├── dropdata.csv       # raw values + uncertainties
│   └── charges.csv        # dropdata + charge and charge uncertainties
├── python/
│   ├── datacollection     # rawdata.csv -> dropdata.csv 
│   ├── velocity2charge.py # dropdata.csv -> charges.csv, charges.png
│   └── charge_to_e.py     # charges.csv -> e, iteration plots
├── iterations/            # plots saved by charge_to_e.py
└── charges.png            # sorted drop charges, used to pick the initial guess for e
```

## Step 1: Enter raw measurements (`data/rawdata.csv`)

One row per drop:

| Column | Meaning | Units |
|---|---|---|
| `capacitorTotal`, `capacitorTotalUNC` | plate separation and its uncertainty | m |
| `airPressure` | air pressure | kPa |
| `airTemperature` | air temperature | °C |
| `voltage` | plate voltage | V |
| `FOV` | field of view of the camera | m |
| `FPS` | camera frame rate | frames/s |
| `resolution` | image width | pixels |
| `velocity` | velocity (field off) | m/s |
| `velocityE` | velocity (field on) | m/s |
| `travelDistance` | distance tracked for the velocity measurement | m |

## Step 2: Add uncertainties (`dropdata.csv`)

The datacollection script copies the measurements into `dropdata.csv` under the names `velocity2charge.py` expects and attaches an uncertainty to each one:

`capacitorDistance`, `airTemperature`, `airPressure`, `voltage`, `velocity`, `velocityE`, each with a matching `...Unc` column (`capacitorDistanceUnc`, `airTemperatureUnc`, `airPressureUnc`, `voltageUnc`, `velocityUnc`, `velocityEUnc`).

Capacitor distance, temperature, pressure, and voltage uncertainties are instrument uncertainties.

Velocity uncertainties come from the camera resolution and frame rate. Since v = distance / time, the relative uncertainties add in quadrature:

```
position_unc = FOV / resolution              # one pixel, in m
time         = travelDistance / velocity     # time the drop took
time_unc     = 1 / FPS                       # one frame, in s

velocityUnc  = velocity * sqrt( (position_unc / travelDistance)^2 + (time_unc / time)^2 )
```

The same formula is applied to `velocityE` to get `velocityEUnc`. Typical result is about 1% of the velocity. If `velocityUnc` comes out comparable to or larger than `velocity`, check units and that both ratios are squared as a whole.

## Step 3: Charge per drop (`velocity2charge.py`)

Reads `dropdata.csv` and writes `charges.csv` (same columns plus `charge` and `chargeUnc`) and `charges.png`.

Air viscosity from temperature (Sutherland's formula, T in kelvin):

```
eta = eta0 * (T / T0)^(3/2) * (T0 + S) / (T + S)
```

Drop radius from the fall velocity (Stokes' law):

```
a = sqrt( 9 * eta * v / (2 * g * rho) )
```

Charge, with the correction factor:

```
Q = (6 * pi * d / V) * sqrt( 9 * eta^3 / (2 * rho * g) ) * (v + vE) * sqrt(v) * (1 + b / (a * P))^(-3/2)
```


`chargeUnc` is found by error propagation for each input (velocity, velocityE, temperature, pressure, capacitor distance, voltage), take the partial derivative of `Q` with respect to that input, multiply by its uncertainty, and add the contributions in quadrature.

`charges.png` plots the drop charges sorted from smallest to largest. The plateaus in this plot are steps of one electron.

## Step 4: Find the electron charge (`charge2e.py`)

1. **Initial guess.** Set `e_guess` from the smallest gap between plateaus in `charges.png`.
3. **Iterate** (up to 10 times):
   - Assign each drop an integer number of electrons: `n = round(Q / e_guess)`.
   - Each drop gives one estimate of `e`: `Q / n`, with uncertainty `chargeUnc / n`.
   - Combine them in a weighted average with weights `(n / chargeUnc)^2`:
     ```
     e_guess = sum(w * Q/n) / sum(w)
     e_unc   = 1 / sqrt(sum(w))
     ```
   - Stop when `n` no longer changes between iterations.
4. **Output.** The final `e = e_guess ± e_unc` is printed.

Plots are saved to `iterations/`: `iteration_1.png`, `iteration_2.png`, ... show `Q / n` for each drop against the current weighted average, and `summary.png` shows how the `e` estimate changes with each iteration.

## Running

From `python/`:

```
python datacollection.py
python velocity2charge.py
python charge_to_e.py
```

Check `charges.png` after step 2 to make sure the initial `e_guess` in `charge_to_e.py` is reasonable.
