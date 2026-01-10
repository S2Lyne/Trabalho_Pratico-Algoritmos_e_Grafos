#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import argparse
from dataclasses import dataclass
from collections import deque
from typing import List, Set, Optional, Tuple


@dataclass
class Graph:
    n: int
    adj: List[Set[int]]

    @property
    def m(self) -> int:
        return sum(len(s) for s in self.adj) // 2

    def degree(self, v: int) -> int:
        return len(self.adj[v])

    def is_connected_ignoring_isolated(self) -> bool:
        if self.n <= 1:
            return True

        start = None
        for v in range(1, self.n + 1):
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

        for v in range(1, self.n + 1):
            if self.degree(v) > 0 and v not in seen:
                return False
        return True

    def summary(self) -> str:
        degrees = [self.degree(v) for v in range(1, self.n + 1)]
        return (
            f"n={self.n}, m={self.m}\n"
            f"graus (min/med/max) = {min(degrees)}/{sum(degrees)/len(degrees):.2f}/{max(degrees)}\n"
            f"qtd grau 0 = {sum(1 for d in degrees if d == 0)}\n"
            f"qtd grau 1 = {sum(1 for d in degrees if d == 1)}\n"
        )


def read_graph(path: str) -> Graph:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]

    if not lines:
        raise ValueError("Arquivo vazio.")

    first = lines[0].split()
    if len(first) != 2:
        raise ValueError("Primeira linha deve ser: n m")

    n = int(first[0])
    m = int(first[1])
    if n <= 0:
        raise ValueError("n deve ser >= 1")
    if m < 0:
        raise ValueError("m deve ser >= 0")

    adj: List[Set[int]] = [set() for _ in range(n + 1)]  # índice 0 não usado
    edges_read = 0

    for i, ln in enumerate(lines[1:], start=2):
        parts = ln.split()
        if len(parts) != 2:
            raise ValueError(f"Linha {i}: esperado 'u v', veio: {ln}")
        u = int(parts[0])
        v = int(parts[1])

        if not (1 <= u <= n and 1 <= v <= n):
            raise ValueError(f"Linha {i}: vértice fora de 1..n: {u}, {v}")
        if u == v:
            raise ValueError(f"Linha {i}: auto-loop (u==v) não permitido: {u}")

        if v not in adj[u]:
            adj[u].add(v)
            adj[v].add(u)
            edges_read += 1

    if edges_read != m:
        print(f"[AVISO] m no arquivo={m}, mas arestas únicas lidas={edges_read}.")

    return Graph(n=n, adj=adj)


def quick_reject(g: Graph) -> Tuple[bool, str]:
    # Grau 0 inviabiliza (para n>1)
    for v in range(1, g.n + 1):
        if g.degree(v) == 0:
            return True, f"Rejeita: vértice {v} tem grau 0 (isolado)."

    # Conectividade (considerando vértices com grau>0)
    if not g.is_connected_ignoring_isolated():
        return True, "Rejeita: grafo desconectado (há componente separado)."

    # No máximo 2 vértices de grau 1 (extremos do caminho)
    deg1 = sum(1 for v in range(1, g.n + 1) if g.degree(v) == 1)
    if deg1 > 2:
        return True, f"Rejeita: há {deg1} vértices de grau 1 (no máximo 2)."

    return False, "Passou nas condições necessárias (não garante que exista HP)."


@dataclass
class Stats:
    calls: int = 0
    expansions: int = 0
    prunes_reach: int = 0
    prunes_deg0_remaining: int = 0
    dead_ends: int = 0


def _reachable_all_from_endpoint(g: Graph, endpoint: int, visited: Set[int]) -> bool:
    """
    Poda por alcançabilidade:
    Se existe vértice não visitado que NÃO é alcançável a partir do endpoint
    usando somente vértices ainda não visitados (e o endpoint), então não dá
    pra completar um caminho hamiltoniano a partir desse estado.
    """
    allowed = set(v for v in range(1, g.n + 1) if v not in visited)
    allowed.add(endpoint)

    q = deque([endpoint])
    seen = {endpoint}

    while q:
        x = q.popleft()
        for y in g.adj[x]:
            if y in allowed and y not in seen:
                seen.add(y)
                q.append(y)

    # todos os não visitados precisam estar alcançáveis a partir do endpoint
    for v in range(1, g.n + 1):
        if v not in visited and v not in seen:
            return False
    return True


def _has_deg0_in_remaining(g: Graph, endpoint: int, visited: Set[int]) -> bool:
    """
    Poda por grau 0 no subgrafo restante:
    Se algum vértice não visitado não tem nenhuma aresta para (endpoint OU outros não visitados),
    ele nunca vai conseguir entrar no caminho.
    """
    remaining = set(v for v in range(1, g.n + 1) if v not in visited)
    allowed = set(remaining)
    allowed.add(endpoint)

    for u in remaining:
        if not any(v in allowed for v in g.adj[u]):
            return True
    return False


def hamiltonian_path_backtracking(g: Graph, stats: Stats) -> Optional[List[int]]:
    """
    Algoritmo exato: backtracking (DFS) construindo um caminho simples.
    Retorna um caminho Hamiltoniano se existir, senão None.
    """

    if g.n == 1:
        return [1]

    # Heurística: se existem vértices de grau 1, eles são bons candidatos a extremos
    deg1_vertices = [v for v in range(1, g.n + 1) if g.degree(v) == 1]
    start_candidates = deg1_vertices if deg1_vertices else list(range(1, g.n + 1))

    def remaining_degree(x: int, visited: Set[int]) -> int:
        return sum(1 for nb in g.adj[x] if nb not in visited)

    def dfs(endpoint: int, path: List[int], visited: Set[int]) -> bool:
        stats.calls += 1

        if len(path) == g.n:
            return True

        # Podas
        if _has_deg0_in_remaining(g, endpoint, visited):
            stats.prunes_deg0_remaining += 1
            return False

        if not _reachable_all_from_endpoint(g, endpoint, visited):
            stats.prunes_reach += 1
            return False

        # Expansão: tenta vizinhos não visitados
        candidates = [nb for nb in g.adj[endpoint] if nb not in visited]
        if not candidates:
            stats.dead_ends += 1
            return False

        # Heurística: tenta primeiro quem tem menor grau restante (reduz branching)
        candidates.sort(key=lambda x: remaining_degree(x, visited))

        for nb in candidates:
            stats.expansions += 1
            visited.add(nb)
            path.append(nb)

            if dfs(nb, path, visited):
                return True

            path.pop()
            visited.remove(nb)

        return False

    for start in start_candidates:
        path = [start]
        visited = {start}
        if dfs(start, path, visited):
            return path

    return None


def write_dot(g: Graph, out_path: str, highlight_path: Optional[List[int]] = None) -> None:
    """
    Exporta o grafo em formato Graphviz DOT.
    Se highlight_path existir, destaca as arestas do caminho.
    """
    highlight_edges = set()
    if highlight_path and len(highlight_path) >= 2:
        for a, b in zip(highlight_path, highlight_path[1:]):
            if a > b:
                a, b = b, a
            highlight_edges.add((a, b))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("graph G {\n")
        f.write("  overlap=false;\n")
        f.write("  splines=true;\n")
        f.write("  node [shape=circle];\n")

        # nós
        for v in range(1, g.n + 1):
            f.write(f"  {v};\n")

        # arestas (u < v)
        for u in range(1, g.n + 1):
            for v in g.adj[u]:
                if u < v:
                    if (u, v) in highlight_edges:
                        f.write(f'  {u} -- {v} [color=red, penwidth=3];\n')
                    else:
                        f.write(f"  {u} -- {v};\n")

        f.write("}\n")


def main():
    ap = argparse.ArgumentParser(description="Hamiltonian Path (HP) - projeto")
    ap.add_argument("graph_file", help="Arquivo do grafo: n m + m arestas (u v)")
    ap.add_argument("--show-adj", action="store_true", help="Imprime lista de adjacência")
    ap.add_argument("--bt", action="store_true", help="Roda backtracking (algoritmo exato 1)")
    ap.add_argument("--show-path", action="store_true", help="Mostra o caminho encontrado (se existir)")
    ap.add_argument("--stats", action="store_true", help="Mostra estatísticas do backtracking")
    ap.add_argument("--dot", type=str, default=None, help="Gera arquivo .dot do grafo (opcional)")
    args = ap.parse_args()

    g = read_graph(args.graph_file)

    print("=== RESUMO DO GRAFO ===")
    print(g.summary())

    if g.n == 1:
        print("=== RESULTADO ===")
        print("HP: SIM (n=1)")
        if args.dot:
            write_dot(g, args.dot, highlight_path=[1])
            print(f"[DOT] gerado em: {args.dot}")
        return

    reject, reason = quick_reject(g)
    print("=== SANITY CHECKS (condições necessárias) ===")
    print(reason)
    if reject:
        print("=== RESULTADO ===")
        print("HP: NÃO (impossível por condição necessária).")
        if args.dot:
            write_dot(g, args.dot, highlight_path=None)
            print(f"[DOT] gerado em: {args.dot}")
        if args.show_adj:
            print("\n=== ADJACÊNCIA ===")
            for v in range(1, g.n + 1):
                print(f"{v}: {sorted(g.adj[v])}")
        return

    if args.show_adj:
        print("\n=== ADJACÊNCIA ===")
        for v in range(1, g.n + 1):
            print(f"{v}: {sorted(g.adj[v])}")

    if not args.bt:
        print("=== RESULTADO ===")
        print("HP: INDEFINIDO (sanity checks passaram; rode --bt para decidir).")
        if args.dot:
            write_dot(g, args.dot, highlight_path=None)
            print(f"[DOT] gerado em: {args.dot}")
        return

    stats = Stats()
    path = hamiltonian_path_backtracking(g, stats)

    print("=== RESULTADO ===")
    if path is None:
        print("HP: NÃO")
    else:
        print("HP: SIM")
        if args.show_path:
            print("Caminho:", " -> ".join(map(str, path)))

    if args.stats:
        print("=== STATS (backtracking) ===")
        print(f"calls (dfs): {stats.calls}")
        print(f"expansions (tentativas): {stats.expansions}")
        print(f"prunes_reach (poda alcançabilidade): {stats.prunes_reach}")
        print(f"prunes_deg0_remaining (poda grau0 restante): {stats.prunes_deg0_remaining}")
        print(f"dead_ends (becos sem saída): {stats.dead_ends}")

    if args.dot:
        write_dot(g, args.dot, highlight_path=path)
        print(f"[DOT] gerado em: {args.dot}")


if __name__ == "__main__":
    main()
