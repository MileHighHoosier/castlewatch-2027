
import time
from datetime import datetime
import random

def get_wait_times():
    rides = [
        "Space Mountain",
        "Seven Dwarfs Mine Train",
        "Test Track",
        "Flight of Passage"
    ]

    return [
        {
            "ride": ride,
            "wait": random.randint(5, 120),
            "timestamp": str(datetime.now())
        }
        for ride in rides
    ]

def run():
    print("WaitDragon online")

    while True:
        hour = datetime.now().hour

        if 8 <= hour <= 22:
            interval = 300
        else:
            interval = 900

        data = get_wait_times()

        for item in data:
            print(f"{item['ride']} -> {item['wait']} min")

        time.sleep(interval)

if __name__ == "__main__":
    run()
