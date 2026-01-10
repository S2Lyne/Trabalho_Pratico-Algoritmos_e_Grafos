#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import time
import signal
import os
from dataclasses import asdict

import hp_bt0  # BT (0-based) - Agora com poda de componentes!
import hp_dp  # DP (0-based)
from graph_gen import gen_random_graph, write_graph

class Timeout(Exception):
    pass

def _alarm_handler(signum, frame):
    raise Timeout()

def run_bt(path_0based: str, timeout_sec: int):
    """Executa o Backtracking com tratamento de Timeout e Sanity Checks."""
    g = hp_bt0.read_graph_0based(path_0based)

    # Sanity Check original mantido
    reject, _ = hp_bt0.quick_reject(g)
    if reject:
        return {"hp": False, "time_sec": 0.0, "calls": 0, "expansions": 0,
                "prunes_reach": 0, "prunes_deg0_remaining": 0, "dead_ends": 0,
                "status": "rejected_by_sanity"}

    stats = hp_bt0.Stats()
    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(timeout_sec)

    t0 = time.perf_counter()
    try:
        path = hp_bt0.hamiltonian_path_backtracking_0based(g, stats)
        dt = time.perf_counter() - t0
        signal.alarm(0)
        return {"hp": path is not None, "time_sec": dt, **asdict(stats), "status": "ok"}
    except Timeout:
        dt = time.perf_counter() - t0
        signal.alarm(0)
        return {"hp": None, "time_sec": dt, **asdict(stats), "status": "timeout"}

def run_dp(path_0based: str):
    """Executa a Programação Dinâmica com limite de N."""
    g = hp_dp.read_graph_0based(path_0based)

    if g.n > 24:
        return {"hp": None, "time_sec": None,
                "masks_processed": None, "states_reached": None,
                "transitions": None, "status": "skipped_n_gt_24"}

    stats = hp_dp.DPStats()
    t0 = time.perf_counter()
    path = hp_dp.hamiltonian_path_dp_bitmask(g, stats)
    dt = time.perf_counter() - t0

    return {"hp": path is not None, "time_sec": dt,
            "masks_processed": stats.masks_processed,
            "states_reached": stats.states_reached,
            "transitions": stats.transitions,
            "status": "ok"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="outputs/results.csv")
    ap.add_argument("--timeout-bt", type=int, default=10)
    ap.add_argument("--trials", type=int, default=3)
    args = ap.parse_args()

    os.makedirs("data/graphs", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    # Mantendo seus tamanhos e densidades originais
    sizes = [10, 20, 30, 40, 50]
    # Usaremos probabilidades para definir esparso (~0.15) e denso (~0.5)
    experiments = [
        {"label": "sparse", "p": 0.15}, 
        {"label": "dense", "p": 0.5}
    ]

    rows = []
    print(f"Iniciando benchmark completo... (Salvando em {args.csv})")

    for n in sizes:
        for exp in experiments:
            density_label = exp["label"]
            prob = exp["p"]
            
            for trial in range(args.trials):
                seed = 1000 + 17*n + 31*trial
                f0 = f"data/graphs/g{n}_{density_label}_{trial}_0.txt"

                # Geração de grafo aleatório (Erdős–Rényi) para teste real NP-Completo
                edges = gen_random_graph(n, prob, seed=seed)
                write_graph(f0, n, edges, base=0)

                # Execução BT
                bt_res = run_bt(f0, timeout_sec=args.timeout_bt)
                rows.append({
                    "algo": "BT", "n": n, "density": density_label, 
                    "p": prob, "trial": trial, **bt_res
                })

                # Execução DP
                dp_res = run_dp(f0)
                rows.append({
                    "algo": "DP", "n": n, "density": density_label, 
                    "p": prob, "trial": trial, **dp_res
                })
        
        print(f"Finalizado N={n}...")

    # Salva os resultados garantindo que todas as colunas de Stats apareçam
    fieldnames = sorted({k for r in rows for k in r.keys()})
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\n[OK] Benchmark concluído. Resultados salvos em {args.csv}")

if __name__ == "__main__":
    main()