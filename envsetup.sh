#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 Thomas@chriesibaum.dev

VENV_DIR="/tmp/.venv_cb_jtag"


if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..."
    source $VENV_DIR/bin/activate
else
    echo "Virtual environment not found. Let's create it first."
    python -m venv $VENV_DIR

    source $VENV_DIR/bin/activate

    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Virtual environment setup complete and ready to use."
fi

