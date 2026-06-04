
def get_weather():
    return {
        "city": "Chennai",
        "temperature": "26.68°C",
        "condition": "scattered clouds"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
