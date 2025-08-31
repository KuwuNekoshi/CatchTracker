import json
import os
import re
import threading
import webbrowser
from flask import Flask, redirect, render_template, request, url_for
import requests

app = Flask(__name__)

DATA_FILE = os.path.join("data", "games.json")
STATE_FILE = os.path.join("data", "state.json")

with open(DATA_FILE) as f:
    GAMES = json.load(f)

POKE_CACHE_FILE = os.path.join("data", "pokemon_cache.json")
if os.path.exists(POKE_CACHE_FILE):
    with open(POKE_CACHE_FILE) as f:
        POKE_CACHE = json.load(f)
else:
    POKE_CACHE = {}


def _api_name(name):
    n = name.lower()
    n = n.replace("♀", "-f").replace("♂", "-m")
    n = n.replace(".", "").replace("'", "")
    n = n.replace(" ", "-")
    return n


def get_poke_info(name):
    key = _api_name(name)
    if key in POKE_CACHE:
        return POKE_CACHE[key]
    try:
        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{key}", timeout=5)
        if resp.ok:
            poke_id = resp.json()["id"]
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{poke_id}.png"
        else:
            poke_id = 9999
            img_url = ""
    except Exception:
        poke_id = 9999
        img_url = ""
    POKE_CACHE[key] = {"id": poke_id, "img_url": img_url}
    with open(POKE_CACHE_FILE, "w") as f:
        json.dump(POKE_CACHE, f)
    return POKE_CACHE[key]


def parse_location(loc_str):
    match = re.match(r"^(.*?)(?:\s*\(([^)]+)\))?$", loc_str)
    base = match.group(1).strip()
    variants = [v.strip() for v in match.group(2).split("/")] if match.group(2) else []
    return base, variants


def game_entries_for_state(state):
    games = GAMES[state["generation"]]
    for combo, entries in games.items():
        if state["game"] in combo.split("/"):
            return entries
    return []


def full_dex_list():
    all_poke = {}
    for gen, games in GAMES.items():
        for combo, entries in games.items():
            base_games = combo.split("/")
            for entry in entries:
                loc, variants = parse_location(entry["location"])
                games_for_entry = variants if variants else base_games
                info = get_poke_info(entry["name"])
                pid = info["id"]
                p = all_poke.setdefault(
                    pid,
                    {
                        "id": pid,
                        "name": entry["name"],
                        "img_url": info["img_url"],
                        "generations": set(),
                        "games": set(),
                        "locations": {},
                    },
                )
                p["generations"].add(gen)
                for g in games_for_entry:
                    p["games"].add(g)
                    p["locations"][g] = loc
    dex = []
    for p in all_poke.values():
        p["generations"] = sorted(p["generations"])
        p["games"] = sorted(p["games"])
        dex.append(p)
    return sorted(dex, key=lambda x: x["id"])

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    generation = next(iter(GAMES.keys()))
    first_combo = next(iter(GAMES[generation].keys()))
    game = first_combo.split("/")[0]
    return {"generation": generation, "game": game, "index": 0, "caught": {}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def ordered_game_list(state):
    entries = game_entries_for_state(state)
    game_list = []
    for entry in entries:
        loc, variants = parse_location(entry["location"])
        if variants and state["game"] not in variants:
            continue
        info = get_poke_info(entry["name"])
        game_list.append(
            {
                "name": entry["name"],
                "location": loc,
                "id": info["id"],
                "img_url": info["img_url"],
            }
        )

    def sort_key(entry):
        loc = entry["location"].lower()
        if "starter" in loc:
            return (-1, entry["name"])
        match = re.search(r"route\s*(\d+)", loc)
        if match:
            return (int(match.group(1)), entry["name"])
        return (9999, entry["name"])

    return sorted(game_list, key=sort_key)


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
    games_for_gen = []
    for combo in GAMES[state["generation"]].keys():
        games_for_gen.extend(combo.split("/"))
    return render_template("select.html", generations=generations, games=games_for_gen, state=state)


def current_pokemon(state, game_list=None):
    if game_list is None:
        game_list = ordered_game_list(state)
    if state["index"] < 0:
        state["index"] = 0
    if state["index"] >= len(game_list):
        state["index"] = len(game_list) - 1
    return game_list[state["index"]]


@app.route("/tracker", methods=["GET", "POST"])
def tracker():
    state = load_state()
    game_list = ordered_game_list(state)
    dex_list = full_dex_list()
    if request.method == "POST":
        action = request.form["action"]
        if action == "next" and state["index"] < len(game_list) - 1:
            state["index"] += 1
        elif action == "prev" and state["index"] > 0:
            state["index"] -= 1
        elif action == "toggle":
            poke = current_pokemon(state)["id"]
            key = str(poke)
            state["caught"][key] = not state["caught"].get(key, False)
        save_state(state)
    poke = current_pokemon(state, game_list)
    caught = state["caught"].get(str(poke["id"]), False)
    return render_template(
        "tracker.html",
        state=state,
        pokemon=poke,
        caught=caught,
        dex_list=dex_list,
        caught_map=state["caught"],
    )


@app.route("/display")
def display():
    state = load_state()
    game_list = ordered_game_list(state)
    poke = current_pokemon(state, game_list)
    img_url = poke.get("img_url", "")
    return render_template("display.html", pokemon=poke, img_url=img_url, index=state["index"])


@app.route("/current_index")
def current_index():
    state = load_state()
    return {"index": state["index"]}


if __name__ == "__main__":
    def open_browser():
        try:
            webbrowser.open_new("http://127.0.0.1:5000/tracker")
            webbrowser.open_new("http://127.0.0.1:5000/display")
        except Exception:
            pass

    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)
