"""Compare two folders of result CSVs. Prints one line per file, never rows."""

import sys
from pathlib import Path

import pandas as pd


def same_results(old_dir, new_dir, tolerance: float = 1e-9) -> dict:
    """Check that the CSVs in `new_dir` match those in `old_dir`.

    Use it after rerunning a script into a copy, to see whether its saved results still hold.
    """
    old_dir, new_dir = Path(old_dir), Path(new_dir)
    names = sorted({p.name for p in old_dir.glob("*.csv")} | {p.name for p in new_dir.glob("*.csv")})
    files = {}
    for name in names:
        if not (new_dir / name).exists():
            files[name] = "missing from the rerun"
            continue
        if not (old_dir / name).exists():
            files[name] = "new in the rerun"
            continue
        a, b = pd.read_csv(old_dir / name), pd.read_csv(new_dir / name)
        if list(a.columns) != list(b.columns):
            files[name] = "columns differ"
        elif len(a) != len(b):
            files[name] = f"{len(a):,} rows before, {len(b):,} in the rerun"
        else:
            num = a.select_dtypes("number").columns
            an, bn = a[num], b[num].apply(pd.to_numeric, errors="coerce")
            nan_differ = bool((an.isna() != bn.isna()).any().any())
            gap = float((an - bn).abs().max().max()) if len(num) else 0.0
            text_same = a.drop(columns=num).astype(str).equals(b.drop(columns=num).astype(str))
            if nan_differ or not text_same or gap > tolerance:
                files[name] = f"values differ (largest numeric gap {gap:,.6g})"
            else:
                files[name] = "matches"
    differ = [n for n, s in files.items() if s != "matches"]
    if differ:
        summary = f"{len(differ)} of {len(files)} result files differ: " + "; ".join(f"{n}: {files[n]}" for n in differ) + "."
    else:
        summary = f"All {len(files)} result files match the rerun."
    return {"ok": not differ, "summary": summary, "files": files}


if __name__ == "__main__":
    print(same_results(sys.argv[1], sys.argv[2])["summary"])
