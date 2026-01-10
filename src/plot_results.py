#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "outputs/results.csv"
OUT_DIR = "outputs/plots"

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)

# garante numérico; DP pulado vira NaN (porque time_sec fica vazio)
df["time_sec"] = pd.to_numeric(df["time_sec"], errors="coerce")

# remove linhas sem tempo (ex: DP skipped)
df_ok = df[(df["status"] == "ok") & (df["time_sec"].notna())].copy()

# média por (algo, density, n)
grp = df_ok.groupby(["algo", "density", "n"])["time_sec"].mean().reset_index()

for density in ["sparse", "dense"]:
    sub = grp[grp["density"] == density]

    for algo in ["BT", "DP"]:
        s2 = sub[sub["algo"] == algo]
        if s2.empty:
            continue
        plt.plot(s2["n"], s2["time_sec"], marker="o", label=algo)

    plt.xlabel("n (vértices)")
    plt.ylabel("tempo médio (s)")
    plt.title(f"Tempo médio vs n ({density})")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/time_{density}1.png")
    plt.clf()

print(f"[OK] gráficos gerados: {OUT_DIR}/time_sparse1.png, {OUT_DIR}/time_dense1.png")
