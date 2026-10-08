import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

os.makedirs("../iterations", exist_ok=True)

# initial guess for e, read from the plateau spacing in charges.png - this should be based off of the smallest gap we see between steps
e_guess = 1.65e-19

# charges and uncertainties saved by velocity2charge.py
df = pd.read_csv("../data/charges.csv")
charge = df["charge"].to_numpy()
charge_unc = df["chargeUnc"].to_numpy()

prev_n = None
e_history = []
e_unc_history = []
order = np.argsort(charge)   # plot drops from smallest to largest charge

for iteration in range(10):
    # number of electrons on each drop, using the current guess
    n = np.rint(charge / e_guess).astype(int)

    # one estimate of e per drop, weighted average of them, and its uncertainty
    e_new = charge / n
    weights = (n / charge_unc)**2
    e_guess = np.sum(weights * e_new) / np.sum(weights)
    e_unc = 1 / np.sqrt(np.sum(weights))

    e_history.append(e_guess)
    e_unc_history.append(e_unc)
    print(f"iteration {iteration + 1}: e = {e_guess:.5e} +/- {e_unc:.2e}")

    # plot Q/N for this iteration
    plt.figure()
    plt.errorbar(range(len(charge)), e_new[order], yerr=(charge_unc / n)[order], fmt="o", capsize=3)
    plt.axhline(e_guess, color="red", label="weighted average")
    plt.xlabel("Drop (sorted by charge)")
    plt.ylabel("Q / n  (C)")
    plt.title(f"Iteration {iteration + 1}")
    plt.legend()
    plt.savefig(os.path.join("../iterations", f"iteration_{iteration + 1}.png"), dpi=200, bbox_inches="tight")

    # stop once n is not changing
    if prev_n is not None and np.array_equal(n, prev_n):
        break
    prev_n = n

# add to the dataframe: number of electrons and individual e charge value for each drop
df["n"] = n
df["eNew"] = e_new
print(f"\nFinal: e = {e_guess:.4e} +/- {e_unc:.1e} C")

# plot how the overall e estimate changes
plt.figure()
plt.errorbar(range(1, len(e_history) + 1), e_history, yerr=e_unc_history, fmt="o-", capsize=3)
plt.xlabel("Iteration")
plt.ylabel("e guess (C)")
plt.title("Weighted average of e per iteration")
plt.xticks(range(1, len(e_history) + 1))
plt.savefig(os.path.join("../iterations", "summary.png"), dpi=200, bbox_inches="tight")

plt.show()