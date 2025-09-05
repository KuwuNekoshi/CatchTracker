import json
from pathlib import Path

EVOLVES_FROM = {
    "Grovyle": "Treecko",
    "Sceptile": "Grovyle",
    "Combusken": "Torchic",
    "Blaziken": "Combusken",
    "Marshtomp": "Mudkip",
    "Swampert": "Marshtomp",
    "Mightyena": "Poochyena",
    "Linoone": "Zigzagoon",
    "Silcoon": "Wurmple",
    "Beautifly": "Silcoon",
    "Cascoon": "Wurmple",
    "Dustox": "Cascoon",
    "Lombre": "Lotad",
    "Ludicolo": "Lombre",
    "Nuzleaf": "Seedot",
    "Shiftry": "Nuzleaf",
    "Swellow": "Taillow",
    "Pelipper": "Wingull",
    "Kirlia": "Ralts",
    "Gardevoir": "Kirlia",
    "Masquerain": "Surskit",
    "Breloom": "Shroomish",
    "Vigoroth": "Slakoth",
    "Slaking": "Vigoroth",
    "Ninjask": "Nincada",
    "Shedinja": "Nincada",
    "Loudred": "Whismur",
    "Exploud": "Loudred",
    "Hariyama": "Makuhita",
    "Delcatty": "Skitty",
    "Lairon": "Aron",
    "Aggron": "Lairon",
    "Medicham": "Meditite",
    "Manectric": "Electrike",
    "Swalot": "Gulpin",
    "Sharpedo": "Carvanha",
    "Wailord": "Wailmer",
    "Camerupt": "Numel",
    "Grumpig": "Spoink",
    "Vibrava": "Trapinch",
    "Flygon": "Vibrava",
    "Cacturne": "Cacnea",
    "Altaria": "Swablu",
    "Whiscash": "Barboach",
    "Crawdaunt": "Corphish",
    "Claydol": "Baltoy",
    "Cradily": "Lileep",
    "Armaldo": "Anorith",
    "Milotic": "Feebas",
    "Banette": "Shuppet",
    "Dusclops": "Duskull",
    "Glalie": "Snorunt",
    "Sealeo": "Spheal",
    "Walrein": "Sealeo",
    "Huntail": "Clamperl",
    "Gorebyss": "Clamperl",
    "Shelgon": "Bagon",
    "Salamence": "Shelgon",
    "Metang": "Beldum",
    "Metagross": "Metang",
}

BASE_LOCATIONS = {
    "Treecko": "Starter",
    "Torchic": "Starter",
    "Mudkip": "Starter",
    "Poochyena": "Route 101",
    "Zigzagoon": "Route 101",
    "Wurmple": "Routes 101-102",
    "Lotad": "Route 102 (Sapphire)",
    "Seedot": "Route 102 (Ruby)",
    "Taillow": "Route 104",
    "Wingull": "Route 103",
    "Ralts": "Route 102",
    "Surskit": "Route 102 (swarm)",
    "Shroomish": "Petalburg Woods",
    "Slakoth": "Petalburg Woods",
    "Nincada": "Route 116",
    "Whismur": "Rusturf Tunnel",
    "Makuhita": "Granite Cave",
    "Azurill": "Breed Marill",
    "Nosepass": "Granite Cave",
    "Skitty": "Route 116",
    "Sableye": "Granite Cave (Sapphire)",
    "Mawile": "Granite Cave (Ruby)",
    "Aron": "Granite Cave",
    "Meditite": "Mt. Pyre slopes",
    "Electrike": "Route 110",
    "Plusle": "Route 110 (Ruby)",
    "Minun": "Route 110 (Sapphire)",
    "Volbeat": "Route 117 (Ruby)",
    "Illumise": "Route 117 (Sapphire)",
    "Roselia": "Route 117",
    "Gulpin": "Route 110",
    "Carvanha": "Route 118 water",
    "Wailmer": "Route 110 water",
    "Numel": "Fiery Path",
    "Torkoal": "Fiery Path",
    "Spoink": "Jagged Pass",
    "Spinda": "Route 113",
    "Trapinch": "Route 111 desert",
    "Cacnea": "Route 111 desert",
    "Swablu": "Route 114",
    "Zangoose": "Route 114 (Ruby)",
    "Seviper": "Route 114 (Sapphire)",
    "Lunatone": "Meteor Falls (Sapphire)",
    "Solrock": "Meteor Falls (Ruby)",
    "Barboach": "Route 111 (fishing)",
    "Corphish": "Route 102 (fishing)",
    "Baltoy": "Route 111 desert",
    "Lileep": "Root Fossil",
    "Anorith": "Claw Fossil",
    "Feebas": "Route 119 water",
    "Castform": "Weather Institute gift",
    "Kecleon": "Route 119",
    "Shuppet": "Mt. Pyre exterior",
    "Duskull": "Mt. Pyre interior",
    "Tropius": "Route 119",
    "Chimecho": "Mt. Pyre summit",
    "Absol": "Route 120",
    "Wynaut": "Lavaridge Town egg",
    "Snorunt": "Shoal Cave",
    "Spheal": "Shoal Cave",
    "Clamperl": "Route 124 (fishing)",
    "Relicanth": "Underwater routes",
    "Luvdisc": "Route 128 (fishing)",
    "Bagon": "Meteor Falls basement",
    "Beldum": "Steven's house gift",
    "Regirock": "Desert Ruins",
    "Regice": "Island Cave",
    "Registeel": "Ancient Tomb",
    "Latias": "Southern Island event",
    "Latios": "Southern Island event",
    "Kyogre": "Marine Cave (Sapphire)",
    "Groudon": "Terra Cave (Ruby)",
    "Rayquaza": "Sky Pillar",
    "Jirachi": "Event",
    "Deoxys": "Birth Island event",
}

FRLG_SPECIAL = {
    "Jirachi": "Event",
    "Deoxys": "Birth Island event",
}


def main() -> None:
    path = Path(__file__).resolve().parent.parent / "data" / "games.json"
    data = json.loads(path.read_text())
    gen3 = data.get("Generation III", {})

    for game in ["Ruby/Sapphire", "Emerald"]:
        for entry in gen3.get(game, []):
            name = entry["name"]
            if name in EVOLVES_FROM:
                entry["location"] = f"Evolve {EVOLVES_FROM[name]}"
            else:
                entry["location"] = BASE_LOCATIONS.get(name, entry["location"])

    # Only keep Generation III Pokémon that have an in-game source in
    # FireRed/LeafGreen. Most Hoenn species are unobtainable without
    # trading, so we drop those entries entirely instead of marking them
    # as trade-only placeholders.
    gen3["FireRed/LeafGreen"] = [
        {"name": name, "location": FRLG_SPECIAL[name]}
        for name in FRLG_SPECIAL
    ]

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
