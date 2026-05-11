
def simple_forecast(wait_history):
    if not wait_history:
        return None

    avg = sum(wait_history) / len(wait_history)

    return {
        "projected_next_wait": round(avg * 1.1, 1),
        "confidence": "EARLY MODEL"
    }

if __name__ == "__main__":
    print(simple_forecast([30, 45, 50, 60]))
