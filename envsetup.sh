#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 Thomas@chriesibaum.dev

VENV_DIR="/tmp/cb_jtag/.venv"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required but not installed. Install it from https://docs.astral.sh/uv/ and re-run this script."
    exit 1
fi


if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found. Let's create it first."
    uv venv "$VENV_DIR"

    source "$VENV_DIR/bin/activate"

    echo "Installing project from pyproject.toml..."
    uv pip install -e .

    # ask the user if they want to install dev dependencies
    read -p "Do you want to install development dependencies? (y/n) " -n 1 -r
    echo
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
        echo "Installing development dependencies..."
        uv pip install -e ".[dev]"
    fi

    echo "Virtual environment setup complete and ready to use."
fi
