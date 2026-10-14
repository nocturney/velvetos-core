// Offline DOM-contract test for the generated RustDesk private viewer.
// No browser, OS URI handler, network, or remote session is invoked.
"use strict";
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
const page = fs.readFileSync(process.argv[2], "utf8");
const inventoryTag = page.match(/<script id="embedded-inventory" type="application\/json">([\s\S]*?)<\/script>/);
const jsTag = page.match(/<script>\s*([\s\S]*?)<\/script>\s*<\/body>/);
assert(inventoryTag && jsTag, "generated page must contain embedded data and script");
const data = JSON.parse(inventoryTag[1]);
class Element {
  constructor(tag, id="") {
    this.tagName = tag;
    this.id = id;
    this.children = [];
    this.attributes = {};
    this.listeners = {};
    this.textContent = "";
    this.value = "";
    this.href = "";
    this.className = "";
    this.rel = "";
  }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  setAttribute(name, value) { this.attributes[name] = value; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
}
const ids = [
  "embedded-inventory", "machines", "resultCount", "search", "presence",
  "sourceType", "dataKind", "total", "online", "offline", "unknown", "dataStamp",
  "buildStatus", "previewSubtitle", "footerMode",
];
const nodes = Object.fromEntries(ids.map(id => [id, new Element("div", id)]));
nodes["embedded-inventory"].textContent = inventoryTag[1];
nodes["presence"].value = "ALL";
const document = {
  getElementById(id) { assert(nodes[id], "missing referenced element: "+id); return nodes[id]; },
  createElement(tag) { return new Element(tag); },
};
let navigationAttempted = false;
const window = {
  set location(value) { navigationAttempted = true; throw Error("unexpected automatic navigation"); },
  prompt() { throw Error("manual copy fallback is not part of test"); },
};
vm.runInNewContext(jsTag[1], {
  document, window, navigator: {}, console, Date, Intl, Number, String,
  encodeURIComponent, Error,
}, {timeout: 1500});
function descend(el) {
  return [el, ...el.children.flatMap(child => descend(child))];
}
const all = descend(nodes["machines"]);
const titles = all.filter(el => el.className === "machine-title");
assert.strictEqual(titles.length, data.devices.length, "device title row count mismatch");
data.devices.forEach((d, i) => {
  const expectedTitle = data.state === "REGISTRY_READ_ONLY" && d.name_source === "unmatched"
    ? "מחשב ללא שם מאומת" : (d.display_name || d.device_id);
  assert.strictEqual(titles[i].textContent, expectedTitle,
                     "human-friendly title mismatched for row " + i);
});
const native = all.filter(el => el.tagName === "a");
const safe = data.devices.filter(d =>
  typeof d.device_id === "string" &&
  /^[A-Za-z0-9][A-Za-z0-9._@-]{2,99}$/.test(d.device_id)
);
const enabled = data.state === "REGISTRY_READ_ONLY" && data.native_connect === true;
assert.strictEqual(native.length, enabled ? safe.length : 0, "wrong native link count");
for (let i=0;i<native.length;i++) {
  const a=native[i], id=safe[i].device_id;
  assert.strictEqual(a.href, "rustdesk://connection/new/" + encodeURIComponent(id));
  assert.strictEqual(a.attributes["data-manual-native-launch"], "true");
  assert.strictEqual(a.rel, "noopener noreferrer");
  assert(!a.listeners.click, "link click must be manual OS link, not JS remote control");
}
assert(!navigationAttempted, "no automatic navigation allowed");
assert(!all.some(e => e.tagName === "iframe"), "no embedded remote frames");
if (enabled) {
  assert(nodes["buildStatus"].textContent.includes("MANUAL"), "manual label missing");
  assert(nodes["previewSubtitle"].textContent.includes("לחיצה"), "operator click label missing");
}
console.log("NATIVE_LINK_DOM_OK links=" + native.length +
            " manual=" + enabled + " no-auto-navigation=true");
