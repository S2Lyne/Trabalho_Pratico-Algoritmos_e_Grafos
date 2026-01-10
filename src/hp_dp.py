#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import argparse
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Graph0:
    n: int
    adj: List[List[int]]  # 0..n-1

    @property
    def m(self) -> int:
        return sum(len(vs) for vs in self.adj) // 2


def read_graph_0based(path: str) -> Graph0:
    """
    Lê no formato do enunciado:
      n m
      v u
      v u
      ...
    com vértices tipicamente em 0..n-1.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]

    if not lines:
        raise ValueError("Arquivo vazio.")

    n, m = map(int, lines[0].split())
    if n <= 0 or m < 0:
        raise ValueError("Valores inválidos de n/m.")

    adj = [[] for _ in range(n)]
    seen = set()

    for i, ln in enumerate(lines[1:], start=2):
        a, b = map(int, ln.split())
        if not (0 <= a < n and 0 <= b < n):
            raise ValueError(f"Linha {i}: vértice fora de 0..n-1: {a}, {b}")
        if a == b:
            raise ValueError(f"Linha {i}: auto-loop não permitido: {a}")

        u, v = (a, b) if a < b else (b, a)
        if (u, v) in seen:
            continue
        seen.add((u, v))
        adj[a].append(b)
        adj[b].append(a)

    if len(seen) != m:
        print(f"[AVISO] m no arquivo={m}, mas arestas únicas lidas={len(seen)}.")

    return Graph0(n=n, adj=adj)


@dataclass
class DPStats:
    transitions: int = 0
    states_reached: int = 0
    masks_processed: int = 0
    time_sec: float = 0.0


def hamiltonian_path_dp_bitmask(g: Graph0, stats: DPStats) -> Optional[List[int]]:
    """
    DP por subconjuntos (bitmask):
    dp[mask] = bitset de vértices v tais que existe caminho que visita exatamente os vértices em 'mask'
               e termina em v.

    Reconstrução: guardamos predecessor apenas quando um estado (mask, v) é alcançado pela primeira vez.
    Observação: isso escala bem até ~20-22 vértices em Python.
    """
    n = g.n
    if n == 1:
        return [0]

    # Para não travar: DP explode em 2^n
    if n > 24:
        print("[DP] n muito grande para DP em Python puro (2^n explode). Use DP só até ~24.")
        return None

    start_t = time.perf_counter()

    size = 1 << n
    dp = [0] * size  # bitset de endpoints alcançáveis
    parent = {}      # (mask, v) -> prev

    # inicializa: caminhos de tamanho 1
    for s in range(n):
        mask = 1 << s
        dp[mask] |= (1 << s)
        parent[(mask, s)] = -1

    full = (1 << n) - 1

    # itera máscaras
    for mask in range(size):
        endpoints = dp[mask]
        if endpoints == 0:
            continue
        stats.masks_processed += 1

        # percorre cada endpoint v presente no bitset
        vbits = endpoints
        while vbits:
            lsb = vbits & -vbits
            v = (lsb.bit_length() - 1)
            vbits -= lsb

            # tenta estender para vizinhos u fora do mask
            for u in g.adj[v]:
                if (mask >> u) & 1:
                    continue
                stats.transitions += 1
                nmask = mask | (1 << u)
                if (dp[nmask] >> u) & 1:
                    continue  # já conhecido
                dp[nmask] |= (1 << u)
                parent[(nmask, u)] = v
                stats.states_reached += 1

    stats.time_sec = time.perf_counter() - start_t

    # decide e reconstrói
    endpoints_full = dp[full]
    if endpoints_full == 0:
        return None

    # pega algum endpoint v do full
    lsb = endpoints_full & -endpoints_full
    end = lsb.bit_length() - 1

    # reconstrói caminho
    path = []
    mask = full
    v = end
    while v != -1:
        path.append(v)
        pv = parent.get((mask, v), -1)
        mask = mask & ~(1 << v)
        v = pv

    path.reverse()
    return path


def write_dot_0based(g: Graph0, out_path: str, highlight_path: Optional[List[int]] = None) -> None:
    highlight_edges = set()
    if highlight_path and len(highlight_path) >= 2:
        for a, b in zip(highlight_path, highlight_path[1:]):
            u, v = (a, b) if a < b else (b, a)
            highlight_edges.add((u, v))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("graph G {\n")
        f.write("  overlap=false;\n")
        f.write("  splines=true;\n")
        f.write("  node [shape=circle];\n")

        for v in range(g.n):
            f.write(f"  {v};\n")

        for v in range(g.n):
            for u in g.adj[v]:
                if v < u:
                    if (v, u) in highlight_edges:
                        f.write(f'  {v} -- {u} [color=red, penwidth=3];\n')
                    else:
                        f.write(f"  {v} -- {u};\n")
        f.write("}\n")


def main():
    ap = argparse.ArgumentParser(description="HP via DP bitmask (0-based)")
    ap.add_argument("graph_file")
    ap.add_argument("--show-adj", action="store_true")
    ap.add_argument("--show-path", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--dot", type=str, default=None)
    args = ap.parse_args()

    g = read_graph_0based(args.graph_file)

    print("=== RESUMO DO GRAFO (0-based) ===")
    print(f"n={g.n}, m={g.m}")

    if args.show_adj:
        print("\n=== ADJACÊNCIA ===")
        for v in range(g.n):
            print(f"{v}: {sorted(g.adj[v])}")

    stats = DPStats()
    path = hamiltonian_path_dp_bitmask(g, stats)

    print("=== RESULTADO (DP bitmask) ===")
    if path is None:
        print("HP: NÃO (ou DP abortou por n muito grande)")
    else:
        print("HP: SIM")
        if args.show_path:
            print("Caminho:", " -> ".join(map(str, path)))

    if args.stats:
        print("=== STATS (DP) ===")
        print(f"time_sec: {stats.time_sec:.6f}")
        print(f"masks_processed: {stats.masks_processed}")
        print(f"states_reached: {stats.states_reached}")
        print(f"transitions: {stats.transitions}")

    if args.dot:
        write_dot_0based(g, args.dot, highlight_path=path)
        print(f"[DOT] gerado em: {args.dot}")


if __name__ == "__main__":
    main()
