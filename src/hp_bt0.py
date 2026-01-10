#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import argparse
from dataclasses import dataclass
from collections import deque
from typing import List, Set, Optional, Tuple

@dataclass
class Graph0:
    n: int
    adj: List[Set[int]]  # 0..n-1

    @property
    def m(self) -> int:
        return sum(len(s) for s in self.adj) // 2

    def degree(self, v: int) -> int:
        return len(self.adj[v])

    def is_connected_ignoring_isolated(self) -> bool:
        if self.n <= 1:
            return True

        start = None
        for v in range(self.n):
            if self.degree(v) > 0:
                start = v
                break
        if start is None:
            return False

        seen = {start}
        q = deque([start])
        while q:
            x = q.popleft()
            for y in self.adj[x]:
                if y not in seen:
                    seen.add(y)
                    q.append(y)

        for v in range(self.n):
            if self.degree(v) > 0 and v not in seen:
                return False
        return True

    def summary(self) -> str:
        degrees = [self.degree(v) for v in range(self.n)]
        return (
            f"n={self.n}, m={self.m}\n"
            f"graus (min/med/max) = {min(degrees)}/{sum(degrees)/len(degrees):.2f}/{max(degrees)}\n"
            f"qtd grau 0 = {sum(1 for d in degrees if d == 0)}\n"
            f"qtd grau 1 = {sum(1 for d in degrees if d == 1)}\n"
        )


def read_graph_0based(path: str) -> Graph0:
    """ Lê o formato definido: n m seguido por u v """
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]

    if not lines:
        raise ValueError("Arquivo vazio.")

    first = lines[0].split()
    if len(first) != 2:
        raise ValueError("Primeira linha deve ser: n m")

    n = int(first[0])
    m = int(first[1])
    adj: List[Set[int]] = [set() for _ in range(n)]
    edges_read = 0

    for i, ln in enumerate(lines[1:], start=2):
        parts = ln.split()
        if len(parts) != 2: continue
        u, v = map(int, parts)
        if v not in adj[u]:
            adj[u].add(v)
            adj[v].add(u)
            edges_read += 1

    if edges_read != m:
        print(f"[AVISO] m esperado={m}, lidas={edges_read}.")

    return Graph0(n=n, adj=adj)


def quick_reject(g: Graph0) -> Tuple[bool, str]:
    for v in range(g.n):
        if g.degree(v) == 0:
            return True, f"Rejeita: vértice {v} tem grau 0 (isolado)."

    if not g.is_connected_ignoring_isolated():
        return True, "Rejeita: grafo desconectado."

    deg1 = sum(1 for v in range(g.n) if g.degree(v) == 1)
    if deg1 > 2:
        return True, f"Rejeita: há {deg1} vértices de grau 1 (no máximo 2)."

    return False, "Passou nas condições necessárias."


@dataclass
class Stats:
    calls: int = 0
    expansions: int = 0
    prunes_reach: int = 0
    prunes_deg0_remaining: int = 0
    dead_ends: int = 0


def count_components(nodes: Set[int], adj: List[Set[int]]) -> int:
    """ Conta componentes conexos no subgrafo formado pelos 'nodes' """
    if not nodes: return 0
    visited_comp = set()
    count = 0
    nodes_list = list(nodes)
    for start_node in nodes_list:
        if start_node not in visited_comp:
            count += 1
            q = deque([start_node])
            visited_comp.add(start_node)
            while q:
                curr = q.popleft()
                for neighbor in adj[curr]:
                    if neighbor in nodes and neighbor not in visited_comp:
                        visited_comp.add(neighbor)
                        q.append(neighbor)
    return count


def _reachable_all_from_endpoint(g: Graph0, endpoint: int, visited: Set[int]) -> bool:
    """ Poda avançada: O endpoint e os não visitados devem ser conexos. """
    remaining = set(v for v in range(g.n) if v not in visited)
    if not remaining: 
        return True
    
    # Adiciona o endpoint ao conjunto para checar se ele consegue chegar em todos
    nodes_to_check = remaining | {endpoint}
    if count_components(nodes_to_check, g.adj) > 1:
        return False
    return True

def _has_deg0_in_remaining(g: Graph0, endpoint: int, visited: Set[int]) -> bool:
    remaining = set(v for v in range(g.n) if v not in visited)
    allowed = remaining | {endpoint}
    for u in remaining:
        if not any(v in allowed for v in g.adj[u]):
            return True
    return False


def hamiltonian_path_backtracking_0based(g: Graph0, stats: Stats) -> Optional[List[int]]:
    if g.n == 1: return [0]

    deg1_vertices = [v for v in range(g.n) if g.degree(v) == 1]
    start_candidates = deg1_vertices if deg1_vertices else list(range(g.n))

    def remaining_degree(x: int, visited: Set[int]) -> int:
        return sum(1 for nb in g.adj[x] if nb not in visited)

    def dfs(endpoint: int, path: List[int], visited: Set[int]) -> bool:
        stats.calls += 1
        if len(path) == g.n: return True

        if _has_deg0_in_remaining(g, endpoint, visited):
            stats.prunes_deg0_remaining += 1
            return False

        if not _reachable_all_from_endpoint(g, endpoint, visited):
            stats.prunes_reach += 1
            return False

        candidates = [nb for nb in g.adj[endpoint] if nb not in visited]
        if not candidates:
            stats.dead_ends += 1
            return False

        # Heurística de Warnsdorff
        candidates.sort(key=lambda x: remaining_degree(x, visited))

        for nb in candidates:
            stats.expansions += 1
            visited.add(nb)
            path.append(nb)
            if dfs(nb, path, visited): return True
            path.pop()
            visited.remove(nb)
        return False

    for start in start_candidates:
        path = [start]
        visited = {start}
        if dfs(start, path, visited):
            return path
    return None


def main():
    ap = argparse.ArgumentParser(description="Hamiltonian Path (HP) - backtracking 0-based")
    ap.add_argument("graph_file", help="Arquivo do grafo")
    ap.add_argument("--show-adj", action="store_true")
    ap.add_argument("--show-path", action="store_true")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    g = read_graph_0based(args.graph_file)

    print("=== RESUMO DO GRAFO (0-based) ===")
    print(g.summary())

    reject, reason = quick_reject(g)
    print("=== SANITY CHECKS (condições necessárias) ===")
    print(reason)

    if reject:
        print("=== RESULTADO ===")
        print("HP: NÃO (impossível por condição necessária).")
        if args.show_adj:
            print("\n=== ADJACÊNCIA ===")
            for v in range(g.n):
                print(f"{v}: {sorted(g.adj[v])}")
        return

    if args.show_adj:
        print("\n=== ADJACÊNCIA ===")
        for v in range(g.n):
            print(f"{v}: {sorted(g.adj[v])}")

    stats = Stats()
    path = hamiltonian_path_backtracking_0based(g, stats)

    print("=== RESULTADO ===")
    if path is None:
        print("HP: NÃO")
    else:
        print("HP: SIM")
        if args.show_path:
            print("Caminho:", " -> ".join(map(str, path)))

    if args.stats:
        print("=== STATS (backtracking 0-based) ===")
        print(f"calls (dfs): {stats.calls}")
        print(f"expansions (tentativas): {stats.expansions}")
        print(f"prunes_reach (poda alcançabilidade): {stats.prunes_reach}")
        print(f"prunes_deg0_remaining (poda grau0 restante): {stats.prunes_deg0_remaining}")
        print(f"dead_ends (becos sem saída): {stats.dead_ends}")

if __name__ == "__main__":
    main()