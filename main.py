# main.py
import numpy as np
import matplotlib.pyplot as plt
from optimization import BLWorkflow
from updatePortfolio import write_bl_allocation_to_excel, compare_portfolio_values
from monteCarlo import initialization as MCInit, monte_carlo as MonteCarlo

EXCEL_PATH = "stocks.xlsx"
SHEET_NAME = "Sheet1"
NEW_SHEET = "BL_Allocation"


def run_monte_carlo(excel_path, sheet, n_sims=1000, n_days=252):
    init = MCInit(excel_path, sheet)
    init.get_data()
    mean, cov, weights, initial_value = init.getValues()
    mc = MonteCarlo(mean, cov, weights, initial_value)
    mc.initializeEnv(n_sims, n_days)
    mc.createSim()
    norm_paths = mc.sim_matrix / initial_value
    final_norm = norm_paths[-1]
    ret = final_norm - 1.0
    return float(np.mean(ret)), float(np.std(ret)), norm_paths


def plot_side_by_side(paths_before, paths_after):
    """Display two side-by-side subplots of the simulations."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    for ax, paths, title in zip(
        axes,
        [paths_before, paths_after],
        ["Before Optimization", "After Optimization"],
    ):
        show_n = min(50, paths.shape[1])
        ax.plot(paths[:, :show_n], alpha=0.25)
        ax.axhline(1.0, color="k", lw=1, alpha=0.5)
        ax.set_title(title)
        ax.set_xlabel("Days")
        ax.set_ylabel("Normalized Portfolio Value")

    fig.suptitle("Monte Carlo Simulations — Before vs After Optimization", fontsize=13)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


def main():
    print("=== Running Black–Litterman Optimization ===")
    wf = BLWorkflow(EXCEL_PATH, sheet=SHEET_NAME)
    outputs = wf.run()
    weights = outputs["weights_series"]
    print("\nOptimized Weights:\n", weights.round(4))

    write_bl_allocation_to_excel(EXCEL_PATH, weights, holdings_sheet=SHEET_NAME, new_sheet=NEW_SHEET)

    print("\n=== Monte Carlo Simulation (Before) ===")
    r_before, risk_before, paths_before = run_monte_carlo(EXCEL_PATH, SHEET_NAME)
    print(f"Return: {r_before:.2%}, Risk: {risk_before:.2%}")

    print("\n=== Monte Carlo Simulation (After) ===")
    r_after, risk_after, paths_after = run_monte_carlo(EXCEL_PATH, NEW_SHEET)
    print(f"Return: {r_after:.2%}, Risk: {risk_after:.2%}")

    print("\n=== Comparison ===")
    print(f"Return Improvement: {r_after - r_before:.2%}")
    print(f"Risk Change: {risk_after - risk_before:.2%}")

    plot_side_by_side(paths_before, paths_after)

    diff = compare_portfolio_values(EXCEL_PATH, before_sheet=SHEET_NAME, after_sheet=NEW_SHEET)
    print("\nPer-ticker value differences:\n", diff.round(2))


if __name__ == "__main__":
    main()
