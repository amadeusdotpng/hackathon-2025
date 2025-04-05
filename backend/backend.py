from flask import Flask, request
import json
import numpy
import requests

app = Flask(__name__, static_folder = "frontend")

weather_detail_names = ["feelslike_c", "precip_mm", "cloud", "is_day"]
mood_names = ["sad", "mad", "happy", "excited"]

maxes = {
    weather_detail_names[0]: 50,
    weather_detail_names[1]: 110,
    weather_detail_names[2]: 100,
    weather_detail_names[3]: 1,
}

ideals = {
    mood_names[0]: {
        weather_detail_names[0]: 20,
        weather_detail_names[1]: 20,
        weather_detail_names[2]: 80,
        weather_detail_names[3]: 0.1,
    },
    mood_names[1]: {
        weather_detail_names[0]: 35,
        weather_detail_names[1]: 0,
        weather_detail_names[2]: 20,
        weather_detail_names[3]: 0.8,
    },
    mood_names[2]: {
        weather_detail_names[0]: 23,
        weather_detail_names[1]: 0,
        weather_detail_names[2]: 20,
        weather_detail_names[3]: 0.9,
    },
    mood_names[3]: {
        weather_detail_names[0]: 23,
        weather_detail_names[1]: 0,
        weather_detail_names[2]: 20,
        weather_detail_names[3]: 0.9,
    },
}

weights = {
    mood_names[0]: numpy.array([0, 0, 0, 0]),
    mood_names[1]: numpy.array([0, 0, 0, 0]),
    mood_names[2]: numpy.array([0, 0, 0, 0]),
    mood_names[3]: numpy.array([0, 0, 0, 0]),
}

@app.route("/")
def index():
    # location = request.args.get("location")

    weather_request = requests.get("https://api.weatherapi.com/v1/forecast.json?key=38011b547af74eda9bc61431250504&q=auto:ip")
    weather = json.loads(weather_request.text)["current"]

    music = weather_to_music(weather)

    return "Hello, World!"

def weather_to_music(weather):
    mood_values = []

    for mood_name in mood_names:
        weight = weights[mood_name]
        variable = []

        for weather_detail_name in weather_detail_names:
            weather_detail = weather[weather_detail_name]
            max_weather_detail = maxes[weather_detail_name]
            ideal_weather_detail = ideals[mood_name][weather_detail_name]

            numerater = weather_detail - ideal_weather_detail
            denominator = max_weather_detail - ideal_weather_detail

            print(f"Numerater: {numerater} | Denominator: {denominator}")


            # Switch to a binomial distribution for value
            value = -pow(numerater / denominator, 2) + 1

            variable.append(value)

        print(variable)

        mood_values.append(numpy.multiply(weight, numpy.array(variable)))

    return None


if __name__ == "__main__":
    app.json.sort_keys = False
    app.run(host = "0.0.0.0", port = 80, debug = True)
