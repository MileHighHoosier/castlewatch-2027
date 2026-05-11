
def analyze_wait_trend(current_wait, historical_average):
    if current_wait > historical_average * 1.25:
        return "SURGING"
    elif current_wait < historical_average * 0.75:
        return "LOWER THAN NORMAL"
    else:
        return "NORMAL"

if __name__ == "__main__":
    result = analyze_wait_trend(70, 45)
    print(result)
