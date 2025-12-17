
from typing import List, Dict

# ---- Types ----
State = Dict[str, float]
Budgets = Dict[str, float]

def compute_state_cost(state: State) -> float:
    """Total cost = cost per habitant * population."""
    return float(state["cost_per_habitant"]) * float(state["population"])

def schedule_allow_split(states: List[State], budgets: Budgets) -> Dict[str, List[Dict]]:
    """
    Allow states to be funded across multiple quarters (split funding).
    States are processed in ranked order (given order in the list).
    
    Returns:
      {
        'q1': [{'name': str, 'allocated': float}, ...],
        'q2': [...],
        'q3': [...],
        'q4': [...],
        'remaining_budgets': {quarter: float},
        'coverage': [
            {'name': str, 'total_cost': float, 'allocated': float,
             'coverage_pct': float, 'fully_funded': bool}, ...
        ]
      }
    """
    remaining = {q: float(b) for q, b in budgets.items()}
    schedule: Dict[str, List[Dict]] = {q: [] for q in budgets.keys()}
    coverage: List[Dict] = []

    for s in states:
        name = s["name"]
        total_cost = compute_state_cost(s)
        need = total_cost
        allocated_total = 0.0

        for q in remaining.keys():  # iterate quarters in order
            if need <= 0:
                break
            if remaining[q] <= 0:
                continue

            allot = min(need, remaining[q])
            if allot > 0:
                remaining[q] -= allot
                need -= allot
                allocated_total += allot
                schedule[q].append({"name": name, "allocated": allot})

        coverage.append({
            "name": name,
            "total_cost": total_cost,
            "allocated": allocated_total,
            "coverage_pct": (allocated_total / total_cost) if total_cost > 0 else 0.0,
            "fully_funded": allocated_total >= total_cost
        })

    schedule["remaining_budgets"] = remaining
    schedule["coverage"] = coverage
    return schedule

# ---- Optional pretty-print helpers ----
def fmt_money(x: float) -> str:
    return f"{x:,.0f}"

def print_split_results(title: str, schedule: Dict[str, List[Dict]], budgets: Budgets):
    print(f"\n== {title} ==")
    for q in budgets.keys():
        print(f"{q} allocations:")
        for item in schedule[q]:
            print(f"  - {item['name']}: {fmt_money(item['allocated'])}")
        if not schedule[q]:
            print("  (none)")
    print("\nCoverage by state:")
    for c in schedule["coverage"]:
        pct = f"{c['coverage_pct']*100:.6f}%"
        print(f"  {c['name']}: allocated {fmt_money(c['allocated'])} of {fmt_money(c['total_cost'])} "
              f"({pct}); fully funded={c['fully_funded']}")
    print("\nRemaining budgets:")
    for q, r in schedule["remaining_budgets"].items():
        print(f"  {q}: {fmt_money(r)}")


# ---------------------------
#           MAIN
# ---------------------------
if __name__ == "__main__":
    # Ranked states (from your example)
    states: List[State] = [
        {"name": "State A", "score": 78, "cost_per_habitant": 1100, "population": 2_500_000},
        {"name": "State B", "score": 85, "cost_per_habitant": 1500, "population": 4_000_000},
        {"name": "State C", "score": 72, "cost_per_habitant": 900,  "population": 1_200_000},
        {"name": "State D", "score": 90, "cost_per_habitant": 1700, "population": 3_300_000},
        {"name": "State E", "score": 80, "cost_per_habitant": 1000, "population": 2_000_000},
    ]

    # Example 1: Your small budgets (will show partial coverage, mostly on State A)
    budgets_small: Budgets = {"q1": 100_000, "q2": 500_000, "q3": 890_000, "q4": 100_000}
    split_small = schedule_allow_split(states, budgets_small)
    print_split_results("Allow-split with small budgets", split_small, budgets_small)

    # Example 2: Feasible budgets (fully funds all states within one year)
    costs = {s["name"]: compute_state_cost(s) for s in states}
    budgets_feasible: Budgets = {
        "q1": costs["State A"],                              # fund A
        "q2": costs["State B"],                              # fund B
        "q3": costs["State C"] + costs["State D"],           # fund C + D
        "q4": costs["State E"],                              # fund E
    }
    split_feasible = schedule_allow_split(states, budgets_feasible)
    print_split_results("Allow-split with feasible budgets (fully funded)", split_feasible, budgets_feasible)
