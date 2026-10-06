"""Genera programacion-ficv2026.pdf (programación completa) desde data.js + img/ (HTML -> Chrome headless).

Uso: python3 programa_pdf.py   (correr después de actualizar.py)
"""
import json, re, html, subprocess, os, datetime, shutil
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(f"{HERE}/data.js").read()
rows = json.loads(re.search(r"const FILMS = (.*);\n", src).group(1))
SESSIONS = json.loads(re.search(r"const SESSIONS = (.*);\n", src).group(1))
DAYS = ["Lunes 12", "Martes 13", "Miércoles 14", "Jueves 15", "Viernes 16", "Sábado 17", "Domingo 18"]
CAT_COLORS = {  # paleta derivada del logo: amarillo F0E04A, coral D4625F, negro 1F1E21
    "En Competencia": ("#D4625F", "#fff"),
    "Filmes de Apertura y Clausura": ("#1F1E21", "#F0E04A"),
    "Muestra de Cine Contemporáneo": ("#2F6F6B", "#fff"),
    "Muestra de Cine Chileno": ("#3B5A9A", "#fff"),
    "Cineastas en Foco": ("#7A3E6E", "#fff"),
    "Muestra Contraplanos de la Historia": ("#8A5A2B", "#fff"),
    "Nuevas Narrativas": ("#C98A1A", "#1F1E21"),
    "Pásate una Película": ("#E9A49F", "#1F1E21"),
    "Actividades Paralelas": ("#8C8A84", "#fff"),
    "Ceremonias": ("#F0E04A", "#1F1E21"),
}
ACCESS = {"Entrada Liberada": "Liberada", "Con Entrada o Acreditación": "Entrada / Acreditación",
          "Con Inscripción Previa": "Inscripción previa", "Solo con Invitación": "Solo invitación"}
edge = lambda c: "#1F1E21" if c == "Ceremonias" else CAT_COLORS[c][0]  # amarillo sobre blanco necesita borde
e = lambda s: html.escape(re.sub(r"\s*\n+\s*", " — ", s or "").strip())

# Una función = día + hora + sala; los programas de cortos comparten función.
slots = defaultdict(list)
dur = {}  # minutos de cada función
for fid, t, d, c, sub, acc, pais, funcs, fd in rows:
    film = dict(id=fid, t=t, d=d, c=c, s=sub, a=acc, p=pais, fd=re.sub(r"'\s*$", " min", fd or ""))
    for f in funcs:
        day, time, *v = f.split(" - ")
        key = (day, time.zfill(5), " - ".join(v))
        slots[key].append(film)
        dur[key] = (SESSIONS.get(f) or [None])[0]

def span(time, mins):  # "11:30", 105 -> "11:30–13:15 · 105 min"
    if not mins: return f"<b>{time}</b>"
    h, m = map(int, time.split(":")); end = h * 60 + m + mins
    return f"<b>{time}–{end // 60 % 24:02d}:{end % 60:02d}</b>"

def tags(films):
    cats = list(dict.fromkeys(f["c"] for f in films))
    subs = list(dict.fromkeys(f["s"] for f in films if f["s"]))
    accs = list(dict.fromkeys(a for f in films for a in f["a"]))
    out = [f'<span class="tag" style="background:{CAT_COLORS[c][0]};color:{CAT_COLORS[c][1]};border:.25mm solid {edge(c)}">{e(c)}</span>' for c in cats]
    out += [f'<span class="tag sub">{e(s)}</span>' for s in subs if s not in cats]
    out += [f'<span class="tag acc{" free" if a == "Entrada Liberada" else ""}">{ACCESS.get(a, e(a))}</span>' for a in accs]
    return "".join(out)

def card(time, venue, films, mins):
    f0 = films[0]
    if len(films) == 1:
        body = f'<h3>{e(f0["t"])}</h3><p class="by">{" · ".join(x for x in (e(f0["d"]), e(f0["p"]), e(f0["fd"])) if x)}</p>'
    else:
        items = "".join(f'<li>{e(f["t"])}' + (f' <span>· {" · ".join(x for x in (e(f["d"]), e(f["fd"])) if x)}</span>' if f["d"] or f["fd"] else "") + '</li>' for f in films)
        body = f'<h3>{e(f0["s"] or f0["c"])} <small>· {len(films)} obras</small></h3><ul>{items}</ul>'
    return (f'<article class="card"><img src="img/{f0["id"]}.jpg" alt="">'
            f'<div class="info"><p class="when">{span(time, mins)} {e(venue)}</p>{body}<div class="tags">{tags(films)}</div></div></article>')

days_html = []
for day in DAYS:
    ks = sorted((k for k in slots if k[0] == day), key=lambda k: (k[1], k[2]))
    wk, n = day.split(" ")
    cards = "".join(card(k[1], k[2], slots[k], dur[k]) for k in ks)
    days_html.append(f'<section class="day" style="page:d{DAYS.index(day)}"><header class="band"><span class="wk">{wk}</span><span class="n">{n}</span>'
                     f'<span class="meta">octubre 2026 · {len(ks)} funciones</span></header><div class="cols">{cards}</div></section>')

counts = "".join(f'<li><b>{d.split()[0][:3]} {d.split()[1]}</b> {sum(1 for k in slots if k[0] == d)}</li>' for d in DAYS)
legend = "".join(f'<li><span class="tag" style="background:{b};color:{f};border:.25mm solid {edge(c)}">{e(c)}</span></li>' for c, (b, f) in CAT_COLORS.items())
acc_legend = "".join(f'<li><span class="tag acc{" free" if k == "Entrada Liberada" else ""}">{v}</span> {e(k)}</li>' for k, v in ACCESS.items())

day_pages = "".join(f'@page d{i} {{ @top-left {{ content: "{d.upper()} OCT."; font: 900 9pt Lato, sans-serif; color: #D4625F; letter-spacing: .06em; }} }}\n' for i, d in enumerate(DAYS))
doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Calendario FICValdivia 2026</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap">
<style>
:root {{ --yellow:#F0E04A; --coral:#D4625F; --ink:#1F1E21; --muted:#5f5d63; --line:#e4e1d6; }}
@page {{ size: A4; margin: 14mm 11mm 12mm; @bottom-right {{ content: counter(page); font: 700 8pt Lato, sans-serif; color: #5f5d63; }} }}
@page cover {{ margin: 0; @bottom-right {{ content: none; }} }}
{day_pages}
* {{ box-sizing: border-box; }}
body {{ margin:0; font: 8.3pt/1.3 Lato, "Helvetica Neue", Arial, sans-serif; color: var(--ink); }}
.cover {{ page: cover; height: 297mm; background: var(--yellow); display:flex; flex-direction:column; align-items:center; padding: 14mm 14mm 10mm; break-after: page; }}
.cover img {{ width: 92mm; }}
.cover h1 {{ font: 900 24pt/1 Lato, sans-serif; letter-spacing:.04em; text-transform: uppercase; margin: 7mm 0 1mm; }}
.cover .sub {{ color: var(--coral); font-weight:900; font-size: 12pt; letter-spacing: .03em; margin:0 0 8mm; }}
.cover h2 {{ font: 900 9pt Lato; text-transform: uppercase; letter-spacing:.08em; margin: 0 0 2.5mm; }}
.legend {{ display:grid; grid-template-columns: 1.2fr 1fr; gap: 10mm; width: 100%; }}
.legend ul {{ list-style:none; margin:0; padding:0; display:grid; gap: 2mm; }}
.days-count {{ list-style:none; display:flex; gap: 3mm; padding:0; margin: 0 0 9mm; }}
.days-count li {{ background: var(--ink); color: var(--yellow); padding: 2mm 3mm; border-radius: 2mm; text-align:center; font-size: 8pt; }}
.days-count b {{ display:block; color:#fff; font-size: 9pt; text-transform: uppercase; }}
.note {{ margin-top:auto; font-size: 7.5pt; color: var(--muted); text-align:center; }}
.day {{ break-before: page; }}
.band {{ background: var(--yellow); display:flex; align-items: baseline; gap: 3mm; padding: 3mm 5mm; margin-bottom: 4mm; }}
.band .wk {{ font: 900 22pt/1 Lato; text-transform: uppercase; letter-spacing: .05em; }}
.band .n {{ font: 900 22pt/1 Lato; color: var(--coral); }}
.band .meta {{ margin-left:auto; font-weight:700; font-size: 9pt; }}
.cols {{ column-count: 2; column-gap: 5mm; }}
.card {{ break-inside: avoid; display:grid; grid-template-columns: 29mm 1fr; gap: 3mm; padding: 2.4mm 0; border-bottom: .3mm solid var(--line); }}
.card img {{ width: 29mm; height: 19.3mm; object-fit: cover; border-radius: 1mm; background: var(--line); }}
.info {{ min-width: 0; }}
.when {{ margin:0; font-size: 7.5pt; color: var(--muted); }}
.when .dur {{ font-weight: 700; color: var(--ink); }}
.when b {{ background: var(--ink); color: var(--yellow); padding: .3mm 1.3mm; border-radius: .8mm; margin-right: 1mm; font-size: 8pt; }}
h3 {{ font: 900 9.3pt/1.2 Lato; margin: 1mm 0 .4mm; }}
h3 small {{ font-weight: 700; color: var(--coral); font-size: 7.5pt; }}
.by {{ margin: 0; color: var(--muted); font-size: 7.6pt; }}
ul {{ margin: .5mm 0 0; padding-left: 3.5mm; font-size: 7.4pt; }}
ul span {{ color: var(--muted); }}
.tags {{ display:flex; flex-wrap: wrap; gap: 1mm; margin-top: 1.2mm; }}
.tag {{ font-size: 6.6pt; font-weight: 700; padding: .35mm 1.6mm; border-radius: 5mm; white-space: nowrap; }}
.tag.sub {{ border: .25mm solid var(--ink); white-space: normal; }}
.tag.acc {{ background: #fff; border: .25mm solid var(--muted); color: var(--muted); }}
.tag.acc.free {{ border-color: var(--coral); color: var(--coral); }}
.cover .tag {{ font-size: 8pt; }}
</style></head><body>
<section class="cover"><img src="logo.png" alt="FICValdivia 33">
<h1>Calendario de programación</h1><p class="sub">12–18 OCT. 2026 · {len(slots)} funciones · {len(rows)} obras</p>
<ul class="days-count">{counts}</ul>
<div class="legend"><div><h2>Categorías</h2><ul>{legend}</ul></div><div><h2>Acceso</h2><ul>{acc_legend}</ul>
<h2 style="margin-top:6mm">Cómo leerlo</h2><p>Cada día empieza en una página nueva. Las funciones van por hora, con su hora de inicio y término; junto a cada obra va lo que dura la película. Los programas de cortos aparecen como una sola función con la lista de obras. La etiqueta con borde negro es la sub categoría.</p></div></div>
<p class="note">Arma tu agenda en tpirkovic.github.io/ficv2026-calendario<br>Datos de 33.ficvaldivia.cl/programacion al {datetime.date.today():%d-%m-%Y}. Revisa la web oficial por cambios de última hora.</p></section>
{"".join(days_html)}
</body></html>"""
tmp = f"{HERE}/.programa.html"  # junto a img/ para que las rutas relativas funcionen
open(tmp, "w").write(doc)
CHROME = next(p for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Mac
                           shutil.which("google-chrome"), shutil.which("chromium")] if p and os.path.exists(p))  # Linux (GitHub Actions)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                "--no-pdf-header-footer", "--virtual-time-budget=10000", "--allow-file-access-from-files",
                f"--print-to-pdf={HERE}/programacion-ficv2026.pdf", f"file://{tmp}"],
               check=True, capture_output=True)
os.remove(tmp)
print("programacion-ficv2026.pdf listo,", len(slots), "funciones")
