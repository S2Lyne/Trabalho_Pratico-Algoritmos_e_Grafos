# plot_results.py (ideia)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("outputs/results.csv")

# só ok (e opcionalmente timeout se você quiser mostrar)
df["time_sec"] = pd.to_numeric(df["time_sec"], errors="coerce")
df_ok = df[df["status"].isin(["ok", "timeout"]) & df["time_sec"].notna()].copy()

# média por n/density/algo
g = (df_ok.groupby(["density", "algo", "n"])["time_sec"]
          .mean()
          .reset_index())

for density in ["sparse", "dense"]:
    plt.figure()
    sub = g[g["density"] == density]

    for algo in ["BT", "DP"]:
        s = sub[sub["algo"] == algo].sort_values("n")
        if s.empty:
            continue

        y = s["time_sec"].to_numpy()
        # log não aceita 0
        y = np.maximum(y, 1e-6)

        plt.plot(s["n"], y, marker="o", label=algo)

    plt.yscale("log")
    plt.xlabel("n (vértices)")
    plt.ylabel("tempo médio (s) - escala log")
    plt.title(f"Tempo médio vs n ({density})")
    plt.grid(True, which="both")
    plt.legend()
    plt.savefig(f"outputs/plots/time_{density}.png", dpi=200, bbox_inches="tight")
    plt.close()