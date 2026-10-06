import numpy as np
import pandas as pd
import os

'''
Reads in raw data: FPS, Camera Resolution, FOV, Capacitor measurements, Air Pressure, Temperature
Propagates the uncertainty in the necessary manner, and creates a new CSV (dropdata.csv) which then 
can be used in velocity2charge.py.

So before running this file, the csv should contain: 
airPressure, airTemperature,voltage,velocity,velocityE, travelDistance - measured data
capacitor_total, FOV, FPS, resolution - uncertainties
'''
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
os.makedirs('../data', exist_ok=True)
df = pd.read_csv('../data/rawdata.csv')

# define capacitor distance from the total measurement, as the top and bottom plates do not change
df["capacitorDistance"] = df["capacitorTotal"] - 0.015351

# uncertainties
calipers_uncertainty = 10e-7
capacitor_top_unc = 0.000004
capacitor_bottom_unc = 0.000004

capacitor_total_unc = df["capacitorTotalUNC"]

FOV = df["FOV"]
FPS = df["FPS"]
resolution = df["resolution"]
travel_distance = df["travelDistance"]

#uncertainty propagation calculations
def calc_capacitor(df):
    # top and bottom in quadrature, then that in quadrature with the device uncertainty
    measurement_unc = np.sqrt(capacitor_bottom_unc**2 + capacitor_top_unc**2 + capacitor_total_unc**2)
    total_uncertainty = np.sqrt(measurement_unc**2 + calipers_uncertainty**2)
    return total_uncertainty

def calc_temperature(df):
    return 0.5 # simple error of device

def calc_pressure(df):
    return 0.1 # simple error of device

def calc_voltage(df):
    return 0.003 * 500.0 # simple error of device

def calc_velocity(df, column):
    # v = distance / time, so the relative uncertainties add in quadrature
    velocity = df[column]
    position_unc = 5 * FOV / resolution   # five pixels, in meters
    time_unc = 1 / FPS                        # one frame, in seconds
    time = travel_distance / velocity                      # time the drop took

    relative_unc = np.sqrt((position_unc / travel_distance)**2 + (time_unc / time)**2)
    return velocity * relative_unc

df["capacitorDistanceUnc"] = calc_capacitor(df)
df["airTemperatureUnc"] = calc_temperature(df)
df["airPressureUnc"] = calc_pressure(df)
df["voltageUnc"] = calc_voltage(df)
df["velocityUnc"] = calc_velocity(df, "velocity")
df["velocityEUnc"] = calc_velocity(df, "velocityE")
df.to_csv('../data/dropdata.csv', index=False)