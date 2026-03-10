"""
visualization_service.py

Generates both static (Matplotlib) and interactive (Vega-Lite) data visualizations.
Tasks implemented:
1. Smart Time-Series Detection
2. NLP-to-Chart Customization (via chart_type param)
3. Statistical Annotations (Avg, Peak, Low, Growth%)
4. Hybrid Interactive Rendering (Vega-Lite JSON)
"""

import io
import base64
import logging
import traceback
import json
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
import altair as alt

logger = logging.getLogger(__name__)

# ── Color palette ──────────────────────────────────────────────────────────────
COLORS = [
    "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b",
    "#ef4444", "#06b6d4", "#ec4899", "#84cc16",
    "#f97316", "#6366f1",
]

# ── Matplotlib global style ────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#f8f8fc",
    "axes.edgecolor": "#e2e8f0",
    "axes.grid": True,
    "grid.color": "#e2e8f0",
    "grid.linewidth": 0.8,
    "grid.linestyle": "--",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlecolor": "#1e293b",
    "axes.labelcolor": "#475569",
    "xtick.color": "#64748b",
    "ytick.color": "#64748b",
    "legend.framealpha": 0.9,
    "legend.edgecolor": "#e2e8f0",
    "legend.fontsize": 9,
})


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_numeric_col(series: pd.Series) -> bool:
    if series.empty:
        return False
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    if pd.api.types.is_numeric_dtype(series):
        return True
    try:
        converted = pd.to_numeric(non_null, errors="coerce")
        return converted.notna().mean() > 0.6
    except Exception:
        return False

def _is_date_col(series: pd.Series) -> bool:
    if series.empty:
        return False
    name = str(series.name).lower()
    if any(k in name for k in ["date", "time", "year", "month", "day", "created_at"]):
        return True
    non_null = series.dropna().head(10)
    if len(non_null) == 0:
        return False
    try:
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        sample = non_null.astype(str)
        pd.to_datetime(sample, errors="raise")
        return True
    except Exception:
        return False

def _detect_columns(df: pd.DataFrame) -> Tuple[Optional[str], List[str], bool]:
    numeric_cols = [c for c in df.columns if _is_numeric_col(df[c])]
    label_candidates = [c for c in df.columns if c not in numeric_cols]
    date_cols = [c for c in label_candidates if _is_date_col(df[c])]
    if date_cols:
        label_col = date_cols[0]
        is_timeseries = True
    else:
        label_col = label_candidates[0] if label_candidates else df.columns[0]
        is_timeseries = _is_date_col(df[label_col])
    value_cols = [c for c in numeric_cols if c != label_col]
    return label_col, value_cols, is_timeseries


def _suggest_chart_type(n_rows: int, n_numeric: int, is_timeseries: bool) -> str:
    if n_numeric == 0:
        return "none"
    if is_timeseries:
        return "line" if n_rows > 1 else "bar"
    if n_rows <= 8 and n_numeric == 1:
        return "pie"
    if n_rows > 25:
        return "area"
    return "bar"


def _truncate_labels(labels, max_len: int = 14) -> List[str]:
    result = []
    for v in labels:
        s = str(v)
        result.append(s[:max_len] + "\u2026" if len(s) > max_len else s)
    return result


def _format_number(val) -> str:
    try:
        val = float(val)
        if abs(val) >= 1_000_000:
            return f"{val/1_000_000:.1f}M"
        if abs(val) >= 1_000:
            return f"{val/1_000:.1f}K"
        return f"{val:,.1f}"
    except Exception:
        return str(val)


def _to_base64_png(fig: plt.Figure, dpi: int = 130) -> str:
    from matplotlib.figure import Figure
    if not isinstance(fig, Figure): return None
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def _get_numeric_values(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


# ── Interactive Rendering: Vega-Lite (Task #4) ──────────────────────────────────

def _generate_vega_spec(df: pd.DataFrame, label_col: str, numeric_cols: List[str], chart_type: str, title: str) -> Optional[Dict]:
    try:
        data = df.copy()
        is_temporal = _is_date_col(df[label_col])
        if is_temporal:
            data[label_col] = pd.to_datetime(data[label_col], errors="coerce")
            data = data.dropna(subset=[label_col])

        melted = data.melt(id_vars=[label_col], value_vars=numeric_cols, var_name="Metric", value_name="Value")
        x_type = 'temporal' if is_temporal else 'nominal'
        
        base = alt.Chart(melted).encode(
            x=alt.X(f"{label_col}:{x_type}", title=label_col),
            y=alt.Y("Value:quantitative", title="Value"),
            color=alt.Color("Metric:nominal", scale=alt.Scale(range=COLORS)),
            tooltip=[label_col, "Metric", "Value"]
        ).properties(
            title=title,
            width='container',
            height=300
        ).interactive()

        if chart_type == "line":
            chart = base.mark_line(point=True, strokeWidth=3)
        elif chart_type == "area":
            chart = base.mark_area(opacity=0.5)
        elif chart_type == "pie":
            chart = alt.Chart(df).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(f"{numeric_cols[0]}:quantitative"),
                color=alt.Color(f"{label_col}:nominal", scale=alt.Scale(range=COLORS)),
                tooltip=[label_col, numeric_cols[0]]
            ).properties(title=title)
        else:
            chart = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                xOffset="Metric:N"
            )

        return json.loads(chart.to_json())
    except Exception as e:
        print(f"[VIZ] Vega-Lite generation failed: {e}")
        return None


# ── Matplotlib Renderers ────────────────────────────────────────────────────────

MAX_ITEMS_PER_PAGE = 10  # Pagination: max bars/points per chart page


def _compute_global_stats(df: pd.DataFrame, numeric_cols: List[str], label_col: str) -> Dict[str, Dict]:
    """
    Pre-compute global statistics from the FULL dataset.
    Returns a dict keyed by column name with avg, min, max, growth, etc.
    """
    stats = {}
    for col in numeric_cols:
        vals = _get_numeric_values(df, col)
        avg_val = vals.mean()
        max_val = vals.max()
        min_val = vals.min()
        max_row_idx = int(vals.idxmax())
        min_row_idx = int(vals.idxmin())
        max_label = str(df[label_col].iloc[max_row_idx]) if max_row_idx < len(df) else ""
        min_label = str(df[label_col].iloc[min_row_idx]) if min_row_idx < len(df) else ""

        growth = None
        if len(vals) > 1:
            first_val = vals.iloc[0]
            last_val = vals.iloc[-1]
            if abs(first_val) > 1e-6:
                growth = ((last_val - first_val) / abs(first_val)) * 100

        stats[col] = {
            "avg": avg_val,
            "max": max_val,
            "min": min_val,
            "max_row_idx": max_row_idx,
            "min_row_idx": min_row_idx,
            "max_label": max_label,
            "min_label": min_label,
            "growth": growth,
        }
    return stats


def _add_statistical_annotations(
    ax, x, vals,
    col, color,
    label_col_name, value_col_name,
    index=0,
    global_stats=None,
    page_start_idx=0,
):
    """
    Adds data storytelling annotations using GLOBAL stats.
    - Average line & summary box use global values (same on every page).
    - Peak/Low arrows only appear on the page containing the actual global max/min.
    """
    if vals.empty or len(vals) < 1:
        return

    # Use global stats if provided, otherwise compute from local page data
    if global_stats and col in global_stats:
        gs = global_stats[col]
        avg_val = gs["avg"]
        global_max = gs["max"]
        global_min = gs["min"]
        global_max_row = gs["max_row_idx"]
        global_min_row = gs["min_row_idx"]
        growth = gs["growth"]
    else:
        avg_val = vals.mean()
        global_max = vals.max()
        global_min = vals.min()
        global_max_row = int(vals.idxmax())
        global_min_row = int(vals.idxmin())
        growth = None
        if len(vals) > 1:
            first_val = vals.iloc[0]
            last_val = vals.iloc[-1]
            if abs(first_val) > 1e-6:
                growth = ((last_val - first_val) / abs(first_val)) * 100

    page_end_idx = page_start_idx + len(vals)
    val_range = global_max - global_min if global_max != global_min else max(global_max * 0.1, 1)

    # 1. Average Line (dashed horizontal) - GLOBAL avg, same on every page
    ax.axhline(avg_val, color=color, linestyle="--", alpha=0.45, linewidth=1.2, zorder=1)
    ax.text(len(x) - 0.5, avg_val, f"  Avg: {_format_number(avg_val)}",
            va='bottom', ha='left', fontsize=7.5, fontweight='bold', color=color,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor=color, boxstyle='round,pad=0.25', linewidth=0.6))

    # 2. Peak annotation - only if the global max row is on THIS page
    if page_start_idx <= global_max_row < page_end_idx:
        local_idx = global_max_row - page_start_idx
        if local_idx < len(x):
            ax.annotate(
                f"\u25b2 Peak: {_format_number(global_max)}",
                xy=(x[local_idx], vals.iloc[local_idx]),
                xytext=(x[local_idx], vals.iloc[local_idx] + val_range * 0.18),
                fontsize=7.5, fontweight='bold', color='#059669',
                ha='center', va='bottom',
                arrowprops=dict(arrowstyle='->', color='#059669', lw=1.2),
                bbox=dict(facecolor='#ecfdf5', edgecolor='#059669', boxstyle='round,pad=0.3', linewidth=0.6),
                zorder=15
            )

    # 3. Low annotation - only if the global min row is on THIS page
    if page_start_idx <= global_min_row < page_end_idx and global_min_row != global_max_row:
        local_idx = global_min_row - page_start_idx
        if local_idx < len(x):
            ax.annotate(
                f"\u25bc Low: {_format_number(global_min)}",
                xy=(x[local_idx], vals.iloc[local_idx]),
                xytext=(x[local_idx], vals.iloc[local_idx] - val_range * 0.18),
                fontsize=7.5, fontweight='bold', color='#dc2626',
                ha='center', va='top',
                arrowprops=dict(arrowstyle='->', color='#dc2626', lw=1.2),
                bbox=dict(facecolor='#fef2f2', edgecolor='#dc2626', boxstyle='round,pad=0.3', linewidth=0.6),
                zorder=15
            )

    # 4. Statistical Summary Box - GLOBAL stats, same on every page
    summary_parts = [f"Avg: {_format_number(avg_val)}"]
    summary_parts.append(f"Peak: {_format_number(global_max)}")
    summary_parts.append(f"Low: {_format_number(global_min)}")

    if growth is not None:
        sign = "+" if growth >= 0 else ""
        summary_parts.append(f"{sign}{growth:.1f}% growth")

    summary_text = f"{col}:  " + "  |  ".join(summary_parts)

    y_pos = 1.02 + (index * 0.06)
    ax.text(0.0, y_pos, summary_text, transform=ax.transAxes,
            fontsize=8, fontweight='bold', color=color,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='#cbd5e1', boxstyle='round,pad=0.4', linewidth=0.6))

    # 5. Add X and Y axis labels
    ax.set_xlabel(label_col_name, fontsize=10, fontweight='bold', color='#475569', labelpad=8)
    ax.set_ylabel(value_col_name, fontsize=10, fontweight='bold', color='#475569', labelpad=8)


def _paginate_chart(df, label_col, numeric_cols, title, chart_fn):
    """
    Splits large datasets into paginated chart pages (max MAX_ITEMS_PER_PAGE per page),
    computes GLOBAL stats once, passes them to each page for consistent annotations.
    """
    total_rows = len(df)

    # Pre-compute global stats from the FULL dataset
    global_stats = _compute_global_stats(df, numeric_cols, label_col)

    if total_rows <= MAX_ITEMS_PER_PAGE:
        return chart_fn(df, label_col, numeric_cols, title, page_info=None,
                        global_stats=global_stats, page_start_idx=0)

    num_pages = (total_rows + MAX_ITEMS_PER_PAGE - 1) // MAX_ITEMS_PER_PAGE
    page_images = []

    for page_num in range(num_pages):
        start = page_num * MAX_ITEMS_PER_PAGE
        end = min(start + MAX_ITEMS_PER_PAGE, total_rows)
        page_df = df.iloc[start:end].reset_index(drop=True)
        page_info = f"Page {page_num + 1} of {num_pages}  (items {start+1}\u2013{end} of {total_rows})"

        png_b64 = chart_fn(page_df, label_col, numeric_cols, title,
                           page_info=page_info, global_stats=global_stats, page_start_idx=start)
        if png_b64:
            page_images.append(png_b64)

    if not page_images:
        return None
    if len(page_images) == 1:
        return page_images[0]

    # Stitch images vertically
    from PIL import Image
    pil_images = []
    for b64 in page_images:
        img_data = base64.b64decode(b64)
        pil_images.append(Image.open(io.BytesIO(img_data)))

    total_width = max(img.width for img in pil_images)
    total_height = sum(img.height for img in pil_images)

    stitched = Image.new('RGB', (total_width, total_height), color=(255, 255, 255))
    y_offset = 0
    for img in pil_images:
        stitched.paste(img, (0, y_offset))
        y_offset += img.height

    buf = io.BytesIO()
    stitched.save(buf, format="PNG", dpi=(130, 130))
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _bar_chart(df, label_col, numeric_cols, title, page_info=None, global_stats=None, page_start_idx=0):
    n_cols = len(numeric_cols)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = list(range(len(df)))
    bar_width = min(0.7 / n_cols, 0.45)
    for i, col in enumerate(numeric_cols):
        vals = _get_numeric_values(df, col)
        offset = [xi + i * bar_width - (n_cols - 1) * bar_width / 2 for xi in x]
        ax.bar(offset, vals, width=bar_width * 0.9, color=COLORS[i % len(COLORS)], label=col, edgecolor="white", linewidth=0.5)
        # Add value labels on bar tops
        for xi, vi in zip(offset, vals):
            if vi > 0:
                ax.text(xi, vi + (vals.max() * 0.01), _format_number(vi),
                        ha='center', va='bottom', fontsize=7, color='#475569', fontweight='medium')
        # Add insights (using global stats)
        value_label = col if n_cols > 1 else ', '.join(numeric_cols)
        _add_statistical_annotations(ax, x, vals, col, COLORS[i % len(COLORS)], label_col, value_label, i,
                                     global_stats=global_stats, page_start_idx=page_start_idx)
    ax.set_xticks(x)
    ax.set_xticklabels(_truncate_labels(df[label_col]), rotation=35, ha="right", fontsize=9)
    ax.set_title(title, pad=35 + len(numeric_cols) * 15)
    if n_cols > 1: ax.legend(loc='upper right', fontsize=8)

    if page_info:
        fig.text(0.5, 0.01, page_info, ha='center', fontsize=8, color='#94a3b8', fontstyle='italic')

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return _to_base64_png(fig)


def _line_chart(df, label_col, numeric_cols, title, page_info=None, global_stats=None, page_start_idx=0):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = list(range(len(df)))
    for i, col in enumerate(numeric_cols):
        vals = _get_numeric_values(df, col)
        ax.plot(x, vals, marker="o", markersize=5, linewidth=2.2, color=COLORS[i % len(COLORS)], label=col)
        value_label = col if len(numeric_cols) > 1 else ', '.join(numeric_cols)
        _add_statistical_annotations(ax, x, vals, col, COLORS[i % len(COLORS)], label_col, value_label, i,
                                     global_stats=global_stats, page_start_idx=page_start_idx)
    ax.set_xticks(x)
    labels = df[label_col].dt.strftime('%b %d') if _is_date_col(df[label_col]) else df[label_col]
    ax.set_xticklabels(_truncate_labels(labels), rotation=35, ha="right", fontsize=9)
    ax.set_title(title, pad=35 + len(numeric_cols) * 15)
    if len(numeric_cols) > 1: ax.legend(loc='upper right', fontsize=8)

    if page_info:
        fig.text(0.5, 0.01, page_info, ha='center', fontsize=8, color='#94a3b8', fontstyle='italic')

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return _to_base64_png(fig)


def _area_chart(df, label_col, numeric_cols, title, page_info=None, global_stats=None, page_start_idx=0):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = list(range(len(df)))
    for i, col in enumerate(numeric_cols):
        vals = _get_numeric_values(df, col)
        ax.fill_between(x, vals, alpha=0.25, color=COLORS[i % len(COLORS)])
        ax.plot(x, vals, linewidth=2.2, color=COLORS[i % len(COLORS)], label=col)
        value_label = col if len(numeric_cols) > 1 else ', '.join(numeric_cols)
        _add_statistical_annotations(ax, x, vals, col, COLORS[i % len(COLORS)], label_col, value_label, i,
                                     global_stats=global_stats, page_start_idx=page_start_idx)
    ax.set_xticks(x)
    ax.set_xticklabels(_truncate_labels(df[label_col]), rotation=35, ha="right", fontsize=9)
    ax.set_title(title, pad=35 + len(numeric_cols) * 15)
    if len(numeric_cols) > 1: ax.legend(loc='upper right', fontsize=8)

    if page_info:
        fig.text(0.5, 0.01, page_info, ha='center', fontsize=8, color='#94a3b8', fontstyle='italic')

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return _to_base64_png(fig)


def _pie_chart(df, label_col, value_col, title):
    fig, ax = plt.subplots(figsize=(7, 5))
    vals = _get_numeric_values(df, value_col)
    ax.pie(vals, labels=_truncate_labels(df[label_col]), colors=COLORS, autopct='%1.1f%%', startangle=140)
    ax.set_title(title)
    return _to_base64_png(fig)


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_chart(
    columns: List[str],
    data: List[Dict[str, Any]],
    query: str = "",
    chart_type: Optional[str] = None,
) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Returns (base64_png_image, vega_lite_json_spec).
    """
    try:
        if not columns or not data: return None, None
        df = pd.DataFrame(data)
        existing = [c for c in columns if c in df.columns]
        if not existing: return None, None
        df = df[existing].head(100)

        label_col, numeric_cols, is_timeseries = _detect_columns(df)
        if not numeric_cols: return None, None

        title = query.strip().capitalize()[:70]

        selected_type = chart_type if chart_type and chart_type != "none" else _suggest_chart_type(len(df), len(numeric_cols), is_timeseries)

        print(f"[VIZ] suggest_type={selected_type}, timeseries={is_timeseries}")

        # 1. Generate Interactive Spec
        vega_spec = _generate_vega_spec(df, label_col, numeric_cols, selected_type, title)

        # 2. Generate Static PNG with Statistical Annotations (paginated, global stats)
        png_out = None
        if selected_type == "pie":
            png_out = _pie_chart(df, label_col, numeric_cols[0], title)
        elif selected_type == "line":
            png_out = _paginate_chart(df, label_col, numeric_cols, title, _line_chart)
        elif selected_type == "area":
            png_out = _paginate_chart(df, label_col, numeric_cols, title, _area_chart)
        else:
            png_out = _paginate_chart(df, label_col, numeric_cols, title, _bar_chart)

        return png_out, vega_spec

    except Exception:
        print(f"[VIZ] Failed: {traceback.format_exc()}")
        return None, None
