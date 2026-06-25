#!/usr/bin/env python3
"""Entry point for the Paper-to-Notebook traditional server."""

# import os
import subprocess
# import sys
import venv

# DIR = os.path.dirname(os.path.abspath(__file__))
# VENV_DIR = os.path.join(DIR, "venv")
# VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python3")
# REQUIREMENTS = os.path.join(DIR, "requirements.txt")

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(DIR, "venv")

if os.name == "nt":
    VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python3")

REQUIREMENTS = os.path.join(DIR, "requirements.txt")


def setup_venv():
    """Create venv and install dependencies if they don't exist."""
    if not os.path.exists(VENV_PYTHON):
        print("🔧 First run — setting up virtual environment...")
        venv.create(VENV_DIR, with_pip=True)
        print("📦 Installing dependencies (this takes ~30 seconds)...")
        subprocess.check_call(
            [VENV_PYTHON, "-m", "pip", "install", "-r", REQUIREMENTS, "-q"],
        )
        print("✅ Setup complete!\n")


if __name__ == "__main__":
    setup_venv()

    if sys.executable != VENV_PYTHON:
        os.execv(VENV_PYTHON, [VENV_PYTHON, __file__])

    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
