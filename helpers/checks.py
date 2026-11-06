"""Sanity checks for analysis results. Each returns ok, a summary and its numbers."""

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


def join_fan_out(
    left: pd.DataFrame, right: pd.DataFrame, on: str | list[str]
) -> dict:
    """Check whether joining `right` onto `left` multiplies rows.

    Use it before trusting any join; a fan-out silently inflates sums and counts.
    """
    rows_before = len(left)
    rows_after = len(left.merge(right, on=on, how="inner"))
    duplicate_keys = int(right.duplicated(subset=on).sum())
    ok = rows_after <= rows_before
    if ok:
        summary = f"The join kept {rows_after:,} of {rows_before:,} rows without fanning out."
    else:
        summary = (
            f"The join grew {rows_before:,} rows to {rows_after:,} because the "
            f"right table repeats {duplicate_keys:,} keys."
        )
    return {
        "ok": ok,
        "summary": summary,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "duplicate_keys_right": duplicate_keys,
    }


def date_boundaries(df: pd.DataFrame, col: str, freq: str = "M") -> dict:
    """Check whether the first and last periods of a date column are only partly covered.

    Use it before comparing periods, so a half month is not read as a drop.
    """
    dates = pd.to_datetime(df[col]).dropna()
    # Normalise to midnight so a timestamp late on the last day still counts as
    # covering that day when compared with the period's start and end.
    min_day, max_day = dates.min().normalize(), dates.max().normalize()
    first, last = min_day.to_period(freq), max_day.to_period(freq)
    first_partial = min_day > first.start_time.normalize()
    last_partial = max_day < last.end_time.normalize()

    partial = []
    if first_partial:
        partial.append(f"the first period ({first}) starts on {min_day.date()}")
    if last_partial:
        partial.append(f"the last period ({last}) ends on {max_day.date()}")
    if partial:
        summary = f"Partial edges in {col}: " + " and ".join(partial) + "."
    else:
        summary = f"Both edge periods of {col} ({first} and {last}) are complete."

    return {
        "ok": not partial,
        "summary": summary,
        "first_period": str(first),
        "last_period": str(last),
        "first_partial": bool(first_partial),
        "last_partial": bool(last_partial),
        "min_date": min_day.date().isoformat(),
        "max_date": max_day.date().isoformat(),
    }


def matured_only(df: pd.DataFrame, end_col: str, as_of=None) -> dict:
    """Return only the rows whose window has closed by `as_of` (today by default).

    Use it for trials or periods still running, whose outcome is not known yet.
    """
    as_of = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.today()
    ends = pd.to_datetime(df[end_col])
    kept = df[ends <= as_of]
    dropped = len(df) - len(kept)
    return {
        "ok": dropped == 0,
        "summary": (
            f"Excluded {dropped:,} of {len(df):,} rows because their window "
            f"has not closed by {as_of.date()}."
        ),
        "kept": kept,
        "dropped": dropped,
        "as_of": as_of.date().isoformat(),
    }


def stable_over_time(
    df: pd.DataFrame, date_col: str, value_col: str, freq: str = "M",
    tolerance: float = 0.25,
) -> dict:
    """Check whether `value_col` is recorded the same way in every period of `date_col`.

    Use it before comparing periods, so a change in how data is logged is not read as a real change.
    """
    periods = pd.to_datetime(df[date_col]).dt.to_period(freq)
    first = periods.min()
    usual = df.loc[periods == first, value_col].mode().iloc[0]
    # Track the share of rows holding the first period's usual value. A change in
    # how a field is logged shows as a step in that share, even when counts look normal.
    share = (df[value_col] == usual).groupby(periods).mean()
    moved = share[(share - share.iloc[0]).abs() > tolerance]
    ok = moved.empty
    if ok:
        summary = (
            f"{value_col} holds {usual} in a steady share of rows across all "
            f"{len(share)} periods, so the periods can be compared."
        )
    else:
        summary = (
            f"{value_col} holds {usual} in {share.iloc[0]:.0%} of rows in {first} "
            f"but {moved.iloc[0]:.0%} in {moved.index[0]}, so it is not recorded "
            f"the same way across the window."
        )
    return {
        "ok": ok,
        "summary": summary,
        "usual_value": usual,
        "first_break": str(moved.index[0]) if not ok else None,
        "share_by_period": share,
        "tolerance": tolerance,
    }

if __name__ == "__main__":
    subscriptions = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date"])
    result = date_boundaries(subscriptions, "start_date")
    for key, value in result.items():
        print(f"{key}: {value}")
