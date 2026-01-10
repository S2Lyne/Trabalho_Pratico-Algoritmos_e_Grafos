#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import random
from typing import Set, Tuple

Edge = Tuple[int, int]

def add_edge(edges: Set[Edge], u: int, v: int):
    if u == v: return
    a, b = (u, v) if u < v else (v, u)
    edges.add((a, b))

def gen_hp_graph(n: int, target_m: int, seed: int) -> Set[Edge]:
    """Gera grafo com HP garantido (Caminho Escondido)."""
    rnd = random.Random(seed)
    perm = list(range(n))
    rnd.shuffle(perm)
    i0 = perm.index(0)
    perm[0], perm[i0] = perm[i0], perm[0]
    edges: Set[Edge] = set()
    for a, b in zip(perm, perm[1:]):
        add_edge(edges, a, b)
    max_m = n * (n - 1) // 2
    target_m = max(target_m, n - 1)
    target_m = min(target_m, max_m)
    all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    rnd.shuffle(all_pairs)
    for (u, v) in all_pairs:
        if len(edges) >= target_m: break
        add_edge(edges, u, v)
    return edges

def gen_random_graph(n: int, p: float, seed: int) -> Set[Edge]:
    """Gera um grafo G(n, p) de Erdős–Rényi."""
    rnd = random.Random(seed)
    edges: Set[Edge] = set()
    for u in range(n):
        for v in range(u + 1, n):
            if rnd.random() < p:
                add_edge(edges, u, v)
    return edges

def write_graph(path: str, n: int, edges: Set[Edge], base: int):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{n} {len(edges)}\n")
        for (u, v) in sorted(edges):
            f.write(f"{u+base} {v+base}\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--mode", choices=["hp", "er"], default="hp")
    ap.add_argument("--p", type=float, default=0.5, help="Probabilidade para modo er")
    ap.add_argument("--m", type=int, default=None, help="Arestas para modo hp")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--base", type=int, choices=[0, 1], default=0)
    args = ap.parse_args()

    if args.mode == "hp":
        target_m = args.m if args.m is not None else args.n * 2
        edges = gen_hp_graph(args.n, target_m, args.seed)
    else:
        edges = gen_random_graph(args.n, args.p, args.seed)
        
    write_graph(args.out, args.n, edges, base=args.base)
    print(f"[OK] {args.mode} n={args.n} m={len(edges)} em {args.out}")

if __name__ == "__main__":
    main()