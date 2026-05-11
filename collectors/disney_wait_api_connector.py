
import requests
from datetime import datetime

def fetch_wait_data():
    # Placeholder endpoint structure
    # Replace with live source feed later
    sample = {
        "park": "Magic Kingdom",
        "ride": "Space Mountain",
        "wait": 45,
        "timestamp": str(datetime.now())
    }

    return sample

if __name__ == "__main__":
    print(fetch_wait_data())
