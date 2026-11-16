"""Check a branch for database credentials before it is pushed. Prints names and counts, never values.

Usage:
    poetry run python helpers/check_credentials.py          # compare HEAD with origin/main
    poetry run python helpers/check_credentials.py <base>   # compare HEAD with another base

Exit 0: clean. Exit 1: a credential or connection string is in the diff or the commit
messages, or .env/.mcp.json is tracked. Exit 2: the check could not run (a POSTGRES_*
variable is not set in this shell, or git failed); that is not a pass.
"""

import os
import re
import subprocess
import sys

VARIABLES = ["POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DATABASE", "POSTGRES_PORT"]
# A connection string or an assigned password, whatever the values are.
PATTERNS = {
    "connection string": re.compile(r"postgres(?:ql)?://"),
    "password assignment": re.compile(r"password\s*[=:]\s*\S"),
}
NEVER_TRACKED = [".env", ".mcp.json"]


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, check=True)
    return result.stdout.decode("utf-8", errors="replace")


def value_pattern(name: str, value: str, host: str) -> re.Pattern:
    """How to look for one value without flagging the same text used innocently.

    The host and password are long and specific, so they count anywhere. The user and
    database name can be ordinary words, so they count only as whole words. The port is a
    short number that turns up in result tables, so it counts only next to the host or after
    "port".
    """
    v = re.escape(value)
    if name == "POSTGRES_PORT":
        return re.compile(rf"(?:{re.escape(host)}:{v}|port\s*[=:]\s*['\"]?{v})(?!\d)")
    if name in ("POSTGRES_USER", "POSTGRES_DATABASE"):
        return re.compile(rf"(?<![a-z0-9_]){v}(?![a-z0-9_])")
    return re.compile(v)


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"

    unset = [name for name in VARIABLES if not os.environ.get(name)]
    if unset:
        print(f"Not set in this shell: {', '.join(unset)}. Open the terminal where they are loaded; nothing was checked.")
        return 2
    values = {name: os.environ[name].lower() for name in VARIABLES}

    try:
        # Lowercase once, so a value is found whatever its case.
        text = (git("diff", f"{base}...HEAD") + git("log", f"{base}..HEAD", "--format=%B")).lower()
        tracked = git("ls-files", *NEVER_TRACKED).split()
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f"git failed, so nothing was checked (is '{base}' a branch here? try git fetch): {error}")
        return 2

    hits = []
    for name in VARIABLES:
        count = len(value_pattern(name, values[name], values["POSTGRES_HOST"]).findall(text))
        print(f"{name}: {count} matches")
        if count:
            hits.append(name)
    for label, pattern in PATTERNS.items():
        count = len(pattern.findall(text))
        print(f"{label}: {count} matches")
        if count:
            hits.append(label)
    print(f"tracked {' or '.join(NEVER_TRACKED)}: {len(tracked)}")
    if tracked:
        hits.append("tracked secrets file")

    if hits:
        print(f"Do not push: {', '.join(hits)}.")
        return 1
    print(f"Clean: no credentials in the diff or commit messages since {base}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
