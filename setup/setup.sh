#!/bin/bash

cd ..
python3 -m venv venv
sudo chmod +rwx ./venv/bin/activate
./venv/bin/activate
pip install -r requirements.txt
python3 gui.py
echo "Setup script finished! Press Enter to continue..."
read -p ""