
from datetime import datetime
import random

def run():
    conditions = ["Sunny", "Cloudy", "Rain", "Storm"]

    weather = {
        "condition": random.choice(conditions),
        "temperature": random.randint(65, 96),
        "timestamp": str(datetime.now())
    }

    print(weather)

if __name__ == "__main__":
    run()
