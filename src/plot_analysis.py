#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

CSV_PATH = "outputs/results.csv"
OUT_DIR = "outputs/plots_analysis"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)
df["time_sec"] = pd.to_numeric(df["time_sec"], errors="coerce")
df_bt = df[df["algo"] == "BT"].copy()

# 1. Gráfico de Esforço de Busca (Calls vs N)
plt.figure(figsize=(10, 6))
sns.lineplot(data=df_bt, x="n", y="calls", hue="density", marker="o")
plt.yscale("log")
plt.title("Esforço de Busca: Número de Chamadas Recursivas (BT)")
plt.ylabel("Qtd de Chamadas (Escala Log)")
plt.xlabel("Número de Vértices (n)")
plt.grid(True, which="both", ls="-", alpha=0.5)
plt.savefig(f"{OUT_DIR}/bt_search_effort.png", dpi=300)

# 2. Gráfico de Podas (Análise de Eficiência)
# Mostra quão úteis estão sendo suas funções de poda
df_bt["total_prunes"] = df_bt["prunes_reach"] + df_bt["prunes_deg0_remaining"]
plt.figure(figsize=(10, 6))
sns.barplot(data=df_bt, x="n", y="total_prunes", hue="density")
plt.title("Eficiência das Podas por Tamanho de Instância")
plt.ylabel("Total de Podas Realizadas")
plt.savefig(f"{OUT_DIR}/bt_pruning_efficiency.png", dpi=300)

print(f"[OK] Gráficos de análise acadêmica gerados em: {OUT_DIR}")