"""National Pokédex: Streamlit edition.

Every Pokémon and form (Megas, Gigantamax, regional variants) from Red/Blue to Legends: Z-A.
Data comes live from PokéAPI (https://pokeapi.co), which needs no API key. Responses are cached
server-side, so all visitors share one cache, as PokéAPI's fair-use policy asks.

Run locally:  streamlit run app.py
"""
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from html import escape

import requests
import streamlit as st

API = "https://pokeapi.co/api/v2/"
SPR = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
DAY, WEEK = 60 * 60 * 24, 60 * 60 * 24 * 7
PAGE = 60

st.set_page_config(page_title="National Pokédex", page_icon=":material/menu_book:", layout="wide")

# ---------------------------------------------------------------- data access
_http = requests.Session()
_http.headers["User-Agent"] = "national-pokedex-streamlit"


def fetch(path):
    """GET a PokéAPI resource. Returns None on 404, raises on other failures."""
    url = path if path.startswith("http") else API + path
    r = _http.get(url, timeout=20)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


get = st.cache_data(ttl=WEEK, show_spinner=False, max_entries=20000)(fetch)
# ponytail: process-wide LRU for move lookups made from worker threads (st.cache_data wants a script context).
fetch_threaded = lru_cache(maxsize=4096)(fetch)


def safe(path):
    try:
        return get(path)
    except requests.RequestException:
        return None


# ---------------------------------------------------------------- reference data
# type: (color, super-effective against, not very effective against, no effect on)
TYPES = {
    "normal": ("#9FA19F", [], ["rock", "steel"], ["ghost"]),
    "fire": ("#E62829", ["grass", "ice", "bug", "steel"], ["fire", "water", "rock", "dragon"], []),
    "water": ("#2980EF", ["fire", "ground", "rock"], ["water", "grass", "dragon"], []),
    "electric": ("#FAC000", ["water", "flying"], ["electric", "grass", "dragon"], ["ground"]),
    "grass": ("#3FA129", ["water", "ground", "rock"], ["fire", "grass", "poison", "flying", "bug", "dragon", "steel"], []),
    "ice": ("#3DCEF3", ["grass", "ground", "flying", "dragon"], ["fire", "water", "ice", "steel"], []),
    "fighting": ("#FF8000", ["normal", "ice", "rock", "dark", "steel"], ["poison", "flying", "psychic", "bug", "fairy"], ["ghost"]),
    "poison": ("#9141CB", ["grass", "fairy"], ["poison", "ground", "rock", "ghost"], ["steel"]),
    "ground": ("#915121", ["fire", "electric", "poison", "rock", "steel"], ["grass", "bug"], ["flying"]),
    "flying": ("#81B9EF", ["grass", "fighting", "bug"], ["electric", "rock", "steel"], []),
    "psychic": ("#EF4179", ["fighting", "poison"], ["psychic", "steel"], ["dark"]),
    "bug": ("#91A119", ["grass", "psychic", "dark"], ["fire", "fighting", "poison", "flying", "ghost", "steel", "fairy"], []),
    "rock": ("#AFA981", ["fire", "ice", "flying", "bug"], ["fighting", "ground", "steel"], []),
    "ghost": ("#704170", ["psychic", "ghost"], ["dark"], ["normal"]),
    "dragon": ("#5060E1", ["dragon"], ["steel"], ["fairy"]),
    "dark": ("#624D4E", ["psychic", "ghost"], ["fighting", "dark", "fairy"], []),
    "steel": ("#60A1B8", ["ice", "rock", "fairy"], ["fire", "water", "electric", "steel"], []),
    "fairy": ("#EF70EF", ["fighting", "dragon", "dark"], ["fire", "poison", "steel"], []),
}
GENS = [(1, 151, "Kanto"), (152, 251, "Johto"), (252, 386, "Hoenn"), (387, 493, "Sinnoh"), (494, 649, "Unova"),
        (650, 721, "Kalos"), (722, 809, "Alola"), (810, 905, "Galar"), (906, 1025, "Paldea")]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
# Version groups in release order. Groups PokéAPI adds later still show up, title-cased, at the end.
VGS = [
    ("red-blue", 1, ["red", "blue"]), ("yellow", 1, ["yellow"]), ("gold-silver", 2, ["gold", "silver"]), ("crystal", 2, ["crystal"]),
    ("ruby-sapphire", 3, ["ruby", "sapphire"]), ("emerald", 3, ["emerald"]), ("firered-leafgreen", 3, ["firered", "leafgreen"]),
    ("colosseum", 3, ["colosseum"]), ("xd", 3, ["xd"]),
    ("diamond-pearl", 4, ["diamond", "pearl"]), ("platinum", 4, ["platinum"]), ("heartgold-soulsilver", 4, ["heartgold", "soulsilver"]),
    ("black-white", 5, ["black", "white"]), ("black-2-white-2", 5, ["black-2", "white-2"]),
    ("x-y", 6, ["x", "y"]), ("omega-ruby-alpha-sapphire", 6, ["omega-ruby", "alpha-sapphire"]),
    ("sun-moon", 7, ["sun", "moon"]), ("ultra-sun-ultra-moon", 7, ["ultra-sun", "ultra-moon"]),
    ("lets-go-pikachu-lets-go-eevee", 7, ["lets-go-pikachu", "lets-go-eevee"]),
    ("sword-shield", 8, ["sword", "shield"]), ("the-isle-of-armor", 8, ["the-isle-of-armor"]), ("the-crown-tundra", 8, ["the-crown-tundra"]),
    ("brilliant-diamond-shining-pearl", 8, ["brilliant-diamond", "shining-pearl"]),
    ("brilliant-diamond-and-shining-pearl", 8, ["brilliant-diamond", "shining-pearl"]), ("legends-arceus", 8, ["legends-arceus"]),
    ("scarlet-violet", 9, ["scarlet", "violet"]), ("the-teal-mask", 9, ["the-teal-mask"]), ("the-indigo-disk", 9, ["the-indigo-disk"]),
    ("legends-za", 9, ["legends-za"]), ("mega-dimension", 9, ["mega-dimension"]),
]
VG = {n: {"gen": g, "versions": v, "order": i} for i, (n, g, v) in enumerate(VGS)}
VERSION_ORDER = list(dict.fromkeys(v for _, _, vs in VGS for v in vs))
VERSION_GEN = {v: g for _, g, vs in VGS for v in vs}
VNAME = {"firered": "FireRed", "leafgreen": "LeafGreen", "heartgold": "HeartGold", "soulsilver": "SoulSilver",
         "lets-go-pikachu": "Let’s Go, Pikachu!", "lets-go-eevee": "Let’s Go, Eevee!", "legends-arceus": "Legends: Arceus",
         "legends-za": "Legends: Z-A", "mega-dimension": "Mega Dimension (DLC)", "the-isle-of-armor": "The Isle of Armor",
         "the-crown-tundra": "The Crown Tundra", "the-teal-mask": "The Teal Mask", "the-indigo-disk": "The Indigo Disk",
         "xd": "XD: Gale of Darkness"}
STAT = {"hp": "HP", "attack": "Attack", "defense": "Defense", "special-attack": "Sp. Atk", "special-defense": "Sp. Def", "speed": "Speed"}
REG = {"alola": "Alolan", "galar": "Galarian", "hisui": "Hisuian", "paldea": "Paldean"}
SPECIAL = {"mr-mime": "Mr. Mime", "mime-jr": "Mime Jr.", "mr-rime": "Mr. Rime", "nidoran-f": "Nidoran♀", "nidoran-m": "Nidoran♂",
           "farfetchd": "Farfetch’d", "sirfetchd": "Sirfetch’d", "ho-oh": "Ho-Oh", "porygon-z": "Porygon-Z", "type-null": "Type: Null",
           "jangmo-o": "Jangmo-o", "hakamo-o": "Hakamo-o", "kommo-o": "Kommo-o", "flabebe": "Flabébé",
           "wo-chien": "Wo-Chien", "chien-pao": "Chien-Pao", "ting-lu": "Ting-Lu", "chi-yu": "Chi-Yu"}
CATS = {"all": "All", "base": "Base species", "mega": "Mega & Primal", "gmax": "Gigantamax", "regional": "Regional", "other": "Other forms"}
BADGE = {"mega": "Mega", "gmax": "G-Max", "other": "Form"}
METHOD_LABEL = {"level-up": "Level up", "machine": "TM / TR / HM", "egg": "Egg move", "tutor": "Move tutor"}


# ---------------------------------------------------------------- helpers
def tc(s):
    return " ".join(w[:1].upper() + w[1:] for w in str(s or "").split("-"))


def pad(n):
    return f"{n:04d}"


def id_from_url(u):
    return int(u.rstrip("/").split("/")[-1])


def en(arr, key="name"):
    return next((x.get(key) for x in arr or [] if x.get("language", {}).get("name") == "en"), None)


def gen_of(n):
    return next((i + 1 for i, (a, b, _) in enumerate(GENS) if a <= n <= b), len(GENS))


def version_name(v):
    return VNAME.get(v) or tc(v)


def vg_name(vg):
    return " / ".join(version_name(v) for v in VG[vg]["versions"]) if vg in VG else tc(vg)


def v_order(v):
    return VERSION_ORDER.index(v) if v in VERSION_ORDER else 999


def art(id_):
    return f"{SPR}other/official-artwork/{id_}.png"


def text_on(hex_):
    n = int(hex_[1:], 16)
    r, g, b = n >> 16, (n >> 8) & 255, n & 255
    return "#111" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "#fff"


def type_chip(t, extra="", small=False):
    c = TYPES.get(t, ("#888888",))[0]
    return f'<span class="type{" sm" if small else ""}" style="background:{c};color:{text_on(c)}">{escape(t)}{extra}</span>'


def category(name, id_):
    if id_ <= 10000:
        return "base"
    if re.search(r"-totem|-cap$|-cap-", name):
        return "other"
    if re.search(r"-(mega|primal)(-|$)", name):
        return "mega"
    if name.endswith("-gmax"):
        return "gmax"
    if re.search(r"-(alola|galar|hisui|paldea)(-|$)", name):
        return "regional"
    return "other"


def pretty(name, base=None):
    base = base or name
    b = SPECIAL.get(base) or tc(base)
    if name == base:
        return b
    parts, pre = [x for x in name[len(base) + 1:].split("-") if x], []
    if parts and parts[0] in ("mega", "primal", "gmax"):
        pre.append({"mega": "Mega", "primal": "Primal", "gmax": "Gigantamax"}[parts.pop(0)])
    elif parts and parts[0] in REG:
        pre.append(REG[parts.pop(0)])
    if parts and parts[-1] == "gmax":
        pre.insert(0, "Gigantamax")
        parts.pop()
    return " ".join([*pre, b, *(p[:1].upper() + p[1:] for p in parts)])


def defenses(types):
    out = {}
    for atk, (_, se, nve, no) in TYPES.items():
        m = 1.0
        for d in types:
            m = m * 2 if d in se else m * 0.5 if d in nve else 0 if d in no else m
        out[atk] = m
    return out


def mult(m):
    return {0.25: "¼", 0.5: "½"}.get(m, f"{m:g}")


@st.cache_data(ttl=DAY, show_spinner="Loading the National Pokédex…")
def load_index():
    """All Pokémon + forms, each mapped back to its base species' National Dex number."""
    results = fetch("pokemon?limit=100000")["results"]
    allp = [{"name": r["name"], "id": id_from_url(r["url"])} for r in results]
    keys = {p["name"]: p["id"] for p in allp if p["id"] <= 10000}
    for p in allp:  # also index "deoxys" for "deoxys-normal" so "deoxys-attack" resolves
        if p["id"] <= 10000:
            seg = p["name"].split("-")
            for i in range(len(seg) - 1, 0, -1):
                keys.setdefault("-".join(seg[:i]), p["id"])
    for p in allp:
        base = p["name"]
        if p["id"] > 10000:
            seg = p["name"].split("-")
            base = next(("-".join(seg[:i]) for i in range(len(seg) - 1, 0, -1) if "-".join(seg[:i]) in keys), p["name"])
        p["dex"] = p["id"] if p["id"] <= 10000 else keys.get(base, 0)
        p["cat"] = category(p["name"], p["id"])
        p["label"] = pretty(p["name"], base)
        p["gen"] = gen_of(p["dex"]) if p["dex"] else 0
    allp.sort(key=lambda p: (p["dex"], p["id"]))
    return allp


@st.cache_data(ttl=WEEK, show_spinner=False)
def type_members(t):
    return {x["pokemon"]["name"] for x in get(f"type/{t}")["pokemon"]}


# ---------------------------------------------------------------- styles
st.html("""<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600;700&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');
:root{--surface:#141922;--surface-2:#1B212D;--ink:#E7EAF1;--muted:#9BA3B6;--line:#283042;--accent:#FF5A42;--lens:#4F98FF;
 --good:#4CC57E;--warn:#F0B040;--bad:#FF5A42;--fd:"Chakra Petch",system-ui,sans-serif;--fb:"Instrument Sans",system-ui,sans-serif;--fm:"JetBrains Mono",ui-monospace,monospace}
.block-container{padding-top:4.5rem;max-width:1240px}
.lens{flex:none;width:40px;height:40px;border-radius:50%;border:2.5px solid var(--ink);background:radial-gradient(circle at 38% 36%,#BFDCFF 0 18%,var(--lens) 20% 58%,var(--surface) 60%)}
.dx{font-family:var(--fb);color:var(--ink)}
.dx a{color:inherit;text-decoration:none}
.brand{display:flex;align-items:center;gap:12px;border-bottom:3px solid var(--accent);padding-bottom:12px;margin-bottom:4px}
.brand b{font:700 1.4rem/1 var(--fd);letter-spacing:.02em;text-transform:uppercase}
.brand small{display:block;font:500 .7rem/1.2 var(--fm);color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-top:4px}
.intro h1{font:700 clamp(1.8rem,4vw,2.5rem)/1.05 var(--fd);margin:8px 0 6px;padding:0}
.intro p{margin:0;color:var(--muted);max-width:62ch}
.count{font:500 .8rem var(--fm);color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.card{position:relative;display:flex;flex-direction:column;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px 10px 14px;transition:transform .18s,border-color .18s}
.card:hover{transform:translateY(-3px);border-color:var(--lens)}
.card .num{align-self:flex-start;font:500 .75rem var(--fm);color:var(--muted)}
.card img{width:104px;height:104px;object-fit:contain;margin:4px 0 8px}
.card .nm{font-weight:600;text-align:center;line-height:1.25;font-size:.95rem}
.badge{position:absolute;top:10px;right:10px;font:600 .64rem/1 var(--fm);letter-spacing:.06em;text-transform:uppercase;padding:4px 7px;border-radius:999px;background:var(--surface-2);color:var(--muted)}
.badge.mega{background:#2E2148;color:#C9A8FF}.badge.gmax{background:#3A1A16;color:#FF9A8A}.badge.regional{background:#162A47;color:#9CC8FF}
.art{position:relative;border-radius:20px;overflow:hidden;min-height:340px;display:grid;place-items:center;border:1px solid var(--line)}
.art .wm{position:absolute;left:14px;bottom:-.12em;font:700 clamp(4.5rem,10vw,8.5rem)/1 var(--fd);opacity:.22;pointer-events:none}
.art img{position:relative;width:min(84%,360px);aspect-ratio:1;object-fit:contain;filter:drop-shadow(0 18px 22px rgba(0,0,0,.4))}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:4px}
.dexno{font:500 .8rem var(--fm);color:var(--muted);letter-spacing:.06em;text-transform:uppercase;margin:0}
.pname{font:700 clamp(2.1rem,5vw,3.3rem)/1 var(--fd);margin:6px 0 4px}
.genus{color:var(--muted);font-weight:500;margin:0 0 12px}
.types,.chips,.row{display:flex;gap:6px;flex-wrap:wrap}
.type{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;font:600 .78rem/1.2 var(--fb);letter-spacing:.06em;text-transform:uppercase}
.type.sm{padding:3px 9px;font-size:.68rem}.type i{font:600 .7rem var(--fm);font-style:normal}
.flavor{margin:14px 0 0;font-size:1.02rem;max-width:62ch}
.flavor cite{display:block;margin-top:4px;font:500 .74rem var(--fm);color:var(--muted);font-style:normal}
.facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px 18px;margin:16px 0 0}
.facts dt,.kv dt{font:500 .68rem var(--fm);text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.facts dd,.kv dd{margin:2px 0 0;font-weight:600;font-variant-numeric:tabular-nums}
.facts dd small,.kv dd small{font-weight:400;color:var(--muted)}
.kv{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px 20px;margin:0}
.flag{font:600 .7rem var(--fm);text-transform:uppercase;letter-spacing:.06em;padding:4px 8px;border-radius:6px;border:1px solid var(--line);margin-top:12px;display:inline-block}
.h2{font:700 1.2rem/1.2 var(--fd);margin:0 0 14px;letter-spacing:.02em;text-transform:uppercase}
.h2 small{font:500 .74rem var(--fm);color:var(--muted);text-transform:none;letter-spacing:0;margin-left:8px}
.h3{font:600 .76rem var(--fm);text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:16px 0 8px}
.muted{color:var(--muted)}
.forms{display:flex;gap:10px;overflow-x:auto;padding-bottom:4px}
.form{flex:none;display:flex;align-items:center;gap:8px;padding:6px 14px 6px 6px;border:1px solid var(--line);border-radius:999px;font-weight:600;font-size:.9rem;min-height:48px}
.form img{width:40px;height:40px;object-fit:contain}.form.on{border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}
.stats{display:grid;grid-template-columns:auto 3.2ch minmax(0,1fr);gap:8px 12px;align-items:center;font-variant-numeric:tabular-nums}
.stats .k{font:500 .8rem var(--fm);color:var(--muted)}.stats .v{font-weight:600;text-align:right}
.track{height:10px;border-radius:999px;background:var(--surface-2);overflow:hidden}.fill{height:100%;border-radius:999px}
.total{grid-column:1/-1;display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:10px;font-weight:600}
.total span{font:500 .8rem var(--fm);color:var(--muted)}
.abil div{margin-bottom:8px}.abil em{font:600 .64rem var(--fm);text-transform:uppercase;letter-spacing:.06em;color:var(--accent);margin-left:6px;font-style:normal}
.abil p{margin:2px 0 0;color:var(--muted);font-size:.86rem}
.evo{display:flex;align-items:center;gap:8px;overflow-x:auto;padding:4px 2px 8px}
.evo-col{display:flex;flex-direction:column;gap:10px}.evo-branch{display:flex;align-items:center;gap:8px}
.evo-node{display:flex;flex-direction:column;align-items:center;gap:2px;padding:8px 10px;border-radius:14px;border:1px solid transparent;min-width:118px;flex:none}
.evo-node:hover,.evo-node.on{border-color:var(--line);background:var(--surface-2)}
.evo-node img{width:84px;height:84px;object-fit:contain}.evo-node b{font-size:.92rem;text-align:center}.evo-node span{font:500 .7rem var(--fm);color:var(--muted)}
.evo-arrow{display:flex;flex-direction:column;align-items:center;gap:2px;color:var(--muted);font:500 .72rem/1.3 var(--fm);text-align:center;max-width:130px;min-width:70px;flex:none}
.evo-arrow .arr{color:var(--accent);font-size:1.4rem;line-height:1}
.gen-row{display:grid;grid-template-columns:7.5ch minmax(0,1fr);gap:10px;padding:8px 0;border-top:1px solid var(--line);align-items:baseline}
.gen-row:first-child{border-top:0}.gen-row b{font:600 .78rem var(--fm);color:var(--muted)}
.chip{padding:3px 10px;border-radius:999px;background:var(--surface-2);font-size:.85rem;font-weight:500}.chip.za{background:#2E2148}
.btn{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:8px 16px;border-radius:999px;border:1px solid var(--line);background:var(--surface);font-weight:600}
.btn:hover{background:var(--surface-2)}
.pager{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.foot{color:var(--muted);font-size:.85rem;border-top:1px solid var(--line);padding-top:16px;margin-top:24px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media (max-width:640px){.grid{grid-template-columns:repeat(auto-fill,minmax(130px,1fr))}.card img{width:88px;height:88px}.art{min-height:260px}}
@media (prefers-reduced-motion:reduce){.card{transition:none}}
</style>""")


def html(s):
    st.html(f'<div class="dx">{s}</div>')


def link(name):
    return f"?p={name}"


ARROW = '<b class="arr" aria-hidden="true">→</b>'  # st.html strips inline SVG


# ---------------------------------------------------------------- browse view
def browse(idx):
    html('<div class="intro"><h1>Every Pokémon, every form</h1><p>All species from Red and Blue through Legends: Z-A, '
         'plus Mega Evolutions, Gigantamax and regional variants. Search above or pick one below.</p></div>')
    counts = {"all": len(idx)}
    for p in idx:
        counts[p["cat"]] = counts.get(p["cat"], 0) + 1
    cat = st.segmented_control("Form type", list(CATS), default="all", key="cat",
                               format_func=lambda k: f"{CATS[k]} · {counts.get(k, 0):,}") or "all"
    c2, c3, _ = st.columns([1, 1, 2])
    gen = c2.selectbox("Generation", list(range(10)), key="gen",
                       format_func=lambda g: "All generations" if g == 0 else f"Gen {ROMAN[g - 1]} · {GENS[g - 1][2]}")
    typ = c3.selectbox("Type", ["", *TYPES], key="type", format_func=lambda t: t.capitalize() if t else "All types")

    members = None
    if typ:
        try:
            members = type_members(typ)
        except requests.RequestException:
            st.warning("Couldn’t load that type from PokéAPI. Try again in a moment.")
    rows = [p for p in idx if (cat == "all" or p["cat"] == cat) and (not gen or p["gen"] == gen)
            and (members is None or p["name"] in members)]

    filters = (cat, gen, typ)
    if st.session_state.get("filters") != filters:  # new filters → back to the first page
        st.session_state.filters, st.session_state.limit = filters, PAGE
    limit = st.session_state.limit

    html(f'<p class="count">Showing {min(limit, len(rows)):,} of {len(rows):,} matches · {len(idx):,} Pokémon and forms in total</p>')
    if not rows:
        st.info("No Pokémon match these filters. Try another type or generation.")
        return
    cards = []
    for p in rows[:limit]:
        reg = next((v for k, v in REG.items() if f"-{k}" in p["name"]), "Regional")
        badge = "" if p["cat"] == "base" else f'<span class="badge {p["cat"]}">{reg if p["cat"] == "regional" else BADGE[p["cat"]]}</span>'
        num = f"#{pad(p['dex'])}" if p["dex"] else "&nbsp;"
        cards.append(f'<a class="card" href="{link(p["name"])}" target="_self">{badge}<span class="num">{num}</span>'
                     f'<img src="{art(p["id"])}" alt="" loading="lazy" width="104" height="104"><span class="nm">{escape(p["label"])}</span></a>')
    html(f'<div class="grid">{"".join(cards)}</div>')
    if limit < len(rows):
        st.button(f"Show {min(PAGE, len(rows) - limit)} more", on_click=lambda: st.session_state.update(limit=limit + PAGE),
                  width="stretch")


# ---------------------------------------------------------------- detail view
def evo_text(details):
    texts = []
    for d in details or []:
        t, out = (d.get("trigger") or {}).get("name"), []

        def nm(k):
            return tc((d.get(k) or {}).get("name"))
        if d.get("min_level"):
            out.append(f"Lv. {d['min_level']}")
        elif t == "level-up":
            out.append("Level up")
        if t == "trade":
            out.append("Trade")
        if d.get("item"):
            out.append(("Use " if t == "use-item" else "") + nm("item"))
        for key, fmt in (("held_item", "holding {}"), ("trade_species", "for {}"), ("known_move", "knowing {}"),
                         ("known_move_type", "knowing a {} move"), ("location", "at {}"), ("party_species", "with {} in party"),
                         ("party_type", "with a {} type in party"), ("region", "in {}")):
            if d.get(key):
                out.append(fmt.format(nm(key)))
        if d.get("min_happiness"):
            out.append("high friendship")
        if d.get("min_affection"):
            out.append("high affection")
        if d.get("min_beauty"):
            out.append("high beauty")
        if d.get("time_of_day"):
            out.append("full moon" if d["time_of_day"] == "full-moon" else d["time_of_day"])
        out += {1: ["female"], 2: ["male"]}.get(d.get("gender"), [])
        if d.get("needs_overworld_rain"):
            out.append("while raining")
        if d.get("turn_upside_down"):
            out.append("console upside down")
        out += {1: ["Atk > Def"], 0: ["Atk = Def"], -1: ["Atk < Def"]}.get(d.get("relative_physical_stats"), [])
        if d.get("used_move"):
            out.append(f"after using {nm('used_move')}" + (f" ×{d['min_move_count']}" if d.get("min_move_count") else ""))
        if d.get("min_steps"):
            out.append(f"after {d['min_steps']:,} steps")
        if d.get("min_damage_taken"):
            out.append(f"after taking {d['min_damage_taken']} damage")
        if not out and t:
            out.append(tc(t))
        s = ", ".join(out)
        if s and s not in texts:
            texts.append(s)
    return " · or ".join(texts[:2])


def evo_html(root, current, by_dex):
    def node(l):
        id_ = id_from_url(l["species"]["url"])
        e = by_dex.get(id_)
        on = " on" if l["species"]["name"] == current else ""
        label = e["label"] if e else pretty(l["species"]["name"])
        return (f'<a class="evo-node{on}" href="{link(e["name"] if e else l["species"]["name"])}" target="_self">'
                f'<img src="{art(id_)}" alt="" loading="lazy"><b>{escape(label)}</b><span>#{pad(id_)}</span></a>')

    def walk(l):
        if not l["evolves_to"]:
            return node(l)
        kids = "".join(f'<div class="evo-branch"><div class="evo-arrow">{ARROW}<span>{escape(evo_text(c["evolution_details"]))}</span></div>{walk(c)}</div>'
                       for c in l["evolves_to"])
        return f'{node(l)}<div class="evo-col">{kids}</div>'

    if not root["evolves_to"]:
        return f'<div class="evo">{node(root)}</div><p class="muted">This Pokémon does not evolve.</p>'
    return f'<div class="evo">{walk(root)}</div>'


def stat_color(v):
    return "var(--bad)" if v < 50 else "var(--warn)" if v < 80 else "var(--good)" if v < 110 else "var(--lens)"


def _move(url):
    try:
        return fetch_threaded(url)
    except requests.RequestException:
        return None


def detail(name, idx):
    by_name = {p["name"]: p for p in idx}
    by_dex = {p["id"]: p for p in idx if p["id"] <= 10000}
    try:
        p = get(f"pokemon/{name}")
        if p is None:  # maybe a species name, e.g. "deoxys" → its default form
            s = get(f"pokemon-species/{name}")
            if s is None:
                st.warning(f"No Pokémon called “{name}” was found. Check the spelling, or search above.")
                st.link_button("Browse all Pokémon", "?")
                return
            p = get(next(v for v in s["varieties"] if v["is_default"])["pokemon"]["url"])
        s = get(p["species"]["url"])
    except requests.RequestException:
        st.error("Couldn’t reach PokéAPI. Check your connection and try again.")
        st.button("Try again")
        return

    types = [t["type"]["name"] for t in sorted(p["types"], key=lambda t: t["slot"])]
    dex, gen = s["id"], gen_of(s["id"])
    sp_name = en(s.get("names")) or pretty(s["name"])
    genus = en(s.get("genera"), "genus") or ""
    form = safe(p["forms"][0]["url"]) if p.get("forms") else None
    title = (form and en(form.get("names"))) or sp_name
    form_name = form and en(form.get("form_names"))
    sub = " · ".join(x for x in (genus, form_name) if x)
    ft = [f for f in s.get("flavor_text_entries", []) if f["language"]["name"] == "en"]
    ft = ft[-1] if ft else None
    sprites = p.get("sprites") or {}
    other = sprites.get("other") or {}
    oa, home = other.get("official-artwork") or {}, other.get("home") or {}
    art_url = oa.get("front_default") or home.get("front_default") or sprites.get("front_default")
    shiny_url = oa.get("front_shiny") or home.get("front_shiny") or sprites.get("front_shiny")
    c1 = TYPES.get(types[0], ("#888888",))[0]
    c2 = TYPES.get(types[-1], ("#888888",))[0]
    cries = p.get("cries") or {}
    cry = cries.get("latest") or cries.get("legacy")

    html('<a class="btn" href="?" target="_self">← All Pokémon</a>')

    left, right = st.columns([5, 7], gap="medium")
    with left:
        shiny = bool(shiny_url) and st.toggle("Shiny", key=f"shiny-{p['name']}")
        src = shiny_url if shiny else art_url
        img = (f'<img src="{src}" alt="{"Shiny " if shiny else ""}official artwork of {escape(title)}">'
               if src else '<p class="muted">No artwork yet</p>')
        html(f'<div class="art" style="background:radial-gradient(120% 90% at 50% 40%,{c1}55 0%,{c2}22 60%,var(--surface) 100%);'
             f'border-color:{c1}66"><span class="wm" style="color:{c1}">{pad(dex)}</span>{img}</div>')
        if cry:
            st.audio(cry, format="audio/ogg")
    with right:
        female = s["gender_rate"] * 12.5
        gender = "Genderless" if s["gender_rate"] < 0 else f"{100 - female:g}% ♂ · {female:g}% ♀"
        ev = ", ".join(f"{x['effort']} {STAT.get(x['stat']['name'], tc(x['stat']['name']))}" for x in p["stats"] if x["effort"]) or "None"
        m, kg = p["height"] / 10, p["weight"] / 10
        inch = round(m * 39.3701)
        flags = [f for f, on in (("Legendary", s.get("is_legendary")), ("Mythical", s.get("is_mythical")), ("Baby", s.get("is_baby"))) if on]
        flavor = ""
        if ft:
            flavor = (f'<p class="flavor">{escape(" ".join(ft["flavor_text"].split()))}'
                      f'<cite>Pokédex entry · Pokémon {escape(version_name(ft["version"]["name"]))}</cite></p>')
        region = f"Gen {ROMAN[gen - 1]} · {GENS[gen - 1][2]}" if gen <= len(GENS) else "Gen ?"
        flag_html = "".join(f'<span class="flag">{f}</span> ' for f in flags)
        html(f'''<div class="panel">
          <p class="dexno">No. {pad(dex)} · {region}</p>
          <div class="pname">{escape(title)}</div><p class="genus">{escape(sub)}</p>
          <div class="types">{"".join(type_chip(t) for t in types)}</div>{flavor}
          <dl class="facts">
            <div><dt>Height</dt><dd>{m:.1f} m <small>{inch // 12}′{inch % 12}″</small></dd></div>
            <div><dt>Weight</dt><dd>{kg:.1f} kg <small>{kg * 2.20462:.1f} lb</small></dd></div>
            <div><dt>Gender</dt><dd>{gender}</dd></div>
            <div><dt>Catch rate</dt><dd>{s.get("capture_rate", "—")} <small>/ 255</small></dd></div>
            <div><dt>Base exp.</dt><dd>{p.get("base_experience") or "—"}</dd></div>
            <div><dt>EV yield</dt><dd>{escape(ev)}</dd></div>
          </dl>{flag_html}</div>''')

    varieties = s.get("varieties", [])
    if len(varieties) > 1:
        chips = []
        for v in varieties:
            vn = v["pokemon"]["name"]
            label = by_name[vn]["label"] if vn in by_name else pretty(vn, s["name"])
            chips.append(f'<a class="form{" on" if vn == p["name"] else ""}" href="{link(vn)}" target="_self">'
                         f'<img src="{art(id_from_url(v["pokemon"]["url"]))}" alt="" loading="lazy">{escape(label)}</a>')
        html(f'<div class="panel"><div class="h2">Forms<small>{len(varieties)} varieties</small></div><div class="forms">{"".join(chips)}</div></div>')

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        total = sum(x["base_stat"] for x in p["stats"])
        bars = "".join(
            f'<span class="k">{STAT.get(x["stat"]["name"], tc(x["stat"]["name"]))}</span><span class="v">{x["base_stat"]}</span>'
            f'<div class="track"><div class="fill" style="width:{min(100, x["base_stat"] / 255 * 100):.1f}%;background:{stat_color(x["base_stat"])}"></div></div>'
            for x in p["stats"])
        abil = []
        for a in p["abilities"]:
            d = safe(a["ability"]["url"])
            nm = (d and en(d.get("names"))) or tc(a["ability"]["name"])
            fx = d and (en(d.get("effect_entries"), "short_effect") or en(list(reversed(d.get("flavor_text_entries", []))), "flavor_text"))
            fx_html = f"<p>{escape(' '.join(fx.split()))}</p>" if fx else ""
            hidden = "<em>Hidden</em>" if a["is_hidden"] else ""
            abil.append(f"<div><b>{escape(nm)}</b>{hidden}{fx_html}</div>")
        abil_html = "".join(abil) or '<span class="muted">No abilities in this game.</span>'
        html(f'<div class="panel"><div class="h2">Base stats</div><div class="stats">{bars}<div class="total"><span>Total</span>{total}</div></div>'
             f'<div class="h3">Abilities</div><div class="abil">{abil_html}</div></div>')
    with col_b:
        dfn = defenses(types)

        def group(f):
            items = sorted(((t, x) for t, x in dfn.items() if f(x)), key=lambda kv: -kv[1])
            return "".join(type_chip(t, f" <i>×{mult(x)}</i>", True) for t, x in items) or '<span class="muted">None</span>'
        html(f'<div class="panel"><div class="h2">Type defenses<small>damage taken</small></div>'
             f'<div class="h3">Weak to</div><div class="row">{group(lambda x: x > 1)}</div>'
             f'<div class="h3">Resists</div><div class="row">{group(lambda x: 0 < x < 1)}</div>'
             f'<div class="h3">Immune to</div><div class="row">{group(lambda x: x == 0)}</div></div>')

    chain = safe(s["evolution_chain"]["url"]) if s.get("evolution_chain") else None
    evo = evo_html(chain["chain"], s["name"], by_dex) if chain else '<p class="muted">No evolution data.</p>'
    html(f'<div class="panel"><div class="h2">Evolution</div>{evo}</div>')

    # Games: union of every version PokéAPI links to this Pokémon.
    versions = {g["version"]["name"] for g in p.get("game_indices", [])}
    versions |= {f["version"]["name"] for f in s.get("flavor_text_entries", [])}
    for mv in p["moves"]:
        for d in mv["version_group_details"]:
            vgn = d["version_group"]["name"]
            versions.update(VG[vgn]["versions"] if vgn in VG else [vgn])
    by_gen = {}
    for v in versions:
        by_gen.setdefault(VERSION_GEN.get(v, 0), []).append(v)
    rows = []
    for g, vs in sorted(by_gen.items(), key=lambda kv: kv[0] or 99):
        chips = "".join(f'<span class="chip{" za" if v in ("legends-za", "mega-dimension") else ""}">{escape(version_name(v))}</span>'
                        for v in sorted(vs, key=v_order))
        rows.append(f'<div class="gen-row"><b>{"Gen " + ROMAN[g - 1] if g else "Other"}</b><div class="chips">{chips}</div></div>')
    games = "".join(rows) or '<p class="muted">No game data yet.</p>'
    nums = [d for d in s.get("pokedex_numbers", []) if d["pokedex"]["name"] != "national"]
    dexnums = ""
    if nums:
        dexnums = ('<div class="h3">Regional Pokédex numbers</div><div class="chips">'
                   + "".join(f'<span class="chip">{escape(tc(d["pokedex"]["name"]))} #{d["entry_number"]}</span>' for d in nums) + "</div>")
    html(f'<div class="panel"><div class="h2">Games<small>appearances recorded in PokéAPI</small></div>{games}{dexnums}</div>')

    html('<div class="h2" style="margin-top:8px">Where to find it<small>wild encounters by game</small></div>')
    by_v = {}
    for a in safe(p["location_area_encounters"]) or []:
        for vd in a["version_details"]:
            lv = [(d["min_level"], d["max_level"]) for d in vd["encounter_details"]] or [(0, 0)]
            lo, hi = min(x[0] for x in lv), max(x[1] for x in lv)
            by_v.setdefault(vd["version"]["name"], []).append({
                "Location": tc(re.sub(r"-area$", "", a["location_area"]["name"])),
                "Method": ", ".join(dict.fromkeys(tc(d["method"]["name"]) for d in vd["encounter_details"])),
                "Levels": str(lo) if lo == hi else f"{lo}–{hi}", "Chance": f"{vd['max_chance']}%"})
    if not by_v:
        st.caption("PokéAPI has no wild encounter records for this Pokémon. It may come from evolution, a trade, a gift, "
                   "a raid, or a game whose locations PokéAPI hasn’t mapped yet.")
    for i, v in enumerate(sorted(by_v, key=v_order)):
        n = len(by_v[v])
        with st.expander(f"Pokémon {version_name(v)} · {n} location{'s' if n > 1 else ''}", expanded=i == 0):
            st.dataframe(by_v[v], hide_index=True)

    html('<div class="h2" style="margin-top:8px">Moves</div>')
    vgs = sorted({d["version_group"]["name"] for mv in p["moves"] for d in mv["version_group_details"]},
                 key=lambda v: VG[v]["order"] if v in VG else 999)
    if not vgs:
        st.caption("PokéAPI has no move data for this form yet.")
    else:
        m1, m2 = st.columns(2)
        vg = m1.selectbox("Game", vgs, index=len(vgs) - 1, format_func=vg_name, key=f"vg-{p['name']}")
        by_method = {}
        for mv in p["moves"]:
            for d in mv["version_group_details"]:
                if d["version_group"]["name"] == vg:
                    by_method.setdefault(d["move_learn_method"]["name"], []).append((d["level_learned_at"], mv["move"]))
        methods = sorted(by_method, key=lambda k: list(METHOD_LABEL).index(k) if k in METHOD_LABEL else 99)
        method = m2.selectbox("Learned by", methods, index=methods.index("level-up") if "level-up" in methods else 0,
                              format_func=lambda k: f"{METHOD_LABEL.get(k, tc(k))} ({len(by_method[k])})", key=f"m-{p['name']}-{vg}")
        moves = sorted(by_method[method], key=lambda x: (x[0], x[1]["name"]))
        with st.spinner("Loading move details…"), ThreadPoolExecutor(8) as ex:
            info = list(ex.map(lambda x: _move(x[1]["url"]), moves))
        table = []
        for (lv, mv), d in zip(moves, info):
            d = d or {}
            table.append({"Lv.": str(lv or "Evo") if method == "level-up" else "—",
                          "Move": en(d.get("names")) or tc(mv["name"]),
                          "Type": tc((d.get("type") or {}).get("name", "")),
                          "Category": tc((d.get("damage_class") or {}).get("name", "")),
                          "Power": d.get("power"), "Accuracy": d.get("accuracy"), "PP": d.get("pp")})
        st.dataframe(table, hide_index=True, column_config={
            "Power": st.column_config.NumberColumn(format="%d"),
            "Accuracy": st.column_config.NumberColumn(format="%d%%"),
            "PP": st.column_config.NumberColumn(format="%d")})

    hatch = s.get("hatch_counter")
    steps = f"≈ {(hatch + 1) * 255:,} steps" if hatch is not None else ""
    html(f'''<div class="panel"><div class="h2">Training &amp; breeding</div><dl class="kv">
      <div><dt>Base friendship</dt><dd>{s.get("base_happiness", "—")}</dd></div>
      <div><dt>Growth rate</dt><dd>{escape(tc((s.get("growth_rate") or {}).get("name", "—")))}</dd></div>
      <div><dt>Egg groups</dt><dd>{escape(", ".join(tc(g["name"]) for g in s.get("egg_groups", [])) or "—")}</dd></div>
      <div><dt>Egg cycles</dt><dd>{hatch if hatch is not None else "—"} <small>{steps}</small></dd></div>
      <div><dt>Habitat</dt><dd>{escape(tc((s.get("habitat") or {}).get("name", "—")))}</dd></div>
      <div><dt>Color · Shape</dt><dd>{escape(tc((s.get("color") or {}).get("name", "—")))} · {escape(tc((s.get("shape") or {}).get("name", "—")))}</dd></div>
    </dl></div>''')

    prev, nxt = by_dex.get(dex - 1), by_dex.get(dex + 1)
    prev_html = f'<a class="btn" href="{link(prev["name"])}" target="_self">← #{pad(prev["dex"])} {escape(prev["label"])}</a>' if prev else "<span></span>"
    next_html = f'<a class="btn" href="{link(nxt["name"])}" target="_self">#{pad(nxt["dex"])} {escape(nxt["label"])} →</a>' if nxt else ""
    html(f'<div class="pager">{prev_html}{next_html}</div>')


# ---------------------------------------------------------------- page
html('<div class="brand"><span class="lens"></span><span><b>National Pokédex</b><small>Gen I → Legends: Z-A</small></span></div>')

try:
    index = load_index()
except requests.RequestException:
    st.error("Couldn’t reach PokéAPI to load the Pokédex. Check your connection, then reload the page.")
    st.stop()

lookup = {p["name"]: p for p in index}
current = (st.query_params.get("p") or "").lower()
names = [p["name"] for p in index]
choice = st.selectbox("Search Pokémon", names, index=names.index(current) if current in lookup else None,
                      placeholder="Search by name: Charizard, Mega Lucario, Alolan Vulpix…",
                      format_func=lambda n: f"#{pad(lookup[n]['dex'])}  {lookup[n]['label']}")
if choice and choice != current:
    st.query_params["p"] = choice
    st.rerun()

if current:
    detail(current, index)
else:
    browse(index)

html('<div class="foot"><span>Unofficial fan project. Data and sprites from <a href="https://pokeapi.co/" target="_blank">PokéAPI</a>, '
     'no API key required.</span><span>Pokémon and character names are trademarks of Nintendo, Creatures and Game Freak.</span></div>')
