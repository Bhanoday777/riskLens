# -*- coding: utf-8 -*-
def get_weather():
    return {
        "city": "Sydney",
        "temperature": "27.32 degrees C",
        "condition": "overcast clouds"
    }

if __name__ == "__main__":
    w = get_weather()
    print(f"Weather in {w['city']}: {w['temperature']}, {w['condition']}")
