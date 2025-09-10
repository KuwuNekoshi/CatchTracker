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

# Explicitly use UTF-8 so special characters like the Nidoran symbols
# load correctly regardless of platform defaults.
with open(DATA_FILE, encoding="utf-8") as f:
    GAMES = json.load(f)
KNOWN_GAMES = {g for games in GAMES.values() for combo in games.keys() for g in combo.split("/")}

POKE_CACHE_FILE = os.path.join("data", "pokemon_cache.json")
if os.path.exists(POKE_CACHE_FILE):
    with open(POKE_CACHE_FILE, encoding="utf-8") as f:
        POKE_CACHE = json.load(f)
else:
    POKE_CACHE = {}


def _api_name(name):
    n = name.lower()
    n = n.replace("♀", "-f").replace("♂", "-m")
    n = n.replace(".", "").replace("'", "")
    n = n.replace(" ", "-")
    return n


# PokeAPI uses "nidoran-f" and "nidoran-m" which are sometimes tricky to
# resolve when network access fails. Provide explicit IDs so their sprites are
# always correct.
SPECIAL_IDS = {
    "nidoran-f": 29,
    "nidoran-m": 32,
}


def get_poke_info(name):
    key = _api_name(name)
    if key in POKE_CACHE:
        return POKE_CACHE[key]
    try:
        if key in SPECIAL_IDS:
            poke_id = SPECIAL_IDS[key]
        else:
            resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{key}", timeout=5)
            if resp.ok:
                poke_id = resp.json()["id"]
            else:
                poke_id = 9999
        img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{poke_id}.png" if poke_id != 9999 else ""
    except Exception:
        poke_id = 9999
        img_url = ""
    POKE_CACHE[key] = {"id": poke_id, "img_url": img_url}
    with open(POKE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(POKE_CACHE, f)
    return POKE_CACHE[key]


def parse_location(loc_str):
    match = re.match(r"^(.*?)(?:\s*\(([^)]+)\))?$", loc_str)
    base = match.group(1).strip()
    variant_str = match.group(2)
    if variant_str:
        variants = [v.strip() for v in variant_str.split("/")]
        if all(v in KNOWN_GAMES for v in variants):
            return base, variants
    return loc_str.strip(), []


def game_entries_for_state(state):
    games = GAMES[state["generation"]]
    for combo, entries in games.items():
        if state["game"] in combo.split("/"):
            return entries
    return []


def full_dex_list(filter_gen=None):
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
        if filter_gen and filter_gen not in p["generations"]:
            continue
        dex.append(p)
    return sorted(dex, key=lambda x: x["id"])

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
        if "title_size" not in state:
            state["title_size"] = 32
        return state
    generation = next(iter(GAMES.keys()))
    first_combo = next(iter(GAMES[generation].keys()))
    game = first_combo.split("/")[0]
    return {"generation": generation, "game": game, "index": 0, "caught": {}, "title_size": 32}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
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
        games_for_gen = []
        for combo in GAMES[state["generation"]].keys():
            games_for_gen.extend(combo.split("/"))
        game = request.form["game"]
        if game not in games_for_gen:
            game = games_for_gen[0]
        state["game"] = game
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
    if not game_list:
        return {"id": 0, "name": "Unknown", "location": "", "img_url": ""}
    if state["index"] < 0:
        state["index"] = 0
    if state["index"] >= len(game_list):
        state["index"] = len(game_list) - 1
    return game_list[state["index"]]


@app.route("/tracker", methods=["GET", "POST"])
def tracker():
    state = load_state()
    game_list = ordered_game_list(state)
    dex_list = full_dex_list(state["generation"])
    sort = request.args.get("sort", "dex")
    if request.method == "POST":
        sort = request.form.get("sort", "dex")
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
        return redirect(url_for("tracker", sort=sort))
    catch_order_map = {p["id"]: i for i, p in enumerate(game_list)}
    if sort == "catch":
        dex_list.sort(key=lambda p: catch_order_map.get(p["id"], 999999))
    caught_map = state["caught"]
    uncaught_list = [p for p in dex_list if not caught_map.get(str(p["id"]), False)]
    caught_list = [p for p in dex_list if caught_map.get(str(p["id"]), False)]
    poke = current_pokemon(state, game_list)
    caught = caught_map.get(str(poke["id"]), False)
    return render_template(
        "tracker.html",
        state=state,
        pokemon=poke,
        caught=caught,
        uncaught_list=uncaught_list,
        caught_list=caught_list,
        sort=sort,
    )


@app.route("/set_current", methods=["POST"])
def set_current():
    data = request.get_json()
    poke_id = int(data.get("id", -1))
    state = load_state()
    game_list = ordered_game_list(state)
    for i, p in enumerate(game_list):
        if p["id"] == poke_id:
            state["index"] = i
            save_state(state)
            break
    return "", 204


@app.route("/set_title_size", methods=["POST"])
def set_title_size():
    data = request.get_json()
    size = int(data.get("size", 32))
    state = load_state()
    state["title_size"] = size
    save_state(state)
    return "", 204


@app.route("/display")
def display():
    state = load_state()
    game_list = ordered_game_list(state)
    poke = current_pokemon(state, game_list)
    img_url = poke.get("img_url", "")
    dex_list = full_dex_list(state["generation"])
    total_count = len(dex_list)
    caught_count = sum(1 for p in dex_list if state["caught"].get(str(p["id"]), False))
    title_size = state.get("title_size", 32)
    return render_template(
        "display.html",
        pokemon=poke,
        img_url=img_url,
        index=state["index"],
        title_size=title_size,
        caught_count=caught_count,
        total_count=total_count,
    )


@app.route("/current_index")
def current_index():
    state = load_state()
    dex_list = full_dex_list(state["generation"])
    total_count = len(dex_list)
    caught_count = sum(1 for p in dex_list if state["caught"].get(str(p["id"]), False))
    return {
        "index": state["index"],
        "title_size": state.get("title_size", 32),
        "caught_count": caught_count,
        "total_count": total_count,
    }


@app.route("/games/<generation>")
def games_for_generation(generation):
    games_for_gen = []
    if generation in GAMES:
        for combo in GAMES[generation].keys():
            games_for_gen.extend(combo.split("/"))
    return {"games": games_for_gen}


if __name__ == "__main__":
    def open_browser():
        try:
            webbrowser.open_new("http://127.0.0.1:5000/tracker")
            webbrowser.open_new("http://127.0.0.1:5000/display")
        except Exception:
            pass

    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)
