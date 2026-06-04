def get_weather():
    return {
        "city": "Hyderabad",
        "temperature": "27.23°C",
        "condition": "haze"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
