@echo off

REM Activate the virtual environment
call venv\Scripts\activate

REM Run the Python scripts in order
python step1_clean.py
python step2_sentiment.py
python step3_createHTML.py

REM Deactivate the virtual environment
call venv\Scripts\deactivate