"""Compatibility launcher for the Django project.

This file replaces the old Flask entrypoint so the workspace remains
error-free after migration to Django.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    manage_py = base_dir / "manage.py"

    if not manage_py.exists():
        print("Error: manage.py not found. Run this file from the project root.")
        return 1

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "career_aptitude.settings")

    cmd = [sys.executable, str(manage_py), "runserver"]
    print("Starting Django server using:", " ".join(cmd))
    return subprocess.call(cmd, cwd=base_dir, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
