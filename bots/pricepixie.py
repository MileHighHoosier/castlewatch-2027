
from datetime import datetime
import random

def run():
    resorts = [
        "Disney's Pop Century Resort",
        "Disney's Beach Club Resort",
        "Disney's Animal Kingdom Lodge"
    ]

    for resort in resorts:
        print({
            "resort": resort,
            "nightly_rate": random.randint(150, 700),
            "timestamp": str(datetime.now())
        })

if __name__ == "__main__":
    run()
