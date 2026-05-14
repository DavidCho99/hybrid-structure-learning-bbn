from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


def _setup_matplotlib() -> None:
    # Avoid warnings/errors when the default config dir isn't writable.
    mpl_dir = Path(tempfile.gettempdir()) / "mplconfig"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))

    import matplotlib

    matplotlib.use("Agg")


def _method_label(algorithm: str) -> str:
    algo = algorithm.strip()
    if algo.startswith("MMHC"):
        return "MMHC"
    if algo.startswith("H2PC"):
        return "H2PC"
    if "ARGES" in algo:
        return "ARGES-like"
    return algo


def _format_float(value: object, decimals: int = 4, commas: bool = True) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    try:
        number = float(value)
    except Exception:
        return str(value)
    return f"{number:,.{decimals}f}" if commas else f"{number:.{decimals}f}"


def _format_int(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    try:
        number = int(value)
    except Exception:
        return str(value)
    return f"{number:,}"


def render_head_to_head_table(summary_csv: Path, output_png: Path, title: str = "HEAD-TO-HEAD RESULTS") -> Path:
    _setup_matplotlib()

    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Rectangle

    df = pd.read_csv(summary_csv)
    required = {"Algorithm", "BIC", "Total Runtime (s)", "Edge Count", "Prediction Accuracy"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing columns in {summary_csv}: {sorted(missing)}")

    view = pd.DataFrame(
        {
            "Method": df["Algorithm"].map(_method_label),
            "BIC": pd.to_numeric(df["BIC"], errors="coerce"),
            "Total Runtime (s)": pd.to_numeric(df["Total Runtime (s)"], errors="coerce"),
            "Edge Count": pd.to_numeric(df["Edge Count"], errors="coerce"),
            "Prediction Accuracy": pd.to_numeric(df["Prediction Accuracy"], errors="coerce"),
        }
    )

    order = ["MMHC", "H2PC", "ARGES-like"]
    view["__order"] = view["Method"].apply(lambda m: order.index(m) if m in order else 999)
    view = view.sort_values(["__order", "Method"]).drop(columns="__order").reset_index(drop=True)

    best_bic_row = int(view["BIC"].idxmax()) if view["BIC"].notna().any() else -1
    best_runtime_row = int(view["Total Runtime (s)"].idxmin()) if view["Total Runtime (s)"].notna().any() else -1
    best_acc_row = int(view["Prediction Accuracy"].idxmax()) if view["Prediction Accuracy"].notna().any() else -1
    max_edges_row = int(view["Edge Count"].idxmax()) if view["Edge Count"].notna().any() else -1

    columns = [
        ("Method", "Method"),
        ("BIC\n(Model Fit)", "BIC"),
        ("Total\nRuntime (s)", "Total Runtime (s)"),
        ("Edge\nCount", "Edge Count"),
        ("Prediction\nAccuracy", "Prediction Accuracy"),
    ]

    # Colors roughly matching the reference.
    header_bg = "#dfe4ea"
    grid_color = "#9aa0a6"
    cell_bg = "#f5f6f7"
    bic_color = "#2b7a86"
    speed_color = "#d47a2d"
    acc_color = "#2b7a86"
    edge_color = "#d47a2d"
    failed_color = "#6b6f76"

    highlight = {
        ("BIC", best_bic_row): (bic_color, "Best Model Fit"),
        ("Total Runtime (s)", best_runtime_row): (speed_color, "Maximum Speed"),
        ("Prediction Accuracy", best_acc_row): (acc_color, "Highest Prediction\nAccuracy"),
        ("Edge Count", max_edges_row): (edge_color, None),
    }

    # Figure geometry (in relative units).
    col_widths = [1.35, 1.85, 1.45, 1.10, 1.60]
    row_height = 1.0
    header_height = 0.9
    title_height = 0.75
    n_rows = len(view)
    total_w = float(sum(col_widths))
    total_h = title_height + header_height + n_rows * row_height + 0.25

    fig = plt.figure(figsize=(total_w * 1.05, total_h * 0.75), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    ax.axis("off")

    # Title.
    ax.text(
        total_w / 2,
        total_h - title_height / 2,
        title,
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#111111",
        family="DejaVu Sans",
    )

    table_top = total_h - title_height

    # Header row background.
    ax.add_patch(Rectangle((0, table_top - header_height), total_w, header_height, facecolor=header_bg, edgecolor=grid_color, linewidth=1.2))

    # Column boundaries.
    x_positions = [0.0]
    for w in col_widths:
        x_positions.append(x_positions[-1] + w)

    for x in x_positions:
        ax.plot([x, x], [table_top - header_height - n_rows * row_height, table_top], color=grid_color, linewidth=1.2)

    # Row boundaries.
    ax.plot([0, total_w], [table_top, table_top], color=grid_color, linewidth=1.2)
    ax.plot([0, total_w], [table_top - header_height, table_top - header_height], color=grid_color, linewidth=1.2)
    for i in range(n_rows + 1):
        y = table_top - header_height - i * row_height
        ax.plot([0, total_w], [y, y], color=grid_color, linewidth=1.0)

    # Header labels.
    for col_idx, (header, _) in enumerate(columns):
        x0, x1 = x_positions[col_idx], x_positions[col_idx + 1]
        ax.text(
            (x0 + x1) / 2,
            table_top - header_height / 2,
            header,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#222222",
        )

    # Cell backgrounds + values.
    for row_idx in range(n_rows):
        y_top = table_top - header_height - row_idx * row_height
        y_bottom = y_top - row_height
        ax.add_patch(Rectangle((0, y_bottom), total_w, row_height, facecolor=cell_bg, edgecolor="none"))

        for col_idx, (_, key) in enumerate(columns):
            x0, x1 = x_positions[col_idx], x_positions[col_idx + 1]
            cx = (x0 + x1) / 2
            cy = (y_top + y_bottom) / 2

            value = view.loc[row_idx, key]
            if key == "Method":
                text = str(value)
                ax.text(cx, cy, text, ha="center", va="center", fontsize=12, fontweight="bold", color="#111111")
                continue

            if key == "Edge Count":
                text = _format_int(value)
            elif key == "Total Runtime (s)":
                text = _format_float(value, decimals=4, commas=False)
            elif key == "Prediction Accuracy":
                text = _format_float(value, decimals=4, commas=False)
            else:  # BIC
                text = _format_float(value, decimals=4, commas=True)

            # Special-case "failed" empty graph.
            edge_count = int(view.loc[row_idx, "Edge Count"]) if not np.isnan(view.loc[row_idx, "Edge Count"]) else None
            is_failed = key == "Edge Count" and edge_count == 0

            hl = highlight.get((key, row_idx))
            if is_failed:
                box_color = failed_color
                caption = "No edges learned"
            elif hl is not None:
                box_color, caption = hl
            else:
                box_color = None
                caption = None

            if box_color is not None:
                pad_x = (x1 - x0) * 0.12
                pad_y = row_height * 0.18
                box_w = (x1 - x0) - 2 * pad_x
                box_h = row_height - 2 * pad_y
                ax.add_patch(
                    FancyBboxPatch(
                        (x0 + pad_x, y_bottom + pad_y),
                        box_w,
                        box_h,
                        boxstyle="round,pad=0.02,rounding_size=0.12",
                        linewidth=0.0,
                        facecolor=box_color,
                        alpha=0.95,
                    )
                )
                ax.text(
                    cx,
                    y_bottom + pad_y + box_h * (0.62 if caption else 0.5),
                    text,
                    ha="center",
                    va="center",
                    fontsize=11,
                    fontweight="bold",
                    color="white",
                )
                if caption:
                    ax.text(
                        cx,
                        y_bottom + pad_y + box_h * 0.22,
                        caption,
                        ha="center",
                        va="center",
                        fontsize=8.2,
                        fontweight="bold",
                        color="white",
                        linespacing=1.0,
                    )
            else:
                ax.text(cx, cy, text, ha="center", va="center", fontsize=11, color="#111111")

    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return output_png


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Render a head-to-head results table PNG from results_summary.csv")
    parser.add_argument("--summary-csv", default="results_summary.csv")
    parser.add_argument("--output", default="head_to_head_results.png")
    args = parser.parse_args()

    out = render_head_to_head_table(Path(args.summary_csv), Path(args.output))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()

