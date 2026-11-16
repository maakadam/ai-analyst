"""Sanity checks that run in pandas on result tables. Each returns ok, a summary and its numbers.

Checks that need raw rows (join fan-out, edge periods, matured windows) run as SQL instead,
saved as data/check_<name>.csv in the run folder."""

from collections.abc import Iterable

import pandas as pd


def parts_sum_to_total(
    parts: Iterable[float], total: float, tolerance: float = 0.005
) -> dict:
    """Check that segment values add back to the overall total, within a tolerance.

    Use it after splitting a number by segment, to catch rows lost or counted twice.
    """
    parts_sum = float(sum(parts))
    # Compare as a relative difference so the tolerance works for counts and revenue alike.
    rel_diff = abs(parts_sum - total) / abs(total) if total else abs(parts_sum)
    ok = rel_diff <= tolerance
    verdict = "match" if ok else "do not match"
    return {
        "ok": ok,
        "summary": (
            f"The parts sum to {parts_sum:,.2f} against a total of {total:,.2f} "
            f"({rel_diff:.2%} apart), so they {verdict}."
        ),
        "parts_sum": parts_sum,
        "total": total,
        "relative_difference": rel_diff,
        "tolerance": tolerance,
    }


def stable_over_time(
    df: pd.DataFrame, date_col: str, value_col: str, freq: str = "M",
    tolerance: float = 0.10, window: int = 3, min_rows: int = 20,
) -> dict:
    """Check whether `value_col` is recorded the same way in every period of `date_col`.

    Use it before comparing periods, so a change in how data is logged is not read as a real change.
    It tracks one level per period: the share of True for a yes/no field, the median for a
    numeric field (such as a gap between two dates), and otherwise the
    share holding the most common value. A break is a period whose level moves away from
    the median of the `window` periods before it by more than `tolerance` (a share for
    shares, relative for medians) and by more than three standard errors, and stays moved
    in the next period. The last period has no next one, so it breaks only on twice that
    step. Periods with fewer than `min_rows` rows are skipped.

    A break says the field changed, not why. Logging changes and real changes in behaviour
    or mix both show here; test a subset where the mix is steady before calling it logging.
    """
    values = df[value_col]
    periods = pd.to_datetime(df[date_col]).dt.to_period(freq)
    counts = periods.value_counts().sort_index()
    kept = counts[counts >= min_rows].index
    # Pick what to track. Each kind of field gets a level that steps when its logging changes.
    grouped = values.groupby(periods)
    if pd.api.types.is_bool_dtype(values):
        measure, relative = "share True", False
        level = values.astype(float).groupby(periods).mean()
    elif pd.api.types.is_numeric_dtype(values):
        measure, relative = "median", True
        level = grouped.median()
        # Standard error of a median, from the spread (MAD) of each period.
        spread = grouped.apply(lambda v: 1.4826 * (v - v.median()).abs().median())
    else:
        usual = values.mode().iloc[0]
        measure, relative = f"share holding {usual}", False
        level = (values == usual).groupby(periods).mean()
    level = level.reindex(kept).sort_index()
    n = counts.reindex(level.index)
    sparse = [str(x) for x in counts.index.difference(kept)]
    if len(level) < 2:
        return {
            "ok": False,
            "summary": (f"{value_col} has fewer than two periods with {min_rows} or more rows, "
                        f"so stability cannot be judged."),
            "measure": measure, "first_break": None, "breaks": [], "largest_step": None,
            "level_by_period": level, "skipped_periods": sparse, "tolerance": tolerance,
        }
    # Compare each period with the recent level, not the first period, so a step stands
    # out even after an earlier one, and a slow drift is not mistaken for a break.
    recent = level.shift(1).rolling(window, min_periods=1).median()
    if relative:
        se = 1.253 * spread.reindex(level.index) / n ** 0.5
        threshold = pd.concat([tolerance * recent.abs(), 3 * se], axis=1).max(axis=1)
    else:
        se = (recent * (1 - recent) / n) ** 0.5
        threshold = (3 * se).clip(lower=tolerance)
    gap = (level - recent).abs()
    beyond = gap > threshold
    # A change in logging persists: the next period stays away from the same old level.
    nxt = (level.shift(-1) - recent).abs() > threshold
    is_last = pd.Series(level.index == level.index[-1], index=level.index)
    moved = gap[(beyond & nxt) | (is_last & (gap > 2 * threshold))].dropna()
    scaled = (gap / recent.abs().where(recent != 0)) if relative else gap
    scaled = scaled.dropna()
    if scaled.empty:
        largest = None
    else:
        at = scaled.idxmax()
        largest = {"period": str(at), "from": float(recent[at]), "to": float(level[at]),
                   "size": float(scaled[at])}
    ok = moved.empty

    def fmt(x):
        return f"{x:,.1f}" if relative else f"{x:.0%}"

    if ok:
        step = (f"; largest step {fmt(largest['from'])} to {fmt(largest['to'])} in {largest['period']}"
                if largest else "")
        summary = (f"{value_col} ({measure}) shows no lasting step beyond {tolerance:.0%} of its "
                   f"recent level across all {len(level)} periods{step}, so the periods can be compared.")
    else:
        first = moved.index[0]
        summary = (f"{value_col} ({measure}) steps from {fmt(recent[first])} to "
                   f"{fmt(level[first])} in {first} and stays moved, so it changes inside the window "
                   f"({len(moved)} of {len(level)} periods break); find out whether logging or "
                   f"behaviour changed before comparing across it.")
    if sparse:
        summary += f" Skipped {len(sparse)} periods with fewer than {min_rows} rows."
    return {
        "ok": ok,
        "summary": summary,
        "measure": measure,
        "first_break": str(moved.index[0]) if not moved.empty else None,
        "breaks": [str(x) for x in moved.index],
        "largest_step": largest,
        "level_by_period": level,
        "skipped_periods": sparse,
        "tolerance": tolerance,
    }

