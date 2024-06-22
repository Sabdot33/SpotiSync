#!/bin/bash

cd ..
python3 -m venv venv
./venv/bin/activate
pip install -r requirements.txt
python3 app.py
echo "Setup script finished! Press Enter to continue..."
read -p ""