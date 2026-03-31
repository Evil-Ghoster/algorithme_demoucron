from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import List, Optional, Tuple


Matrix = List[List[float]]
MaybeMatrix = List[List[Optional[float]]]


@dataclass
class DemoucronResult:
    values: Matrix
    next_node: List[List[Optional[int]]]
    history: List[Matrix]


def _copy_matrix(m: Matrix) -> Matrix:
    return [row[:] for row in m]


def _validate_square(matrix: MaybeMatrix) -> int:
    n = len(matrix)
    if n == 0:
        raise ValueError("La matrice ne peut pas etre vide.")
    if any(len(row) != n for row in matrix):
        raise ValueError("La matrice doit etre carree (n x n).")
    return n


def demoucron_min(matrix: MaybeMatrix) -> DemoucronResult:
    """Version minimisation (cours: absence d'arc = +inf)."""
    n = _validate_square(matrix)

    values: Matrix = [[inf] * n for _ in range(n)]
    reach = [[False] * n for _ in range(n)]
    next_node: List[List[Optional[int]]] = [[None] * n for _ in range(n)]

    for i in range(n):
        values[i][i] = 0
        reach[i][i] = True
        next_node[i][i] = i
        for j in range(n):
            w = matrix[i][j]
            if w is not None:
                values[i][j] = float(w)
                reach[i][j] = True
                next_node[i][j] = j

    history: List[Matrix] = [_copy_matrix(values)]

    # Etape k: autoriser le sommet k comme intermediaire.
    for k in range(n):
        for i in range(n):
            if not reach[i][k]:
                continue
            for j in range(n):
                if not reach[k][j]:
                    continue
                candidate = values[i][k] + values[k][j]
                if candidate < values[i][j]:
                    values[i][j] = candidate
                    reach[i][j] = True
                    next_node[i][j] = next_node[i][k]
        history.append(_copy_matrix(values))

    return DemoucronResult(values=values, next_node=next_node, history=history)


def demoucron_max(matrix: MaybeMatrix) -> DemoucronResult:
    """Version maximisation (cours: absence d'arc = 0)."""
    n = _validate_square(matrix)

    values: Matrix = [[0.0] * n for _ in range(n)]
    reach = [[False] * n for _ in range(n)]
    next_node: List[List[Optional[int]]] = [[None] * n for _ in range(n)]

    for i in range(n):
        values[i][i] = 0.0
        reach[i][i] = True
        next_node[i][i] = i
        for j in range(n):
            w = matrix[i][j]
            if w is not None:
                values[i][j] = float(w)
                reach[i][j] = True
                next_node[i][j] = j

    history: List[Matrix] = [_copy_matrix(values)]

    # Meme recurrence, mais comparaison en max.
    for k in range(n):
        for i in range(n):
            if not reach[i][k]:
                continue
            for j in range(n):
                if not reach[k][j]:
                    continue
                candidate = values[i][k] + values[k][j]
                if (not reach[i][j]) or (candidate > values[i][j]):
                    values[i][j] = candidate
                    reach[i][j] = True
                    next_node[i][j] = next_node[i][k]
        history.append(_copy_matrix(values))

    return DemoucronResult(values=values, next_node=next_node, history=history)


def build_path(next_node: List[List[Optional[int]]], src: int, dst: int) -> List[int]:
    """Reconstruit le chemin optimal de src vers dst (indices 0..n-1)."""
    if src < 0 or dst < 0 or src >= len(next_node) or dst >= len(next_node):
        raise IndexError("Indices src/dst hors limites.")
    if next_node[src][dst] is None:
        return []

    path = [src]
    cur = src
    while cur != dst:
        nxt = next_node[cur][dst]
        if nxt is None:
            return []
        cur = nxt
        path.append(cur)
        # Protection simple contre une boucle inattendue.
        if len(path) > len(next_node) * 2:
            raise RuntimeError("Boucle detectee pendant la reconstruction du chemin.")
    return path


def _fmt(v: float) -> str:
    if v == inf:
        return "inf"
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.3f}"


def print_matrix(matrix: Matrix) -> None:
    for row in matrix:
        print(" ".join(f"{_fmt(v):>5}" for v in row))


def demo() -> None:
    # Exemple: None signifie absence d'arc.
    graph: MaybeMatrix = [
        [None, 3, 8, 6, None, None],
        [None, None, None, 2, 6, None],
        [None, None, None, None, 1, None],
        [None, None, 2, None, None, 7],
        [None, None, None, None, None, 2],
        [None, None, None, None, None, None],
    ]

    print("=== DEMOUCRON MIN ===")
    rmin = demoucron_min(graph)
    print_matrix(rmin.values)
    pmin = build_path(rmin.next_node, 0, 5)
    print("Chemin min 1->6:", [x + 1 for x in pmin], "cout =", _fmt(rmin.values[0][5]))

    print("\n=== DEMOUCRON MAX ===")
    rmax = demoucron_max(graph)
    print_matrix(rmax.values)
    pmax = build_path(rmax.next_node, 0, 5)
    print("Chemin max 1->6:", [x + 1 for x in pmax], "valeur =", _fmt(rmax.values[0][5]))


if __name__ == "__main__":
    demo()
