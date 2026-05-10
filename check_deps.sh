#!/bin/bash
echo "Checking dependencies..."
pip3 list 2>/dev/null | grep -i -E "requests|dotenv" || {
    echo "Installing requirements..."
    pip3 install -r requirements.txt
}
python3 -c "import requests; import dotenv; print('All dependencies OK')"
