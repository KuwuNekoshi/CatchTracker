import json
import os
import threading
import webbrowser
from flask import Flask, redirect, render_template, request, url_for
import requests

app = Flask(__name__)

DATA_FILE = os.path.join("data", "games.json")
STATE_FILE = os.path.join("data", "state.json")

with open(DATA_FILE) as f:
    GAMES = json.load(f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    # default state
    generation = next(iter(GAMES.keys()))
    game = next(iter(GAMES[generation].keys()))
    return {"generation": generation, "game": game, "index": 0, "caught": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


@app.route("/select", methods=["GET", "POST"])
def select():
    state = load_state()
    if request.method == "POST":
        state["generation"] = request.form["generation"]
        state["game"] = request.form["game"]
        state["index"] = 0
        save_state(state)
        return redirect(url_for("tracker"))
    generations = list(GAMES.keys())
    games_for_gen = GAMES[state["generation"]].keys()
    return render_template("select.html", generations=generations, games=games_for_gen, state=state)


def current_pokemon(state):
    game_list = GAMES[state["generation"]][state["game"]]
    if state["index"] < 0:
        state["index"] = 0
    if state["index"] >= len(game_list):
        state["index"] = len(game_list) - 1
    return game_list[state["index"]]


@app.route("/tracker", methods=["GET", "POST"])
def tracker():
    state = load_state()
    game_list = GAMES[state["generation"]][state["game"]]
    if request.method == "POST":
        action = request.form["action"]
        if action == "next" and state["index"] < len(game_list) - 1:
            state["index"] += 1
        elif action == "prev" and state["index"] > 0:
            state["index"] -= 1
        elif action == "toggle":
            poke = current_pokemon(state)["name"]
            state["caught"][poke] = not state["caught"].get(poke, False)
        save_state(state)
    poke = current_pokemon(state)
    caught = state["caught"].get(poke["name"], False)
    return render_template("tracker.html", state=state, pokemon=poke, caught=caught)


@app.route("/display")
def display():
    state = load_state()
    poke = current_pokemon(state)
    name = poke["name"].lower()
    # fetch id from pokeapi
    try:
        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=5)
        if resp.ok:
            poke_id = resp.json()["id"]
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{poke_id}.png"
        else:
            img_url = ""
    except Exception:
        img_url = ""
    return render_template("display.html", pokemon=poke, img_url=img_url)


if __name__ == "__main__":
    def open_browser():
        try:
            webbrowser.open_new("http://127.0.0.1:5000/tracker")
            webbrowser.open_new("http://127.0.0.1:5000/display")
        except Exception:
            pass

    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)
