# -*- coding: utf-8 -*-
def get_weather():
    return {
        "city": "Delhi",
        "temperature": "22.05 degrees C",
        "condition": "haze"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
