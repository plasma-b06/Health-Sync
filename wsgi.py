# Option 1: If you moved app.py to api/ directory
from api.app import app

# Option 2: If you kept app.py in root directory
# from app import app

if __name__ == "__main__":
    app.run()