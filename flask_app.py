from flask import Flask, render_template
import json
import numpy
import random
import requests
from scipy.stats import beta

app = Flask(__name__, static_folder = "frontend")

data = "../hackathon-2025-data/"

weather_detail_names = ["feelslike_c", "precip_mm", "cloud", "is_day"]
mood_names = ["sad", "mad", "happy", "excited"]

ranges = {
    weather_detail_names[0]: (-25, 50),
    weather_detail_names[1]: (0, 45),
    weather_detail_names[2]: (0, 100),
    weather_detail_names[3]: (0, 1),
}

ideals = {
    mood_names[0]: {
        weather_detail_names[0]: 20,
        weather_detail_names[1]: 8,
        weather_detail_names[2]: 80,
        weather_detail_names[3]: 0.4,
    },
    mood_names[1]: {
        weather_detail_names[0]: 35,
        weather_detail_names[1]: 1,
        weather_detail_names[2]: 20,
        weather_detail_names[3]: 0.8,
    },
    mood_names[2]: {
        weather_detail_names[0]: 23,
        weather_detail_names[1]: 1,
        weather_detail_names[2]: 20,
        weather_detail_names[3]: 0.9,
    },
    mood_names[3]: {
        weather_detail_names[0]: 23,
        weather_detail_names[1]: 1,
        weather_detail_names[2]: 20,
        weather_detail_names[3]: 0.9,
    },
}

weights = {
    mood_names[0]: numpy.array([0.15, 0.35, 0.3, 0.2]),
    mood_names[1]: numpy.array([0.3, 0.3, 0.2, 0.2]),
    mood_names[2]: numpy.array([0.25, 0.25, 0.25, 0.25]),
    mood_names[3]: numpy.array([0.2, 0.3, 0.3, 0.2]),
}

tracks = {
    mood_names[0]: [("American+Football", "Never+Meant"), ("Joji", "Glimpse+of+Us")],
    mood_names[1]: [("Poppy", "I+Disagree"), ("Ado", "Usseewa")],
    mood_names[2]: [("Pharrell+Williams", "Hug+Me"), ("Breakbot", "Baby+I'm+Yours")],
    mood_names[3]: [("Aaron+Smith", "Dancin+-+Krono+Remix"), ("The+Rah+Band", "Messages+from+the+Stars")],
}

@app.route("/")
def index():
    # location = request.args.get("location")

    weather_key_file = open(data + "weather-key.txt")
    weather_key = weather_key_file.read()

    weather_request = requests.get(f"https://api.weatherapi.com/v1/forecast.json?key={weather_key}&q=auto:ip")
    weather = json.loads(weather_request.text)["current"]

    music_key_file = open(data + "music-key.txt")
    music_key = music_key_file.read()

    music = weather_to_music(weather, music_key)

    return render_template("index.html", current_data=weather, tracks=music["similartracks"]['track'],)

def weather_to_music(weather, music_key):
    mood_values = []

    for mood_name in mood_names:
        weight = weights[mood_name]
        variable = []

        for weather_detail_name in weather_detail_names:
            weather_detail = weather[weather_detail_name]
            (min_weather_detail, max_weather_detail) = ranges[weather_detail_name]
            ideal_weather_detail = ideals[mood_name][weather_detail_name]

            if min_weather_detail > weather_detail or max_weather_detail < weather_detail:
                variable.append(0)
                continue

            weather_detail_range = max_weather_detail - min_weather_detail

            noise_range = 0.25
            noise_shift = 0.075

            if weather_detail - min_weather_detail < noise_range * weather_detail_range:
                noise = random.uniform(noise_shift, noise_range)
                weather_detail += noise * weather_detail_range
            elif max_weather_detail - weather_detail < noise_range * weather_detail_range:
                noise = random.uniform(noise_shift, noise_range)
                weather_detail -= noise * weather_detail_range

            ideal_target = ideal_weather_detail - min_weather_detail
            target = weather_detail - min_weather_detail

            c = 10
            a = (ideal_target / weather_detail_range) * (c - 2) + 1
            b = c - a

            value = beta.pdf(target / weather_detail_range, a, b)
            variable.append(value)

        mood_values.append(numpy.sum(numpy.multiply(weight, numpy.array(variable))))

    mood_values = numpy.array(mood_values)
    mood_value_probabilities = mood_values / numpy.sum(mood_values)

    mood_value_probabilities = [(mood_names[i], mood_value_probabilities[i]) for i in range(len(mood_value_probabilities))]
    mood_value_probabilities.sort(key = lambda e : e[1])
    mood_value_probabilities.reverse()

    sum_probabilities = 0
    chosen_mood_values = []
    chosen_mood_value_probabilities = []

    for mood_name, mood_value_probability in mood_value_probabilities:
        if sum_probabilities < .5:
            sum_probabilities += mood_value_probability
            chosen_mood_values.append(mood_name)
            chosen_mood_value_probabilities.append(mood_value_probability)
        else:
            break

    chosen_mood_value_probabilities = numpy.array(chosen_mood_value_probabilities) / sum_probabilities
    chosen_mood_value_index = random.choices(range(len(chosen_mood_values)), weights = chosen_mood_value_probabilities.tolist(), k = 1)[0]

    (track_artist, track_name) = random.choice(tracks[chosen_mood_values[chosen_mood_value_index]])
    # (track_artist, track_name) = tracks['mad'][0]

    music_request = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist={track_artist}&track={track_name}&api_key={music_key}&format=json&limit=18")
    music = json.loads(music_request.text)

    return music

if __name__ == "__main__":
    app.json.sort_keys = False
    app.run(host = "0.0.0.0", port = 80, debug = True)
