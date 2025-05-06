#!/bin/bash

BACK=$(pwd)
mkdir -p ~/Apps
cd ~/Apps

if [[ ! -d "playwright-venv" ]]; then
  echo "No virtual enviroment found. ==> Creating new virtual enviroment..."
  cd ~/Apps
  python3.13 -m venv ~/Apps/playwright-venv
  source ~/Apps/playwright-venv/bin/activate
  python3.13 -m pip install playwright
  python3.13 -m pip install urllib3
  python3.13 -m pip install rich
  python3.13 -m pip install --upgrade rich
  python3.13 -m pip install --upgrade pip
  playwright install
  deactivate
  cd -
else
  source  ~/Apps/playwright-venv/bin/activate
  cd $BACK
  echo "How to run a script: "
  echo "Run with: ~/Apps/playwright-venv/bin/python3.13 search_amazon.py 'Some Search Term' --max 25" 
  deactivate
fi
