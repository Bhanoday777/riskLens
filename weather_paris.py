def get_weather():
    return {
        "city": "Paris",
        "temperature": "12.5°C",
        "condition": "broken clouds"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
