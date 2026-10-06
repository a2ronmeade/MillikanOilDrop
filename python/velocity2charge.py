import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# constants
gravity = 9.8008 
oil_density = 860
correction_constant = 6.17e-6
accepted_q = 1.602e-19
reference_viscosity = 1.716e-5
reference_temp = 273.15
sutherland = 110.4

# read the data
df = pd.read_csv('../data/dropdata.csv')
capacitor_distance, capacitor_distance_unc = df["capacitorDistance"], df["capacitorDistanceUnc"]
temperature, temperature_unc = df["airTemperature"], df["airTemperatureUnc"]
pressure, pressure_unc = df["airPressure"], df["airPressureUnc"]
voltage, voltage_unc = df["voltage"], df["voltageUnc"]
velocity, velocity_unc = df["velocity"], df["velocityUnc"]
velocityE, velocityE_unc = df["velocityE"], df["velocityEUnc"]

# formulas for calcuations
def calculate_viscosity(temperature):
    temp_kelvin = temperature + 273.15
    viscosity = reference_viscosity * (temp_kelvin/reference_temp)**(3/2) * (reference_temp + sutherland)/(temp_kelvin + sutherland)
    return viscosity

def velocity2radius(velocity, temperature):

    air_viscosity = calculate_viscosity(temperature)

    radius = np.sqrt((9 * air_viscosity * velocity)/(2 * gravity * oil_density))
    return radius

def velocity2charge(velocity, velocityE, temperature, pressure, capacitor_distance, voltage):

    air_viscosity = calculate_viscosity(temperature)
    radius = velocity2radius(velocity, temperature)

    term1 = (6 * np.pi * capacitor_distance) / voltage
    term2 = np.sqrt((9 * air_viscosity**3)/(2 * oil_density * gravity))
    term3 = (velocity + velocityE) * np.sqrt(velocity)
    correction =(1 + correction_constant / (radius * pressure))**(-3/2)

    charge = term1 * term2 * term3 * correction

    return charge

# full calculation for the charges of the drops and uncertainty
def calculate(df):

    values = [df["velocity"], df["velocityE"], df["airTemperature"], df["airPressure"], df["capacitorDistance"], df["voltage"]]
    uncertainties = [df["velocityUnc"], df["velocityEUnc"], df["airTemperatureUnc"], df["airPressureUnc"], df["capacitorDistanceUnc"], df["voltageUnc"]]
 
    charge = velocity2charge(*values)

    contributions = []
    for i in range(len(values)):
        up = list(values)
        down = list(values)
        up[i] = values[i] + uncertainties[i]
        down[i] = values[i] - uncertainties[i]
        contributions.append((velocity2charge(*up) - velocity2charge(*down)) / 2)

    stat_variance = contributions[0]**2 + contributions[1]**2
    systematic_contributions = {
        "airTemperature": contributions[2],
        "airPressure": contributions[3],
        "capacitorDistance": contributions[4],
        "voltage": contributions[5],
    }
    systematic_variance = sum(value**2 for value in systematic_contributions.values())

    df["charge"] = charge
    df["chargeStatUnc"] = np.sqrt(stat_variance)
    for name, contribution in systematic_contributions.items():
        df[f"chargeSys_{name}"] = contribution
    df["chargeUnc"] = np.sqrt(stat_variance + systematic_variance)
    return df

# plotting
def plot_charges(df, filename="../charges.png"):
    sorted_df = df.sort_values("charge").reset_index(drop=True)
 
    fig, ax = plt.subplots(figsize=(8, 5))
    #ax.errorbar(sorted_df.index, sorted_df["charge"], yerr=sorted_df["chargeUnc"],
    ax.errorbar(sorted_df.index, sorted_df["charge"] / 1.602, alpha=0.4, yerr=sorted_df["chargeUnc"],
                fmt="o", capsize=3)
    ax.set_xlabel("Drop (arbitrary units, sorted by charge)")
    ax.set_ylabel("Charge (C)")
    ax.set_title("Measured drop charges")
    ax.set_xticks([])
    ax.grid(alpha=0.3)
    fig.tight_layout()

    fig.savefig(filename, dpi=200)
    plt.show()

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#

calculate(df)

df.to_csv("../data/charges.csv", index=False)
plot_charges(df)
print(df['charge'] / accepted_q)
print(df['chargeUnc'])