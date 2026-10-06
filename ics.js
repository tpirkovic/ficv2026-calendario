// Genera un archivo .ics (iCalendar) a partir de funciones seleccionadas.
// Valdivia en octubre 2026 está en horario de verano de Chile (UTC-3), así que se escribe en UTC.
// ponytail: offset fijo, válido solo para fechas del festival (sep–abr); usar TZID+VTIMEZONE si cambia la fecha.
const UTC_OFFSET_H = 3;
const DURATION_MIN = 120; // la programación no trae duración; se asume 2 h

function icsDate(day, time) { // ("Lunes 12", "19:30") -> "20261012T223000Z"
  const [h, m] = time.split(":").map(Number);
  const d = new Date(Date.UTC(2026, 9, Number(day.split(" ")[1]), h + UTC_OFFSET_H, m));
  return d.toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
}

function icsEnd(start) {
  const d = new Date(start.replace(/(\d{4})(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)Z/, "$1-$2-$3T$4:$5:$6Z"));
  return new Date(d.getTime() + DURATION_MIN * 60000).toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
}

const icsText = s => String(s).replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\n/g, "\\n");
function fold(line) { // RFC 5545: líneas de máx. 75 octetos; las de continuación empiezan con espacio
  const out = []; let cur = "", n = 0;
  for (const ch of line) {
    const b = new TextEncoder().encode(ch).length;
    if (n + b > (out.length ? 74 : 75)) { out.push(cur); cur = ""; n = 0; }
    cur += ch; n += b;
  }
  return [...out, cur].join("\r\n ");
}

// slots: [{key, day, time, venue, films:[{t,d,c,s,a,p}]}]
function buildICS(slots, owner) {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
  const events = slots.map(s => {
    const f0 = s.films[0], many = s.films.length > 1;
    const title = many ? (f0.s || f0.c) : f0.t;
    const desc = [
      many ? s.films.map(f => `• ${f.t}${f.d ? " (" + f.d + ")" : ""}`).join("\n") : [f0.d, f0.p].filter(Boolean).join(" · "),
      [f0.c, f0.s].filter(Boolean).join(" · "),
      "Acceso: " + [...new Set(s.films.flatMap(f => f.a))].join(" / "),
      "Duración estimada; revisa 33.ficvaldivia.cl",
    ].join("\n");
    const start = icsDate(s.day, s.time);
    return ["BEGIN:VEVENT", `UID:${encodeURIComponent(s.key)}@ficv2026`, `DTSTAMP:${stamp}`,
      `DTSTART:${start}`, `DTEND:${icsEnd(start)}`, `SUMMARY:${icsText("FICV · " + title)}`,
      `LOCATION:${icsText(s.venue + ", Valdivia")}`, `DESCRIPTION:${icsText(desc)}`, "END:VEVENT"];
  });
  return ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ficv2026-calendario//ES", "CALSCALE:GREGORIAN",
    `X-WR-CALNAME:${icsText("FICValdivia 2026 · " + owner)}`, ...events.flat(), "END:VCALENDAR"]
    .map(fold).join("\r\n") + "\r\n";
}

if (typeof module !== "undefined") module.exports = { buildICS, icsDate, icsEnd };
