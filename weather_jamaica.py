# -*- coding: utf-8 -*-
def get_weather():
    return {
        "city": "Jamaica",
        "temperature": "9.56 degrees C",
        "condition": "clear sky"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
