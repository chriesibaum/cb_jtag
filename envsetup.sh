#!/bin/bash

if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Let's create it first."
    python -m venv .venv

    source .venv/bin/activate

    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Virtual environment setup complete and ready to use."
fi


