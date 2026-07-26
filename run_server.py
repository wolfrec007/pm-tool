"""Run server with proper error logging."""
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting server on http://localhost:8000")
    print("Logs will be written to server.log")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
