// Enhancements for the rendered README: search and filters, a sidebar with
// the table of contents, and sortable tables. The README stays plain
// Markdown; everything here is added in the browser, and the page still works
// without it.
//
// Facets (verifier, year, markers, code links) come from data/list.json,
// which scripts/build_data.py writes from the README at build time. If that
// file is missing, the search box still filters by text.

const main = document.querySelector("main.markdown-body");
const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

// ---------------------------------------------------------------- tables

function numberIn(text) {
  const match = text.match(/^\s*(\d[\d,]*(?:\.\d+)?)\s*([KkMm](?![a-z]))?/);
  if (!match) return null;
  const value = parseFloat(match[1].replace(/,/g, ""));
  return match[2] ? value * (/k/i.test(match[2]) ? 1e3 : 1e6) : value;
}

function makeTablesSortable(root) {
  for (const table of root.querySelectorAll("table")) {
    const body = table.tBodies[0];
    if (!table.tHead || !body || body.rows.length < 5) continue;
    [...body.rows].forEach((row, i) => (row.dataset.order = i));
    [...table.tHead.rows[0].cells].forEach((th, column) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "sort";
      button.append(...th.childNodes);
      th.append(button);
      th.setAttribute("aria-sort", "none");
      button.addEventListener("click", () => sortTable(table, column, th));
    });
  }
}

function sortTable(table, column, th) {
  const direction = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
  for (const cell of th.parentElement.cells) cell.setAttribute("aria-sort", "none");
  th.setAttribute("aria-sort", direction);
  const body = table.tBodies[0];
  const rows = [...body.rows].map((row) => {
    const text = row.cells[column]?.textContent.trim() ?? "";
    return { row, text, number: numberIn(text), order: Number(row.dataset.order) };
  });
  // Sort by number when most cells start with one ("71K proofs", "750+ programs");
  // cells without a number then go last in either direction.
  const numeric = rows.filter((r) => r.number !== null).length >= rows.length / 2;
  const sign = direction === "ascending" ? 1 : -1;
  rows.sort((a, b) => {
    if (numeric && (a.number === null) !== (b.number === null)) return a.number === null ? 1 : -1;
    const order = numeric && a.number !== null ? a.number - b.number : collator.compare(a.text, b.text);
    return order * sign || a.order - b.order;
  });
  body.append(...rows.map((r) => r.row));
}

// ------------------------------------------------------------------ home

function webLink(element) {
  for (const node of element.childNodes) {
    if (node.nodeType === Node.TEXT_NODE && !node.textContent.trim()) continue;
    if (node.nodeType !== Node.ELEMENT_NODE) return null;
    if (node.tagName === "P") return webLink(node);
    return node.tagName === "A" && /^https?:/.test(node.getAttribute("href") || "") ? node : null;
  }
  return null;
}

// Split the page into sections and find every entry, in document order.
function index(root) {
  const sections = [];
  const blocks = [];
  const entries = [];
  const groups = [];
  const strays = [];
  let h2 = null;
  let current = null;
  let previous = null;

  for (const element of root.children) {
    const tag = element.tagName;
    if (tag === "H2" || tag === "H3") {
      current = { heading: element, level: tag === "H2" ? 2 : 3, parent: tag === "H3" ? h2 : null, entries: [] };
      if (tag === "H2") h2 = current;
      sections.push(current);
      blocks.push({ element, kind: "heading", section: current });
    } else if (tag === "BLOCKQUOTE" && previous && /^H[23]$/.test(previous.tagName)) {
      blocks.push({ element, kind: "tagline", section: current });
    } else {
      const found = [];
      const items = tag === "TABLE" ? element.querySelectorAll("tbody tr") : tag === "UL" || tag === "OL" ? element.querySelectorAll("li") : [];
      for (const item of items) {
        const link = webLink(tag === "TABLE" ? item.cells[0] : item);
        if (link) {
          const group = item.parentElement.closest("li");
          found.push({ element: item, link, group, section: current });
        } else if (tag !== "TABLE" && !item.querySelector("li")) {
          strays.push(item);
        }
      }
      if (found.length) {
        entries.push(...found);
        if (current) {
          current.entries.push(...found);
          if (current.parent) current.parent.entries.push(...found);
        }
        for (const entry of found) {
          if (!entry.group) continue;
          let group = groups.find((g) => g.element === entry.group);
          if (!group) groups.push((group = { element: entry.group, entries: [] }));
          group.entries.push(entry);
        }
        blocks.push({ element, kind: "entries", entries: found });
      } else {
        blocks.push({ element, kind: tag === "H1" ? "title" : "other" });
      }
    }
    previous = element;
  }
  return { sections, blocks, entries, groups, strays: strays.filter((li) => li.closest("ul, ol") && entries.some((e) => e.element.parentElement === li.parentElement)) };
}

function attachData(entries, data) {
  const queues = new Map();
  for (const item of data.entries) {
    if (!queues.has(item.url)) queues.set(item.url, []);
    queues.get(item.url).push(item);
  }
  for (const entry of entries) entry.data = queues.get(entry.link.getAttribute("href"))?.shift() ?? null;
}

const ONLY = [
  { key: "start", label: "⭐ Start here", test: (d) => d.markers.includes("start") },
  { key: "production", label: "🏭 In production", test: (d) => d.markers.includes("production") },
  { key: "code", label: "Has code", test: (d) => Boolean(d.code) },
  { key: "free", label: "Free", test: (d) => !d.markers.includes("paid") },
];

function readState() {
  const params = new URLSearchParams(location.search);
  const list = (name) => (params.get(name) || "").split(",").filter(Boolean);
  return {
    q: params.get("q") || "",
    verifiers: new Set(list("v")),
    since: Number(params.get("since")) || null,
    only: new Set(list("only").filter((key) => ONLY.some((o) => o.key === key))),
  };
}

function writeState(state) {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  if (state.verifiers.size) params.set("v", [...state.verifiers].join(","));
  if (state.since) params.set("since", state.since);
  if (state.only.size) params.set("only", [...state.only].join(","));
  const query = params.toString().replace(/%2C/g, ",");
  history.replaceState(null, "", (query ? `?${query}` : location.pathname) + location.hash);
}

function element(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value === false || value == null) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  node.append(...children);
  return node;
}

function escapeRegExp(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function setUpHome(root, contents) {
  const model = index(root);
  const known = new Map(model.blocks.filter((b) => b.kind !== "other").map((b) => [b.element, b]));
  for (const entry of model.entries) {
    const context = [entry.group?.firstChild?.textContent, entry.section?.heading.textContent].filter(Boolean).join(" ");
    entry.text = `${entry.element.textContent} ${context}`.toLowerCase();
    entry.visible = true;
  }

  const state = readState();
  const finder = buildFinder(state);
  const empty = element("p", { class: "finder-empty", hidden: true }, "No entries match. ", element("button", { type: "button", class: "link-button", onclick: () => reset() }, "Clear the filters"));
  contents.before(finder.root, empty);

  const sidebar = buildSidebar(root, contents);
  // The stylesheet decides when the sidebar shows; the search box follows it.
  let inSidebar = null;
  const place = () => {
    const wide = Boolean(sidebar) && getComputedStyle(sidebar.aside).display !== "none";
    if (wide === inSidebar) return;
    inSidebar = wide;
    if (wide) sidebar.finderSlot.append(finder.root);
    else empty.before(finder.root);
    finder.root.classList.toggle("in-sidebar", wide);
  };
  addEventListener("resize", () => requestAnimationFrame(place));
  place();

  function reset() {
    state.q = "";
    state.verifiers.clear();
    state.since = null;
    state.only.clear();
    finder.sync(state);
    apply();
  }

  function matches(entry, terms) {
    if (!terms.every((term) => entry.text.includes(term))) return false;
    const data = entry.data;
    if (state.verifiers.size && !(data && data.verifiers.some((v) => state.verifiers.has(v)))) return false;
    if (state.since && !(data && data.year >= state.since)) return false;
    for (const only of ONLY) if (state.only.has(only.key) && !(data && only.test(data))) return false;
    return true;
  }

  function apply() {
    const terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    const active = terms.length > 0 || state.verifiers.size > 0 || state.since !== null || state.only.size > 0;
    let shown = 0;
    for (const entry of model.entries) {
      entry.visible = !active || matches(entry, terms);
      entry.element.classList.toggle("is-filtered-out", !entry.visible);
      if (entry.visible) shown++;
    }
    for (const group of model.groups) group.element.classList.toggle("is-filtered-out", !group.entries.some((e) => e.visible));
    for (const stray of model.strays) stray.classList.toggle("is-filtered-out", active);
    for (const section of model.sections) section.visible = !active || section.entries.some((e) => e.visible);
    // Walk the live page rather than the indexed blocks: Mermaid replaces the
    // diagram's <pre> after this script has run. Prose hides while filtering.
    for (const child of root.children) {
      if (child === finder.root || child === empty) continue;
      const block = known.get(child);
      let hide = active;
      if (block?.kind === "heading" || block?.kind === "tagline") hide = !block.section.visible;
      else if (block?.kind === "entries") hide = !block.entries.some((e) => e.visible);
      else if (block?.kind === "title") hide = false;
      child.classList.toggle("is-filtered-out", hide);
    }
    empty.hidden = !active || shown > 0;
    finder.count(active ? `${shown} ${shown === 1 ? "match" : "matches"}` : "", active);
    highlight(model.entries, terms);
    if (sidebar) sidebar.counts(model.sections, active);
    writeState(state);
  }

  finder.onChange((change) => {
    Object.assign(state, change);
    apply();
  });
  finder.onReset(reset);

  addEventListener("keydown", (event) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName) || document.activeElement?.isContentEditable;
    if (event.key === "/" && !typing && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      finder.focus();
    }
  });

  // Facet filters from a shared link wait for the data; a text query does not.
  const waitsForData = state.verifiers.size > 0 || state.since !== null || state.only.size > 0;
  fetch(root.dataset.list)
    .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
    .then((data) => {
      attachData(model.entries, data);
      finder.facets(data.entries, state);
      apply();
    })
    .catch(() => {
      state.verifiers.clear();
      state.since = null;
      state.only.clear();
      apply();
    });
  if (!waitsForData) apply();
}

function highlight(entries, terms) {
  for (const mark of main.querySelectorAll("mark.hit")) {
    const parent = mark.parentNode;
    mark.replaceWith(mark.textContent);
    parent.normalize();
  }
  const words = terms.filter((term) => term.length > 1);
  if (!words.length) return;
  const pattern = new RegExp(words.map(escapeRegExp).join("|"), "gi");
  for (const entry of entries) {
    if (!entry.visible) continue;
    const walker = document.createTreeWalker(entry.element, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const text = node.nodeValue;
      const found = [...text.matchAll(pattern)];
      if (!found.length) continue;
      const fragment = document.createDocumentFragment();
      let last = 0;
      for (const match of found) {
        fragment.append(text.slice(last, match.index), element("mark", { class: "hit" }, match[0]));
        last = match.index + match[0].length;
      }
      fragment.append(text.slice(last));
      node.replaceWith(fragment);
    }
  }
}

function buildFinder(state) {
  let listener = () => {};
  let resetListener = () => {};
  const input = element("input", {
    type: "search",
    placeholder: "Search the list",
    "aria-label": "Search entries",
    autocomplete: "off",
    spellcheck: "false",
    value: state.q,
  });
  const icon = element("span", { class: "finder-icon", "aria-hidden": "true" });
  icon.innerHTML = '<svg viewBox="0 0 16 16" width="16" height="16"><path fill="currentColor" d="M10.68 11.74a6 6 0 1 1 1.06-1.06l3.04 3.04a.75.75 0 1 1-1.06 1.06l-3.04-3.04ZM11.5 7a4.5 4.5 0 1 0-9 0 4.5 4.5 0 0 0 9 0Z"/></svg>';
  const count = element("span", { class: "finder-count", role: "status", "aria-live": "polite" });
  const toggle = element("button", { type: "button", class: "finder-toggle", "aria-expanded": "false", "aria-controls": "finder-panel" }, "Filters");
  const chips = element("div", { class: "chips", role: "group", "aria-label": "Verifier" });
  const verifierRow = element("div", { class: "finder-group", hidden: true }, element("div", { class: "finder-label" }, "Verifier"), chips);
  const onlyButtons = ONLY.map((only) =>
    element("button", { type: "button", class: "chip", "data-only": only.key, "aria-pressed": String(state.only.has(only.key)) }, only.label)
  );
  const year = element("select", { "aria-label": "Year" }, element("option", { value: "" }, "Any year"));
  const clear = element("button", { type: "button", class: "link-button finder-clear", hidden: true }, "Clear all");
  const showRow = element("div", { class: "finder-group", hidden: true }, element("div", { class: "finder-label" }, "Show"), element("div", { class: "chips" }, ...onlyButtons, year));
  const panel = element("div", { class: "finder-panel", id: "finder-panel" }, verifierRow, showRow, clear);
  const root = element(
    "section",
    { class: "finder", "aria-label": "Search and filter the list" },
    element("div", { class: "finder-row" }, element("label", { class: "finder-search" }, icon, input, element("kbd", { title: "Press / to search" }, "/")), toggle),
    count,
    panel
  );

  let timer;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => listener({ q: input.value.trim() }), 80);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && input.value) {
      input.value = "";
      listener({ q: "" });
    }
  });
  toggle.addEventListener("click", () => {
    const open = !root.classList.contains("open");
    root.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
  });
  for (const button of onlyButtons) {
    button.addEventListener("click", () => {
      const key = button.dataset.only;
      const only = new Set(state.only);
      if (only.has(key)) only.delete(key);
      else only.add(key);
      button.setAttribute("aria-pressed", String(only.has(key)));
      listener({ only });
    });
  }
  year.addEventListener("change", () => listener({ since: Number(year.value) || null }));
  clear.addEventListener("click", () => resetListener());

  return {
    root,
    focus() {
      input.focus();
      input.select();
      root.scrollIntoView({ block: "nearest" });
    },
    onChange(fn) {
      listener = fn;
    },
    onReset(fn) {
      resetListener = fn;
    },
    count(text, active) {
      count.textContent = text;
      clear.hidden = !active;
      const filters = state.verifiers.size + state.only.size + (state.since ? 1 : 0);
      toggle.textContent = filters ? `Filters (${filters})` : "Filters";
    },
    sync(next) {
      input.value = next.q;
      for (const chip of chips.children) chip.setAttribute("aria-pressed", String(next.verifiers.has(chip.dataset.verifier)));
      for (const button of onlyButtons) button.setAttribute("aria-pressed", String(next.only.has(button.dataset.only)));
      year.value = next.since ? String(next.since) : "";
    },
    facets(entries, current) {
      const counts = new Map();
      for (const entry of entries) for (const v of entry.verifiers) counts.set(v, (counts.get(v) || 0) + 1);
      const verifiers = [...counts].filter(([, n]) => n >= 4).sort((a, b) => b[1] - a[1] || collator.compare(a[0], b[0]));
      for (const [name, n] of verifiers) {
        const chip = element("button", { type: "button", class: "chip", "data-verifier": name, "aria-pressed": String(current.verifiers.has(name)) }, name);
        chip.addEventListener("click", () => {
          const set = new Set(state.verifiers);
          if (set.has(name)) set.delete(name);
          else set.add(name);
          chip.setAttribute("aria-pressed", String(set.has(name)));
          listener({ verifiers: set });
        });
        chips.append(chip);
      }
      const years = entries.map((e) => e.year).filter(Boolean);
      const latest = Math.max(...years);
      for (const y of [latest, latest - 1, latest - 2, 2020]) {
        if (y <= latest && !year.querySelector(`option[value="${y}"]`)) year.append(element("option", { value: String(y) }, y === latest ? String(y) : `Since ${y}`));
      }
      year.value = current.since ? String(current.since) : "";
      verifierRow.hidden = false;
      showRow.hidden = false;
    },
  };
}

function buildSidebar(root, contents) {
  const list = contents.nextElementSibling;
  if (!list || list.tagName !== "UL") return null;
  const toc = list.cloneNode(true);
  toc.removeAttribute("id");
  const links = new Map();
  for (const link of toc.querySelectorAll("a[href^='#']")) {
    const id = decodeURIComponent(link.getAttribute("href").slice(1));
    const label = element("span", { class: "label" }, ...link.childNodes);
    link.append(label, element("span", { class: "n" }));
    links.set(id, link);
  }
  const finderSlot = element("div", { class: "sidebar-finder" });
  const sidebar = element(
    "aside",
    { class: "sidebar", "aria-label": "Search and contents" },
    element("a", { class: "sidebar-title", href: "#" }, document.title),
    finderSlot,
    element("nav", { class: "toc", "aria-label": "Contents" }, toc)
  );
  root.parentElement.prepend(sidebar);
  root.parentElement.classList.add("has-sidebar");

  // Highlight the section being read.
  const headings = [...root.querySelectorAll("h2[id], h3[id]")].filter((h) => links.has(h.id));
  let ticking = false;
  const spy = () => {
    ticking = false;
    let currentId = null;
    for (const heading of headings) {
      if (heading.classList.contains("is-filtered-out")) continue;
      if (heading.getBoundingClientRect().top < 120) currentId = heading.id;
      else break;
    }
    for (const [id, link] of links) {
      if (id === currentId) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    }
    const active = currentId && links.get(currentId);
    if (active && getComputedStyle(sidebar).display !== "none") {
      const box = sidebar.getBoundingClientRect();
      const item = active.getBoundingClientRect();
      if (item.top < box.top + 40 || item.bottom > box.bottom - 40) active.scrollIntoView({ block: "nearest" });
    }
  };
  addEventListener("scroll", () => {
    if (!ticking) requestAnimationFrame(spy);
    ticking = true;
  }, { passive: true });
  spy();

  return {
    aside: sidebar,
    finderSlot,
    counts(sections, active) {
      for (const section of sections) {
        const link = links.get(section.heading.id);
        if (!link) continue;
        const shown = section.entries.filter((e) => e.visible).length;
        link.querySelector(".n").textContent = active && section.entries.length ? String(shown) : "";
        link.classList.toggle("empty", active && shown === 0);
      }
    },
  };
}

// ---------------------------------------------------------------- primers

// Primers keep `text` fences so the Markdown reads the same everywhere. The
// site highlights them by file extension, with Prism, where Prism knows the
// language; the others stay plain rather than borrow a neighbour's grammar.
const PRISM = "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/";
const LANGUAGES = {
  ada: "ada", agda: "agda", c: "c", go: "go", hs: "haskell", idr: "idris",
  java: "java", lisp: "lisp", ml: "ocaml", py: "python", rs: "rust",
  scala: "scala", sml: "sml", v: "coq",
};

// Playgrounds that open code passed in the link, checked with each primer.
// The Verus playground builds a binary, so it needs a main.
const PLAYGROUNDS = {
  lean: {
    label: "Open in the Lean web editor",
    url: (code) => `https://live.lean-lang.org/#code=${encodeURIComponent(code)}`,
  },
  verus: {
    label: "Open in the Verus playground",
    url: (code) =>
      "https://play.verus-lang.org/?version=stable&mode=basic&edition=2021&code=" +
      encodeURIComponent(`${code.trimEnd()}\n\nfn main() {}\n`),
  },
};

function loadScript(src) {
  return new Promise((resolve, reject) => {
    document.head.append(element("script", { src, onload: resolve, onerror: reject }));
  });
}

async function highlightCode(code, language) {
  window.Prism = window.Prism || {};
  window.Prism.manual = true;
  await loadScript(`${PRISM}components/prism-core.min.js`);
  await loadScript(`${PRISM}plugins/autoloader/prism-autoloader.min.js`);
  window.Prism.plugins.autoloader.languages_path = `${PRISM}components/`;
  code.className = `language-${language}`;
  window.Prism.highlightElement(code);
}

function setUpPrimer(primer) {
  const code = primer.querySelector("pre > code");
  if (!code) return;
  const source = code.textContent;
  const extension = (primer.dataset.filename || "").split(".").pop();

  const copy = element("button", { type: "button", class: "primer-button" }, "Copy");
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(source);
      copy.textContent = "Copied";
    } catch {
      copy.textContent = "Copy failed";
    }
    setTimeout(() => (copy.textContent = "Copy"), 1500);
  });

  const bar = element("div", { class: "primer-bar" }, element("code", {}, primer.dataset.filename || ""), copy);
  const playground = PLAYGROUNDS[primer.dataset.primer];
  if (playground) {
    bar.append(element("a", { class: "primer-button", href: playground.url(source), target: "_blank", rel: "noopener" }, `${playground.label} ↗`));
  }
  code.parentElement.before(bar);

  if (LANGUAGES[extension]) highlightCode(code, LANGUAGES[extension]).catch(() => {});
}

// ------------------------------------------------------------------ start

// kramdown keeps the invisible variation selector of an emoji such as ✏️ in
// a heading's id, while GitHub drops it, so the README's own links to that
// heading miss. Drop it here too, and scroll again if the link was followed.
function fixHeadingIds(root) {
  let fixed = false;
  for (const heading of root.querySelectorAll("h1[id], h2[id], h3[id], h4[id]")) {
    if (!heading.id.includes("️")) continue;
    heading.id = heading.id.replace(/️/g, "");
    fixed = true;
  }
  const target = fixed && location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (target) target.scrollIntoView();
}

if (main) {
  fixHeadingIds(main);
  makeTablesSortable(main);
  const contents = main.querySelector("h2#contents");
  if (contents) setUpHome(main, contents);
  const primer = main.querySelector(".primer");
  if (primer) setUpPrimer(primer);
}
