
def get_weather():
    # Simulated weather data
    return {
        "city": "London",
        "temperature": "15�C",
        "condition": "Cloudy"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
