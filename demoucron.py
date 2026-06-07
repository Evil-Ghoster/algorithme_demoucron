from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import List, Optional, Tuple

Matrix = List[List[float]]
MaybeMatrix = List[List[Optional[float]]]

# Constante pour détection de cycles
INF = float("inf")

class DemoucronError(Exception):
    """Exception personnalisée pour les erreurs de l'algorithme."""
    pass

@dataclass
class DemoucronResult:
    values: Matrix
    next_node: List[List[Optional[int]]]
    history: List[Matrix]
    negative_cycle_detected: bool = False
    positive_cycle_detected: bool = False

def _copy_matrix(m: Matrix) -> Matrix:
    return [row[:] for row in m]

def _validate_square(matrix: MaybeMatrix) -> int:
    n = len(matrix)
    if n == 0:
        raise ValueError("La matrice ne peut pas être vide.")
    if any(len(row) != n for row in matrix):
        raise ValueError("La matrice doit être carrée (n x n).")
    return n

def demoucron_min(
    matrix: MaybeMatrix, detect_negative_cycles: bool = True
) -> DemoucronResult:
    """
    Version minimisation (absence d'arc = +inf).
    Si detect_negative_cycles est True, lève DemoucronError si un cycle négatif
    est détecté (distance sur la diagonale devient < 0 après exécution).
    """
    n = _validate_square(matrix)

    values: Matrix = [[INF] * n for _ in range(n)]
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

    negative_cycle = False
    if detect_negative_cycles:
        for i in range(n):
            if values[i][i] < 0:
                negative_cycle = True
                break

    return DemoucronResult(
        values=values,
        next_node=next_node,
        history=history,
        negative_cycle_detected=negative_cycle,
    )

def demoucron_max(
    matrix: MaybeMatrix, detect_positive_cycles: bool = True
) -> DemoucronResult:
    """
    Version maximisation (absence d'arc = 0).
    Si detect_positive_cycles est True, lève DemoucronError si un cycle positif
    est détecté (distance sur la diagonale devient > 0 après exécution).
    """
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

    positive_cycle = False
    if detect_positive_cycles:
        for i in range(n):
            if values[i][i] > 0:
                positive_cycle = True
                break

    return DemoucronResult(
        values=values,
        next_node=next_node,
        history=history,
        positive_cycle_detected=positive_cycle,
    )

def build_path(
    next_node: List[List[Optional[int]]], src: int, dst: int, max_steps: int = 1000
) -> List[int]:
    """Reconstruit le chemin optimal de src vers dst (indices 0..n-1)."""
    n = len(next_node)
    if not (0 <= src < n and 0 <= dst < n):
        raise IndexError("Indices src/dst hors limites.")
    if next_node[src][dst] is None:
        return []

    path = [src]
    cur = src
    steps = 0
    while cur != dst:
        nxt = next_node[cur][dst]
        if nxt is None:
            return []
        cur = nxt
        path.append(cur)
        steps += 1
        if steps > max_steps:
            raise RuntimeError("Boucle détectée pendant la reconstruction du chemin.")
    return path