import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("pokemon")

POKEAPI_BASE = "https://pokeapi.co/api/v2"


@mcp.tool()
async def get_pokemon_stats(name: str) -> str:
    """
    Look up a Pokémon's base stats by name.
    Example: get_pokemon_stats("pikachu")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{name.lower()}")

        if response.status_code == 404:
            return f"Pokémon '{name}' not found. Check the spelling and try again!"

        data = response.json()

        # Extract stats
        stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        types = [t["type"]["name"] for t in data["types"]]

        return (
            f"🎮 {data['name'].capitalize()} (#{data['id']})\n"
            f"Type: {', '.join(types)}\n"
            f"Height: {data['height'] / 10}m | Weight: {data['weight'] / 10}kg\n\n"
            f"Base Stats:\n"
            f"  HP:              {stats.get('hp')}\n"
            f"  Attack:          {stats.get('attack')}\n"
            f"  Defense:         {stats.get('defense')}\n"
            f"  Sp. Attack:      {stats.get('special-attack')}\n"
            f"  Sp. Defense:     {stats.get('special-defense')}\n"
            f"  Speed:           {stats.get('speed')}\n"
        )

@mcp.tool()
async def compare_pokemon(name1: str, name2: str) -> str:
    """
    Compare the base stats of two Pokémon side by side.
    Example: compare_pokemon("pikachu", "raichu")
    """
    async with httpx.AsyncClient() as client:
        r1, r2 = await asyncio.gather(
            client.get(f"{POKEAPI_BASE}/pokemon/{name1.lower()}"),
            client.get(f"{POKEAPI_BASE}/pokemon/{name2.lower()}")
        )

        if r1.status_code == 404:
            return f"Pokémon '{name1}' not found. Check the spelling!"
        if r2.status_code == 404:
            return f"Pokémon '{name2}' not found. Check the spelling!"

        d1, d2 = r1.json(), r2.json()

        def get_stats(data):
            return {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

        s1, s2 = get_stats(d1), get_stats(d2)
        n1, n2 = d1["name"].capitalize(), d2["name"].capitalize()

        stat_keys = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]
        labels =    ["HP", "Attack", "Defense", "Sp. Attack", "Sp. Defense", "Speed"]

        lines = [f"⚔️  {n1} vs {n2}\n"]
        score1, score2 = 0, 0

        for key, label in zip(stat_keys, labels):
            v1, v2 = s1.get(key, 0), s2.get(key, 0)
            winner = "👈" if v1 > v2 else ("👉" if v2 > v1 else "🤝")
            if v1 > v2: score1 += 1
            elif v2 > v1: score2 += 1
            lines.append(f"  {label:<14} {v1:>4}  vs  {v2:<4} {winner}")

        lines.append(f"\n🏆 Winner: {n1 if score1 > score2 else (n2 if score2 > score1 else 'Tie!')}")
        lines.append(f"   ({score1} vs {score2} stats won)")

        return "\n".join(lines)

@mcp.tool()
async def get_pokemon_abilities(name: str) -> str:
    """
    List all abilities a Pokémon can have, including hidden abilities.
    Example: get_pokemon_abilities("gengar")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{name.lower()}")
        if response.status_code == 404:
            return f"Pokémon '{name}' not found."
        data = response.json()
        lines = [f"Abilities for {data['name'].capitalize()}:"]
        for a in data["abilities"]:
            label = " (hidden)" if a["is_hidden"] else f" (slot {a['slot']})"
            lines.append(f"  - {a['ability']['name']}{label}")
        return "\n".join(lines)


@mcp.tool()
async def get_move_details(move: str) -> str:
    """
    Look up details about a Pokémon move: type, power, accuracy, PP, and effect.
    Example: get_move_details("thunderbolt")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/move/{move.lower().replace(' ', '-')}")
        if response.status_code == 404:
            return f"Move '{move}' not found."
        d = response.json()
        effect_entries = d.get("effect_entries", [])
        effect = next((e["short_effect"] for e in effect_entries if e["language"]["name"] == "en"), "No description.")
        effect = effect.replace("$effect_chance", str(d.get("effect_chance") or "?"))
        return (
            f"Move: {d['name'].replace('-', ' ').title()}\n"
            f"Type: {d['type']['name']} | Class: {d['damage_class']['name']}\n"
            f"Power: {d['power'] or '—'} | Accuracy: {d['accuracy'] or '—'} | PP: {d['pp']}\n"
            f"Effect: {effect}"
        )


@mcp.tool()
async def get_pokemon_moves(name: str) -> str:
    """
    List all moves a Pokémon can learn.
    Example: get_pokemon_moves("charmander")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{name.lower()}")
        if response.status_code == 404:
            return f"Pokémon '{name}' not found."
        data = response.json()
        moves = sorted(m["move"]["name"].replace("-", " ").title() for m in data["moves"])
        return f"{data['name'].capitalize()} can learn {len(moves)} moves:\n" + ", ".join(moves)


@mcp.tool()
async def get_type_matchups(type_name: str) -> str:
    """
    Show damage relations for a Pokémon type (strengths, weaknesses, immunities).
    Example: get_type_matchups("fire")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/type/{type_name.lower()}")
        if response.status_code == 404:
            return f"Type '{type_name}' not found."
        dr = response.json()["damage_relations"]

        def fmt(key):
            types = [t["name"] for t in dr.get(key, [])]
            return ", ".join(types) if types else "none"

        return (
            f"Type: {type_name.capitalize()}\n"
            f"  Strong against (2x):    {fmt('double_damage_to')}\n"
            f"  Weak against (2x):      {fmt('double_damage_from')}\n"
            f"  Not very effective:     {fmt('half_damage_to')}\n"
            f"  Resists:                {fmt('half_damage_from')}\n"
            f"  No effect on:           {fmt('no_damage_to')}\n"
            f"  Immune to:              {fmt('no_damage_from')}"
        )


@mcp.tool()
async def get_ability_details(ability: str) -> str:
    """
    Look up the description and effect of a Pokémon ability.
    Example: get_ability_details("intimidate")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/ability/{ability.lower().replace(' ', '-')}")
        if response.status_code == 404:
            return f"Ability '{ability}' not found."
        d = response.json()
        effect_entries = d.get("effect_entries", [])
        effect = next((e["effect"] for e in effect_entries if e["language"]["name"] == "en"), "No description.")
        short = next((e["short_effect"] for e in effect_entries if e["language"]["name"] == "en"), "")
        pokemon = [p["pokemon"]["name"].capitalize() for p in d.get("pokemon", [])][:10]
        return (
            f"Ability: {d['name'].replace('-', ' ').title()}\n"
            f"Summary: {short}\n"
            f"Effect: {effect}\n"
            f"Notable Pokémon: {', '.join(pokemon) or 'none'}"
        )


@mcp.tool()
async def get_evolution_chain(pokemon_name: str) -> str:
    """
    Show the full evolution chain for a given Pokémon.
    Example: get_evolution_chain("eevee")
    """
    async with httpx.AsyncClient() as client:
        species_resp = await client.get(f"{POKEAPI_BASE}/pokemon-species/{pokemon_name.lower()}")
        if species_resp.status_code == 404:
            return f"Pokémon '{pokemon_name}' not found."
        chain_url = species_resp.json()["evolution_chain"]["url"]
        chain_resp = await client.get(chain_url)
        chain_data = chain_resp.json()["chain"]

    def parse_chain(node, depth=0):
        name = node["species"]["name"].capitalize()
        details = node.get("evolution_details", [])
        trigger = ""
        if details:
            d = details[0]
            parts = []
            if d.get("min_level"):
                parts.append(f"level {d['min_level']}")
            if d.get("item"):
                parts.append(f"use {d['item']['name']}")
            if d.get("held_item"):
                parts.append(f"hold {d['held_item']['name']}")
            if d.get("trigger"):
                parts.append(d["trigger"]["name"].replace("-", " "))
            trigger = f" ({', '.join(parts)})" if parts else ""
        prefix = "  " * depth + ("→ " if depth else "")
        lines = [f"{prefix}{name}{trigger}"]
        for evo in node.get("evolves_to", []):
            lines.extend(parse_chain(evo, depth + 1))
        return lines

    return "Evolution Chain:\n" + "\n".join(parse_chain(chain_data))


@mcp.tool()
async def get_item_details(item: str) -> str:
    """
    Look up details about an in-game item.
    Example: get_item_details("master-ball")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/item/{item.lower().replace(' ', '-')}")
        if response.status_code == 404:
            return f"Item '{item}' not found."
        d = response.json()
        effect_entries = d.get("effect_entries", [])
        effect = next((e["short_effect"] for e in effect_entries if e["language"]["name"] == "en"), "No description.")
        category = d.get("category", {}).get("name", "unknown")
        cost = d.get("cost", 0)
        return (
            f"Item: {d['name'].replace('-', ' ').title()}\n"
            f"Category: {category} | Cost: {cost} Pokédollars\n"
            f"Effect: {effect}"
        )


@mcp.tool()
async def get_pokemon_encounters(name: str) -> str:
    """
    Show where a Pokémon can be encountered in the wild.
    Example: get_pokemon_encounters("snorlax")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{name.lower()}/encounters")
        if response.status_code == 404:
            return f"Pokémon '{name}' not found."
        data = response.json()
        if not data:
            return f"{name.capitalize()} has no wild encounter locations (may be event-only or evolve-only)."
        lines = [f"Wild encounter locations for {name.capitalize()}:"]
        for loc in data[:15]:
            area = loc["location_area"]["name"].replace("-", " ").title()
            versions = list({v["version"]["name"] for detail in loc["version_details"] for v in [detail]})
            lines.append(f"  - {area} ({', '.join(versions)})")
        if len(data) > 15:
            lines.append(f"  ... and {len(data) - 15} more locations.")
        return "\n".join(lines)


@mcp.tool()
async def get_nature_details(nature: str) -> str:
    """
    Look up a nature's stat boosts and reductions.
    Example: get_nature_details("adamant")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/nature/{nature.lower()}")
        if response.status_code == 404:
            return f"Nature '{nature}' not found."
        d = response.json()
        increased = d.get("increased_stat", {})
        decreased = d.get("decreased_stat", {})
        inc_name = increased.get("name", "none").replace("-", " ") if increased else "none (neutral)"
        dec_name = decreased.get("name", "none").replace("-", " ") if decreased else "none (neutral)"
        likes = d.get("likes_flavor", {})
        hates = d.get("hates_flavor", {})
        return (
            f"Nature: {d['name'].capitalize()}\n"
            f"  +10% boost: {inc_name}\n"
            f"  -10% cut:   {dec_name}\n"
            f"  Likes flavor: {likes.get('name', 'none') if likes else 'none'}\n"
            f"  Hates flavor: {hates.get('name', 'none') if hates else 'none'}"
        )


@mcp.tool()
async def get_generation_pokemon(generation: int) -> str:
    """
    List all Pokémon species introduced in a given generation (1–9).
    Example: get_generation_pokemon(1)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{POKEAPI_BASE}/generation/{generation}")
        if response.status_code == 404:
            return f"Generation {generation} not found. Valid range is 1–9."
        d = response.json()
        species = sorted(s["name"].capitalize() for s in d["pokemon_species"])
        region = d.get("main_region", {}).get("name", "unknown").capitalize()
        return (
            f"Generation {generation} ({region}) — {len(species)} Pokémon:\n"
            + ", ".join(species)
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")