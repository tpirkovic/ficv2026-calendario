"""Regenera data.js desde la API pública de 33.ficvaldivia.cl (Softr) y baja imágenes faltantes.

Uso: python3 actualizar.py
"""
import json, os, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

SITE = "https://33.ficvaldivia.cl"
APP = "/v1/datasource/applications/371dbf42-7474-43b7-878b-22fe806a33f5"
LIST_PAGE = "ab680307-8871-49a9-9795-5f443ef17c49"  # /programacion
FICHA_PAGE = "5ed87a4a-dbb5-4bfa-b4bc-48c2f03099e4"  # /ficha
LIST = f"{APP}/pages/{LIST_PAGE}/blocks/e13fcdaf-40a2-43e4-8d76-3f595563a0cd/datasources/1959fb79-8120-49b3-81f2-9905cd450a5e/records"
FILM = f"{APP}/pages/{FICHA_PAGE}/blocks/8569b254-26f8-44f4-abda-ce3e5abb5cc5/datasources/4e3b5edb-4f63-4236-9076-2f35bd22055d/records/"
FUNCS = f"{APP}/pages/{FICHA_PAGE}/blocks/12152f56-407a-4a5c-aaaf-734886a31b86/datasources/2c97f264-dc6a-47bd-9344-e2accffcfa30/records"
OPT = {"timeZone": "America/Santiago", "userLocale": "en-US"}
HERE = os.path.dirname(os.path.abspath(__file__))


def post(path, body, page, referer=None):
    req = urllib.request.Request(SITE + path, json.dumps(body).encode(), {
        "content-type": "application/json", "softr-page-id": page, "Referer": referer or SITE + "/programacion"})
    for intento in range(4):  # el sitio a veces corta conexiones si se le pide mucho
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except OSError:
            if intento == 3: raise
            time.sleep(2 * (intento + 1))


def paged(path, page, referer=None, ctx=None):
    items, off = [], 0
    while True:  # la API ignora count > 50 y no marca el final de forma fiable
        r = post(path, {"options": OPT, "pageContext": ctx, "filterCriteria": {}, "sortingOption": [{"sortingField": "tgI6Y", "sortType": "ASC"}] if not ctx else [],
                        "pagingOption": {"offset": str(off), "count": 50}}, page, referer)
        items += r.get("items") or []
        if len(r.get("items") or []) < 50: return items
        off += 50


clean = lambda s: re.sub(r"\s*\n+\s*", " — ", s or "").strip()
labels = lambda v: [x["label"] for x in v or []]

films = paged(LIST, LIST_PAGE)
print(len(films), "películas")


def detail(item):
    fid = item["id"]
    ref = f"{SITE}/ficha?recordId={fid}"
    rec = post(FILM + fid, {"options": OPT, "pageContext": {"recordId": fid}}, FICHA_PAGE, ref)
    funcs = paged(FUNCS, FICHA_PAGE, ref, {"recordId": fid})
    return fid, rec["fields"].get("gfc9z"), {f"{x['fields']['FILBc']} - {(x['fields'].get('yQUbl') or {}).get('label', '')}":
                                              [x["fields"].get("5C4sL"), (x["fields"].get("TA3Zy") or {}).get("label")] for x in funcs}


with ThreadPoolExecutor(4) as ex:
    details = list(ex.map(detail, films))
film_dur = {fid: d for fid, d, _ in details}
sessions = {k: v for *_, s in details for k, v in s.items()}
print(len(sessions), "funciones")

rows = []
for it in films:
    f = it["fields"]
    rows.append([it["id"], clean(f.get("tgI6Y")), clean(f.get("EStWy")), (f.get("9tf35") or {}).get("label", ""),
                 ", ".join(labels(f.get("VWKRF"))), list(dict.fromkeys(labels(f.get("U11RE")))),
                 ", ".join(labels(f.get("cIddG"))).title(), f.get("LVmhF") or [], film_dur.get(it["id"])])
    img = os.path.join(HERE, "img", it["id"] + ".jpg")
    thumbs = ((f.get("mllcQ") or [{}])[0]).get("thumbnails") or []
    if not os.path.exists(img) and thumbs:  # imágenes nuevas: miniatura de 600 px tal cual
        urllib.request.urlretrieve(next((t["url"] for t in thumbs if t["size"] == "medium"), thumbs[0]["url"]), img)

with open(os.path.join(HERE, "data.js"), "w") as out:
    out.write("// Generado por actualizar.py desde 33.ficvaldivia.cl\n"
              "// FILMS: [id, título, dirección, categoría, subcategoría, [acceso], país, [\"Día N - HH:MM - Sala\"], duración film]\n"
              "// SESSIONS: {\"Día N - HH:MM - Sala\": [duración función en min, estado]}\n"
              f"const FILMS = {json.dumps(rows, ensure_ascii=False, separators=(',', ':'))};\n"
              f"const SESSIONS = {json.dumps(sessions, ensure_ascii=False, separators=(',', ':'))};\n")
print("data.js listo")
