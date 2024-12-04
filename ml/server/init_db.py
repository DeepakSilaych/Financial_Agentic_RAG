import os
import sys

# Add the server directory to Python path
server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.append(server_dir)

from server.database import engine
from server.models import Base

def init_db():
    Base.metadata.drop_all(bind=engine)  # Drop existing tables
    Base.metadata.create_all(bind=engine)  # Create new tables

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")