def get_weather():
    return {
        "city": "California",
        "temperature": "6.84°C",
        "condition": "overcast clouds"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
