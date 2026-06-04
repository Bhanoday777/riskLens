# -*- coding: utf-8 -*-
def get_weather():
    return {
        "city": "San Andreas",
        "temperature": "7.86 degrees C",
        "condition": "mist"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
