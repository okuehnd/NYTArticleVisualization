# Activate the virtual environment
source venv/bin/activate

# Run the Python scripts in order
python step1_clean.py
python step2_sentiment.py
python step3_createHTML.py

# Deactivate the virtual environment
deactivate