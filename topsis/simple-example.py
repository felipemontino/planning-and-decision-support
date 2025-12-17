
from math import sqrt
from typing import List, Dict, Tuple

def topsis_rank_states(
    states: List[Dict],
    weights: Dict[str, float] = None,
    benefit_flags: Dict[str, bool] = None,
    criteria_order: Tuple[str, ...] = ("score", "cost_per_habitant", "population")
) -> List[Dict]:
    """
    Perform TOPSIS ranking for a list of states.

    Parameters
    ----------
    states : List[Dict]
        Each dict must include:
        - 'name' (str)
        - 'score' (float or int)
        - 'cost_per_habitant' (float or int)
        - 'population' (int)
    weights : Dict[str, float], optional
        Weights for each criterion. If not provided:
        defaults to {'score': 0.6, 'cost_per_habitant': 0.4, 'population': 0.0}.
        (Population weight 0.0 means it is ignored by default.)
    benefit_flags : Dict[str, bool], optional
        Whether each criterion is a benefit (True) or a cost (False).
        Defaults to {'score': True, 'cost_per_habitant': False, 'population': True}.
    criteria_order : Tuple[str, ...], optional
        Order of criteria to use in the matrix.

    Returns
    -------
    List[Dict]
        Each dict includes:
        - 'name'
        - 'closeness' (float)
        - 'rank' (int, 1 is best)
        - original fields from input
    """

    # --- Defaults
    if weights is None:
        weights = {'score': 0.6, 'cost_per_habitant': 0.3, 'population': 0.1}
    if benefit_flags is None:
        benefit_flags = {'score': True, 'cost_per_habitant': False, 'population': True}

    # --- Validate inputs
    for c in criteria_order:
        if c not in weights:
            raise ValueError(f"Missing weight for criterion '{c}'.")
        if c not in benefit_flags:
            raise ValueError(f"Missing benefit/cost flag for criterion '{c}'.")
    for s in states:
        for c in criteria_order:
            if c not in s:
                raise ValueError(f"State '{s.get('name', '?')}' missing criterion '{c}'.")

    # --- Build decision matrix (n x m)
    names = [s['name'] for s in states]
    X = [[float(s[c]) for c in criteria_order] for s in states]
    n = len(states)
    m = len(criteria_order)

    # --- Vector normalization (column-wise)
    col_norms = []
    for j in range(m):
        norm = sqrt(sum(X[i][j] ** 2 for i in range(n)))
        col_norms.append(norm if norm != 0 else 1.0)  # avoid divide-by-zero

    R = [[X[i][j] / col_norms[j] for j in range(m)] for i in range(n)]

    # --- Normalize and apply weights (ensure weights sum to 1)
    weight_vec = [weights[c] for c in criteria_order]
    total_w = sum(weight_vec)
    if total_w <= 0:
        raise ValueError("Sum of weights must be > 0.")
    weight_vec = [w / total_w for w in weight_vec]  # normalize weights

    V = [[R[i][j] * weight_vec[j] for j in range(m)] for i in range(n)]

    # --- Ideal best (A+) and worst (A-)
    A_plus = []
    A_minus = []
    for j in range(m):
        col = [V[i][j] for i in range(n)]
        if benefit_flags[criteria_order[j]]:
            A_plus.append(max(col))
            A_minus.append(min(col))
        else:  # cost criterion
            A_plus.append(min(col))
            A_minus.append(max(col))

    # --- Distances to ideals
    def euclidean_dist(vec, ref):
        return sqrt(sum((vec[j] - ref[j]) ** 2 for j in range(m)))

    S_plus = [euclidean_dist(V[i], A_plus) for i in range(n)]
    S_minus = [euclidean_dist(V[i], A_minus) for i in range(n)]

    # --- Closeness coefficient (higher is better)
    closeness = []
    for i in range(n):
        denom = (S_plus[i] + S_minus[i])
        c_i = S_minus[i] / denom if denom != 0 else 0.0
        closeness.append(c_i)

    # --- Prepare results
    result = []
    for i in range(n):
        entry = {
            'name': names[i],
            'closeness': closeness[i],
            'score': states[i]['score'],
            'cost_per_habitant': states[i]['cost_per_habitant'],
            'population': states[i]['population']
        }
        result.append(entry)

    # --- Rank (descending by closeness)
    result_sorted = sorted(result, key=lambda d: d['closeness'], reverse=True)
    for idx, r in enumerate(result_sorted, start=1):
               r['rank'] = idx


if __name__ == "__main__":
    states = [
        {"name": "State A", "score": 78, "cost_per_habitant": 1100, "population": 2_500_000},
        {"name": "State B", "score": 85, "cost_per_habitant": 1500, "population": 4_000_000},
        {"name": "State C", "score": 72, "cost_per_habitant": 900,  "population": 1_200_000},
        {"name": "State D", "score": 90, "cost_per_habitant": 1700, "population": 3_300_000},
        {"name": "State E", "score": 80, "cost_per_habitant": 1000, "population": 2_000_000},
    ]

    # Default prioritization: high score (benefit), low cost per habitant (cost).
    # Population is included but weight=0.0 by default (ignored). Change if you want it to matter.
    ranking = topsis_rank_states(states)

    for r in ranking:
        print(f"#{r['rank']} {r['name']} — Closeness={r['closeness']:.4f} "
              f"(score={r['score']}, cost={r['cost_per_habitant']}, pop={r['population']:,})")

