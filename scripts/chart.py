#!/usr/bin/env python3
"""Generate analytics charts from processed ASTRA data.

Professional style, 150 DPI, ASTRA attribution watermark.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "processed"
CHART_DIR = ROOT / "charts"

ATTRIBUTION = "Data: ASTRA/IVZ Open Data"
DPI = 150
FIGSIZE = (12, 7)

# Professional color palette
COLORS = [
    "#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    "#06b6d4", "#e11d48", "#a855f7", "#22c55e", "#eab308",
]


def style_chart(ax, title: str, xlabel: str = "", ylabel: str = ""):
    """Apply consistent professional styling."""
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
    """Add ASTRA data attribution."""
    fig.text(0.99, 0.01, ATTRIBUTION, ha="right", va="bottom",
             fontsize=8, color="#999999", style="italic")


def save_chart(fig, name: str):
    """Save chart to PNG."""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"{name}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    size_kb = path.stat().st_size / 1024
    print(f"  Saved: {name}.png ({size_kb:.0f} KB)")


def chart_monthly_totals():
    """Chart 1: Total new registrations per year."""
    df = pd.read_csv(DATA_DIR / "monthly_totals.csv")
    yearly = df.groupby("year")["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.bar(yearly["year"].astype(str), yearly["count"], color=COLORS[0], width=0.7)

    # Add value labels on bars
    for bar, val in zip(bars, yearly["count"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1000,
                f"{val:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    style_chart(ax, "New Passenger Car Registrations in Switzerland", ylabel="Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    add_attribution(fig)
    save_chart(fig, "01_yearly_registrations")


def chart_powertrain_split():
    """Chart 2: Powertrain split over time (stacked area)."""
    df = pd.read_csv(DATA_DIR / "fuel_by_month.csv")
    # Aggregate to yearly
    yearly = df.groupby(["year", "fuel_type"])["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    # Pivot for stacked chart
    pivot = yearly.pivot(index="year", columns="fuel_type", values="count").fillna(0)

    # Calculate percentages
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Order: Petrol, Diesel, BEV, Hybrid, Other
    order = ["Petrol", "Diesel", "BEV", "Hybrid (Petrol)", "Hybrid (Diesel)", "Hydrogen", "CNG", "LPG", "Other"]
    order = [c for c in order if c in pct.columns]
    pct = pct[order]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    pct.plot.area(ax=ax, stacked=True, color=COLORS[:len(order)], alpha=0.85)

    style_chart(ax, "Powertrain Mix: Share of New Registrations", ylabel="Market Share (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.set_xlabel("")
    add_attribution(fig)
    save_chart(fig, "02_powertrain_split")


def chart_top_brands():
    """Chart 3: Top 15 brands (all-time)."""
    df = pd.read_csv(DATA_DIR / "brand_totals.csv")
    top = df.head(15)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.barh(top["brand"][::-1], top["count"][::-1], color=COLORS[0], height=0.7)

    for bar, val in zip(bars, top["count"][::-1]):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", ha="left", va="center", fontsize=9)

    style_chart(ax, "Top 15 Brands by New Registrations (2016-present)", xlabel="Total Registrations")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    add_attribution(fig)
    save_chart(fig, "03_top_brands")


def chart_manufacturer_origin():
    """Chart 4: Registrations by country/continent of origin."""
    df = pd.read_csv(DATA_DIR / "origin_totals.csv")
    # Skip "Other" for cleaner chart
    df = df[df["country"] != "Other"]
    top = df.head(12)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.barh(top["country"][::-1], top["count"][::-1], color=COLORS[2], height=0.7)

    for bar, val in zip(bars, top["count"][::-1]):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", ha="left", va="center", fontsize=9)

    style_chart(ax, "New Registrations by Manufacturer Origin (2016-present)",
                xlabel="Total Registrations")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    add_attribution(fig)
    save_chart(fig, "04_manufacturer_origin")


def chart_colors():
    """Chart 5: Vehicle colors (pie chart)."""
    df = pd.read_csv(DATA_DIR / "color_totals.csv")
    # Group small slices
    total = df["count"].sum()
    df["pct"] = df["count"] / total * 100
    main = df[df["pct"] >= 2.0].copy()
    other_count = df[df["pct"] < 2.0]["count"].sum()
    if other_count > 0:
        main = pd.concat([main, pd.DataFrame([{"color": "Other", "count": other_count, "pct": other_count / total * 100}])],
                         ignore_index=True)

    # Color map for actual car colors
    color_map = {
        "Black": "#1a1a1a", "White": "#e8e8e8", "Grey": "#808080", "Silver": "#c0c0c0",
        "Blue": "#2563eb", "Red": "#dc2626", "Green": "#16a34a", "Brown": "#8B4513",
        "Orange": "#f97316", "Yellow": "#eab308", "Purple": "#8b5cf6", "Beige": "#d4a574",
        "Gold": "#daa520", "Other": "#999999",
    }
    pie_colors = [color_map.get(c, "#999999") for c in main["color"]]

    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(
        main["count"], labels=main["color"], autopct="%1.1f%%",
        colors=pie_colors, startangle=90, pctdistance=0.85,
        textprops={"fontsize": 10}
    )
    for t in autotexts:
        t.set_fontsize(9)

    ax.set_title("Vehicle Color Distribution", fontsize=16, fontweight="bold", pad=15)
    add_attribution(fig)
    save_chart(fig, "05_colors")


def chart_private_vs_commercial():
    """Chart 6: Private vs commercial registrations."""
    df = pd.read_csv(DATA_DIR / "usage_totals.csv")

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(df["usage"], df["count"], color=COLORS[:len(df)], width=0.6)

    for bar, val in zip(bars, df["count"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f"{val:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    style_chart(ax, "Registrations by Usage Type", ylabel="Total Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    add_attribution(fig)
    save_chart(fig, "06_usage_type")


def main():
    print("=== Generating Charts ===\n")

    if not (DATA_DIR / "monthly_totals.csv").exists():
        print("ERROR: No processed data. Run process.py first.")
        return

    chart_monthly_totals()
    chart_powertrain_split()
    chart_top_brands()
    chart_manufacturer_origin()
    chart_colors()
    chart_private_vs_commercial()

    print("\nDone.")


if __name__ == "__main__":
    main()
