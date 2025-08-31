# CatchTracker

A simple local web app to track your progress towards a full living Pokédex while streaming.

## Quick Start
1. **Install Python 3** (https://www.python.org/downloads/)
2. **Download or clone this repository**
3. **Run the app**
   - Windows: double-click `start.py` or run `python start.py`
   - macOS/Linux: `python3 start.py`

The script creates a virtual environment, installs required packages, and launches the tracker.

Once running:
- Open **http://localhost:5000/control** to manage your caught Pokémon.
- Add **http://localhost:5000/stream** as a browser source in OBS to show the current target.

Progress is saved in `data/state.json`.
