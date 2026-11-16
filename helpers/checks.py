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
    per_period: pd.DataFrame, name: str, kind: str = "share",
    tolerance: float = 0.10, window: int = 3, min_rows: int = 20,
) -> dict:
    """Check whether a field is recorded the same way in every period.

    Use it before comparing periods, so a change in how data is logged is not read as a real change.
    Takes one row per period, as an aggregate SQL query returns it: `period`, `n` (rows in the
    period) and `level`. For kind "share", level is the share of rows holding a yes/no value or
    the value most common over the whole window. For kind "median", level is the period's median and a `spread`
    column holds its median absolute deviation. A break is a period whose level moves away from
    the median of the `window` periods before it by more than `tolerance` (a share for
    shares, relative for medians) and by more than three standard errors, and stays moved
    in the next period. The last period has no next one, so it breaks only on twice that
    step. Periods with fewer than `min_rows` rows are skipped.

    A break says the field changed, not why. Logging changes and real changes in behaviour
    or mix both show here; test a subset where the mix is steady before calling it logging.
    """
    if kind not in ("share", "median"):
        raise ValueError('kind must be "share" or "median"')
    periods = per_period["period"].astype(str)
    # Periods sort as text, so only YYYY-MM keeps them in time order.
    if not periods.str.fullmatch(r"\d{4}-\d{2}").all():
        raise ValueError("period must be written YYYY-MM, e.g. to_char(month, 'YYYY-MM') in SQL")
    if periods.duplicated().any():
        raise ValueError("each period must appear once")
    if kind == "share" and not per_period["level"].astype(float).between(0, 1).all():
        raise ValueError("a share level must be between 0 and 1, not a percent")
    if kind == "median" and "spread" not in per_period.columns:
        raise ValueError('kind "median" needs a spread column (the median absolute deviation)')
    table = per_period.assign(period=periods).set_index("period").sort_index()
    counts = table["n"]
    kept = counts[counts >= min_rows].index
    relative = kind == "median"
    measure = "median" if relative else "share"
    level = table["level"].astype(float).reindex(kept)
    if relative:
        # Standard error of a median, from the spread (MAD) of each period.
        spread = 1.4826 * table["spread"].astype(float)
    n = counts.reindex(level.index)
    sparse = [str(x) for x in counts.index.difference(kept)]
    if len(level) < 2:
        return {
            "ok": False,
            "summary": (f"{name} has fewer than two periods with {min_rows} or more rows, "
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
        summary = (f"{name} ({measure}) shows no lasting step beyond {tolerance:.0%} of its "
                   f"recent level across all {len(level)} periods{step}, so the periods can be compared.")
    else:
        first = moved.index[0]
        summary = (f"{name} ({measure}) steps from {fmt(recent[first])} to "
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

