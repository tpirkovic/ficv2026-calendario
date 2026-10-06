// node ics.test.js
const assert = require("assert");
const { buildICS, icsDate, icsEnd } = require("./ics.js");

assert.strictEqual(icsDate("Lunes 12", "19:30"), "20261012T223000Z");
assert.strictEqual(icsDate("Domingo 18", "22:00"), "20261019T010000Z"); // cruza medianoche en UTC
assert.strictEqual(icsEnd("20261012T223000Z"), "20261013T003000Z");

const ics = buildICS([{ key: "Lunes 12|19:30|Cine Club UACh", day: "Lunes 12", time: "19:30", venue: "Cine Club UACh",
  films: [{ t: "Una, película; larga".repeat(6), d: "X", c: "En Competencia", s: "", a: ["Entrada Liberada"], p: "Chile" }] }], "Ana");
assert(ics.startsWith("BEGIN:VCALENDAR\r\n") && ics.endsWith("END:VCALENDAR\r\n"));
assert(ics.includes("Una\\, película\\; larga"));
assert(ics.split("\r\n").every(l => Buffer.byteLength(l) <= 75), "líneas plegadas");
console.log("ok");
