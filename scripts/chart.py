#!/usr/bin/env python3
"""Generate analytics charts from processed ASTRA data.

PNG output, professional style, dynamic attribution.
"""

import os
import subprocess
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "processed"
CHART_DIR = ROOT / "charts"

DPI = 150
FIGSIZE = (12, 7)

# Professional color palette
COLORS = [
    "#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    "#06b6d4", "#e11d48", "#a855f7", "#22c55e", "#eab308",
]


def get_repo_url() -> str:
    """Get repo URL from environment or git remote."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        return f"https://github.com/{repo}"
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        if url.startswith("git@"):
            url = url.replace(":", "/").replace("git@", "https://")
        return url.removesuffix(".git")
    except Exception:
        return ""


def get_attribution() -> str:
    from datetime import date
    repo = get_repo_url()
    parts = [f"Data: ASTRA/IVZ Open Data | Generated {date.today()}"]
    if repo:
        parts.append(repo)
    return " | ".join(parts)


def style_chart(ax, title: str, xlabel: str = "", ylabel: str = ""):
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle="--")


def add_attribution(fig):
    fig.text(0.99, 0.01, get_attribution(), ha="right", va="bottom",
             fontsize=7, color="#999999", style="italic")


def save_chart(fig, name: str):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"{name}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    size_kb = path.stat().st_size / 1024
    print(f"  Saved: {name}.png ({size_kb:.0f} KB)")


def chart_yearly_registrations():
    """Total registrations as line chart with trend."""
    df = pd.read_csv(DATA_DIR / "monthly_totals.csv")
    yearly = df.groupby("year")["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(yearly["year"], yearly["count"], marker="o", linewidth=2.5,
            color=COLORS[0], markersize=8, zorder=3)
    ax.fill_between(yearly["year"], yearly["count"], alpha=0.1, color=COLORS[0])

    for _, row in yearly.iterrows():
        ax.annotate(f"{row['count']:,.0f}", (row["year"], row["count"]),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=8, fontweight="bold")

    style_chart(ax, "New Passenger Car Registrations in Switzerland\n(Fahrzeugart = Personenwagen)", ylabel="Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_xlim(yearly["year"].min() - 0.5, yearly["year"].max() + 0.5)
    add_attribution(fig)
    save_chart(fig, "01_yearly_registrations")


def chart_powertrain_absolute():
    """Powertrain mix as absolute stacked bar (annual)."""
    df = pd.read_csv(DATA_DIR / "fuel_by_month.csv")
    yearly = df.groupby(["year", "fuel_type"])["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    order = ["Petrol", "Diesel", "BEV", "PHEV", "Diesel Hybrid", "Hydrogen", "CNG", "LPG", "Other"]
    color_map = {
        "Petrol": "#6b7280", "Diesel": "#374151", "BEV": "#2563eb",
        "PHEV": "#60a5fa", "Diesel Hybrid": "#93c5fd", "Hydrogen": "#16a34a",
        "CNG": "#f59e0b", "LPG": "#f97316", "Other": "#d1d5db",
    }

    pivot = yearly.pivot(index="year", columns="fuel_type", values="count").fillna(0)
    cols = [c for c in order if c in pivot.columns]
    pivot = pivot[cols]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bottom = pd.Series(0, index=pivot.index)
    for col in cols:
        ax.bar(pivot.index.astype(str), pivot[col], bottom=bottom,
               label=col, color=color_map.get(col, "#999"), width=0.7)
        bottom = bottom + pivot[col]

    style_chart(ax, "New Registrations by Powertrain", ylabel="Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    add_attribution(fig)
    save_chart(fig, "02_powertrain_absolute")


def chart_brand_rankings():
    """Brand ranking bump chart — position over time for top brands."""
    path = DATA_DIR / "brand_by_year.csv"
    if not path.exists():
        print("  Skip: brand rankings (no data)")
        return

    df = pd.read_csv(path)
    df = df[df["year"] >= 2016]

    top_brands = df.groupby("brand")["count"].sum().nlargest(10).index.tolist()
    ranked = df[df["brand"].isin(top_brands)].copy()
    ranked["rank"] = ranked.groupby("year")["count"].rank(ascending=False, method="min")

    fig, ax = plt.subplots(figsize=(14, 8))

    for i, brand in enumerate(top_brands):
        brand_data = ranked[ranked["brand"] == brand].sort_values("year")
        color = COLORS[i % len(COLORS)]
        ax.plot(brand_data["year"], brand_data["rank"], marker="o", linewidth=2.5,
                label=brand, color=color, markersize=7, zorder=3)
        if not brand_data.empty:
            last = brand_data.iloc[-1]
            ax.annotate(brand, (last["year"], last["rank"]),
                        textcoords="offset points", xytext=(8, 0),
                        fontsize=9, fontweight="bold", color=color, va="center")

    ax.invert_yaxis()
    ax.set_yticks(range(1, 11))
    ax.set_yticklabels([f"#{i}" for i in range(1, 11)])
    style_chart(ax, "Top 10 Brand Rankings Over Time", ylabel="Position")
    ax.set_xlabel("")
    ax.legend(loc="lower left", fontsize=8, frameon=False, ncol=2)
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    add_attribution(fig)
    save_chart(fig, "03_brand_rankings")


def main():
    print("=== Generating Charts ===\n")

    if not (DATA_DIR / "monthly_totals.csv").exists():
        print("ERROR: No processed data. Run process.py first.")
        return

    chart_yearly_registrations()
    chart_powertrain_absolute()
    chart_brand_rankings()

    print("\nDone.")


if __name__ == "__main__":
    main()
