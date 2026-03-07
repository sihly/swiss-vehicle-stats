#!/usr/bin/env python3
"""Generate analytics charts from processed ASTRA data.

SVG output, professional style, dynamic attribution.
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

FIGSIZE = (12, 7)

# Professional color palette
COLORS = [
    "#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    "#06b6d4", "#e11d48", "#a855f7", "#22c55e", "#eab308",
]


def get_repo_url() -> str:
    """Get repo URL from environment or git remote."""
    # GitHub Actions
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        return f"https://github.com/{repo}"
    # Local: parse git remote
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        # Convert SSH to HTTPS
        if url.startswith("git@"):
            url = url.replace(":", "/").replace("git@", "https://")
        return url.removesuffix(".git")
    except Exception:
        return ""


def get_attribution() -> str:
    """Build attribution string."""
    from datetime import date
    repo = get_repo_url()
    parts = [f"Data: ASTRA/IVZ Open Data | Generated {date.today()}"]
    if repo:
        parts.append(repo)
    return " | ".join(parts)


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
    """Add attribution footer."""
    fig.text(0.99, 0.01, get_attribution(), ha="right", va="bottom",
             fontsize=7, color="#999999", style="italic")


def save_chart(fig, name: str):
    """Save chart to SVG."""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"{name}.svg"
    fig.savefig(path, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    size_kb = path.stat().st_size / 1024
    print(f"  Saved: {name}.svg ({size_kb:.0f} KB)")


def chart_yearly_registrations():
    """Total new registrations per year."""
    df = pd.read_csv(DATA_DIR / "monthly_totals.csv")
    yearly = df.groupby("year")["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.bar(yearly["year"].astype(str), yearly["count"], color=COLORS[0], width=0.7)

    for bar, val in zip(bars, yearly["count"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1000,
                f"{val:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    style_chart(ax, "New Passenger Car Registrations in Switzerland", ylabel="Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    add_attribution(fig)
    save_chart(fig, "01_yearly_registrations")


def chart_powertrain_absolute():
    """Powertrain mix as absolute stacked bar (annual)."""
    df = pd.read_csv(DATA_DIR / "fuel_by_month.csv")
    yearly = df.groupby(["year", "fuel_type"])["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    # Order powertrain types
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

    style_chart(ax, "New Registrations by Powertrain (Absolute)", ylabel="Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    add_attribution(fig)
    save_chart(fig, "02_powertrain_absolute")


def chart_top_brands():
    """Top 15 brands (all-time)."""
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
    """Registrations by country of origin."""
    df = pd.read_csv(DATA_DIR / "origin_totals.csv")
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


def chart_winners_losers():
    """Top 5 brand gainers and losers vs prior year (latest year)."""
    path = DATA_DIR / "brand_by_year.csv"
    if not path.exists():
        print("  Skip: winners/losers (no brand_by_year data)")
        return

    df = pd.read_csv(path)
    years = sorted(df["year"].unique())
    if len(years) < 2:
        print("  Skip: winners/losers (need at least 2 years)")
        return

    # Use the latest complete year (skip partial current year if small)
    latest = years[-1]
    prev = years[-2]

    curr = df[df["year"] == latest].set_index("brand")["count"]
    prev_df = df[df["year"] == prev].set_index("brand")["count"]

    # Calculate deltas
    all_brands = set(curr.index) | set(prev_df.index)
    deltas = pd.Series({b: curr.get(b, 0) - prev_df.get(b, 0) for b in all_brands})
    deltas = deltas.sort_values()

    # Top 5 losers + top 5 winners
    losers = deltas.head(5)
    winners = deltas.tail(5)
    combined = pd.concat([losers, winners])

    fig, ax = plt.subplots(figsize=FIGSIZE)
    colors_list = ["#dc2626" if v < 0 else "#16a34a" for v in combined.values]
    bars = ax.barh(combined.index, combined.values, color=colors_list, height=0.7)

    for bar, val in zip(bars, combined.values):
        offset = 50 if val >= 0 else -50
        ha = "left" if val >= 0 else "right"
        ax.text(bar.get_width() + offset, bar.get_y() + bar.get_height() / 2,
                f"{val:+,.0f}", ha=ha, va="center", fontsize=9, fontweight="bold")

    ax.axvline(x=0, color="black", linewidth=0.8)
    style_chart(ax, f"Brand Winners & Losers: {int(latest)} vs {int(prev)}",
                xlabel="Change in Registrations")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:+,.0f}"))
    add_attribution(fig)
    save_chart(fig, "05_winners_losers")


def chart_colors():
    """Vehicle color distribution (pie)."""
    path = DATA_DIR / "color_totals.csv"
    if not path.exists():
        print("  Skip: colors (no data)")
        return

    df = pd.read_csv(path)
    total = df["count"].sum()
    df["pct"] = df["count"] / total * 100
    main = df[df["pct"] >= 2.0].copy()
    other_count = df[df["pct"] < 2.0]["count"].sum()
    if other_count > 0:
        main = pd.concat([main, pd.DataFrame([{"color": "Other", "count": other_count,
                          "pct": other_count / total * 100}])], ignore_index=True)

    color_map = {
        "Black": "#1a1a1a", "White": "#e8e8e8", "Grey": "#808080", "Silver": "#c0c0c0",
        "Blue": "#2563eb", "Red": "#dc2626", "Green": "#16a34a", "Brown": "#8B4513",
        "Orange": "#f97316", "Yellow": "#eab308", "Purple": "#8b5cf6", "Beige": "#d4a574",
        "Gold": "#daa520", "Other": "#999999", "Multicolor": "#ff69b4",
    }
    pie_colors = [color_map.get(c, "#999999") for c in main["color"]]

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.pie(main["count"], labels=main["color"], autopct="%1.1f%%",
           colors=pie_colors, startangle=90, pctdistance=0.85, textprops={"fontsize": 10})
    ax.set_title("Vehicle Color Distribution", fontsize=16, fontweight="bold", pad=15)
    add_attribution(fig)
    save_chart(fig, "06_colors")


def chart_usage():
    """Private vs commercial registrations."""
    path = DATA_DIR / "usage_totals.csv"
    if not path.exists():
        print("  Skip: usage (no data)")
        return

    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(df["usage"], df["count"], color=COLORS[:len(df)], width=0.6)

    for bar, val in zip(bars, df["count"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f"{val:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    style_chart(ax, "Registrations by Usage Type", ylabel="Total Registrations")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    add_attribution(fig)
    save_chart(fig, "07_usage_type")


def chart_drive_type():
    """AWD vs FWD vs RWD share over time."""
    path = DATA_DIR / "drive_by_month.csv"
    if not path.exists():
        print("  Skip: drive type (no data)")
        return

    df = pd.read_csv(path)
    yearly = df.groupby(["year", "drive"])["count"].sum().reset_index()
    yearly = yearly[yearly["year"] >= 2016]

    pivot = yearly.pivot(index="year", columns="drive", values="count").fillna(0)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    drive_colors = {"AWD": "#2563eb", "FWD": "#f59e0b", "RWD": "#dc2626", "Other": "#d1d5db"}
    order = [c for c in ["AWD", "FWD", "RWD", "Other"] if c in pct.columns]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    pct[order].plot.bar(ax=ax, stacked=True, color=[drive_colors.get(c, "#999") for c in order], width=0.7)

    ax.set_xticklabels([str(int(x)) for x in pct.index], rotation=0)
    style_chart(ax, "Drive Type Distribution (AWD/FWD/RWD)", ylabel="Share (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.set_xlabel("")
    add_attribution(fig)
    save_chart(fig, "08_drive_type")


def main():
    print("=== Generating Charts ===\n")

    if not (DATA_DIR / "monthly_totals.csv").exists():
        print("ERROR: No processed data. Run process.py first.")
        return

    chart_yearly_registrations()
    chart_powertrain_absolute()
    chart_top_brands()
    chart_manufacturer_origin()
    chart_winners_losers()
    chart_colors()
    chart_usage()
    chart_drive_type()

    print("\nDone.")


if __name__ == "__main__":
    main()
