(function () {
  "use strict";

  const els = {
    sidebar: document.getElementById("sidebar"),
    welcomeGrid: document.getElementById("welcome-grid"),
    welcome: document.getElementById("welcome"),
    doc: document.getElementById("doc"),
    docTag: document.getElementById("doc-tag"),
    docTitle: document.getElementById("doc-title"),
    docRaw: document.getElementById("doc-raw"),
    docBody: document.getElementById("doc-body"),
    search: document.getElementById("search"),
    docCount: document.getElementById("doc-count"),
    syncDate: document.getElementById("sync-date"),
    statusLeft: document.getElementById("status-left"),
  };

  let manifest = { categories: [] };
  let flatDocs = []; // { path, title, tag, color, catLabel }

  init();

  async function init() {
    try {
      const res = await fetch("manifest.json", { cache: "no-store" });
      if (!res.ok) throw new Error("manifest.json responded with " + res.status);
      manifest = await res.json();
    } catch (err) {
      els.sidebar.innerHTML =
        '<div class="no-results">manifest.json not found or invalid.<br>Run scripts/generate-manifest.py, or check the file is deployed alongside index.html.</div>';
      els.statusLeft.textContent = "root@soc-kb:~$ error: manifest load failed";
      console.error(err);
      return;
    }

    flatDocs = [];
    manifest.categories.forEach((cat) => {
      (cat.docs || []).forEach((doc) => {
        flatDocs.push({ ...doc, catId: cat.id, catLabel: cat.label, tag: cat.tag, color: cat.color });
      });
    });

    els.docCount.textContent = flatDocs.length + (flatDocs.length === 1 ? " doc" : " docs");
    els.syncDate.textContent = manifest.generated || "—";

    buildSidebar();
    buildWelcomeGrid();
    wireSearch();
    wireHashRouting();

    // Load a doc directly if the URL already has a hash (deep link / refresh)
    if (location.hash.length > 1) {
      loadFromHash();
    }
  }

  function buildSidebar() {
    els.sidebar.innerHTML = "";
    manifest.categories.forEach((cat) => {
      const catEl = document.createElement("div");
      catEl.className = "cat";
      catEl.dataset.catId = cat.id;

      const head = document.createElement("button");
      head.className = "cat-head";
      head.innerHTML = `
        <span class="cat-tag" style="background:${cat.color}">${cat.tag}</span>
        <span class="cat-label">${escapeHtml(cat.label)}</span>
        <span class="cat-chevron">&#9656;</span>
      `;
      head.addEventListener("click", () => catEl.classList.toggle("open"));

      const docsWrap = document.createElement("div");
      docsWrap.className = "cat-docs";

      (cat.docs || []).forEach((doc) => {
        const link = document.createElement("button");
        link.className = "doc-link";
        link.textContent = doc.title;
        link.dataset.path = doc.path;
        link.addEventListener("click", () => {
          location.hash = encodeURIComponent(doc.path);
        });
        docsWrap.appendChild(link);
      });

      catEl.appendChild(head);
      catEl.appendChild(docsWrap);
      els.sidebar.appendChild(catEl);
    });
  }

  function buildWelcomeGrid() {
    els.welcomeGrid.innerHTML = "";
    manifest.categories.forEach((cat) => {
      const card = document.createElement("div");
      card.className = "cat-card";
      card.style.borderLeftColor = cat.color;
      card.innerHTML = `
        <div class="cat-card-tag" style="color:${cat.color}">${cat.tag}</div>
        <div class="cat-card-label">${escapeHtml(cat.label)}</div>
        <div class="cat-card-count">${(cat.docs || []).length} doc${(cat.docs || []).length === 1 ? "" : "s"}</div>
      `;
      card.addEventListener("click", () => {
        const catEl = els.sidebar.querySelector(`.cat[data-cat-id="${cssEscape(cat.id)}"]`);
        if (catEl) {
          catEl.classList.add("open");
          catEl.scrollIntoView({ block: "nearest" });
        }
        const first = (cat.docs || [])[0];
        if (first) location.hash = encodeURIComponent(first.path);
      });
      els.welcomeGrid.appendChild(card);
    });
  }

  function wireSearch() {
    els.search.addEventListener("input", () => {
      const q = els.search.value.trim().toLowerCase();
      let visibleCount = 0;

      els.sidebar.querySelectorAll(".cat").forEach((catEl) => {
        let anyVisible = false;
        catEl.querySelectorAll(".doc-link").forEach((link) => {
          const match = link.textContent.toLowerCase().includes(q);
          link.style.display = match ? "" : "none";
          if (match) { anyVisible = true; visibleCount++; }
        });
        catEl.style.display = anyVisible || q === "" ? "" : "none";
        if (q !== "" && anyVisible) catEl.classList.add("open");
      });

      const existingMsg = els.sidebar.querySelector(".no-results");
      if (existingMsg) existingMsg.remove();
      if (q !== "" && visibleCount === 0) {
        const msg = document.createElement("div");
        msg.className = "no-results";
        msg.textContent = `no matches for "${els.search.value.trim()}"`;
        els.sidebar.appendChild(msg);
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "/" && document.activeElement !== els.search) {
        e.preventDefault();
        els.search.focus();
      }
    });
  }

  function wireHashRouting() {
    window.addEventListener("hashchange", loadFromHash);
  }

  function loadFromHash() {
    const path = decodeURIComponent(location.hash.slice(1));
    const doc = flatDocs.find((d) => d.path === path);
    if (doc) openDoc(doc);
  }

  async function openDoc(doc) {
    els.sidebar.querySelectorAll(".doc-link").forEach((link) => {
      link.classList.toggle("active", link.dataset.path === doc.path);
    });

    els.welcome.hidden = true;
    els.doc.hidden = false;
    els.docTag.textContent = doc.tag;
    els.docTag.style.background = doc.color;
    els.docTitle.textContent = doc.title;
    els.docRaw.href = doc.path;
    els.docBody.className = "doc-body";
    els.docBody.textContent = "Loading " + doc.path + " ...";
    els.statusLeft.textContent = "root@soc-kb:~$ cat " + doc.path;

    try {
      const res = await fetch(doc.path, { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const raw = await res.text();

      if (doc.type === "md") {
        els.docBody.innerHTML = window.marked.parse(raw);
      } else {
        els.docBody.classList.add("plain");
        els.docBody.textContent = raw;
      }
      els.statusLeft.textContent = "root@soc-kb:~$ cat " + doc.path + " — done";
    } catch (err) {
      els.docBody.classList.add("plain");
      els.docBody.textContent = "Could not load " + doc.path + "\n\n" + err.message;
      els.statusLeft.textContent = "root@soc-kb:~$ error loading " + doc.path;
    }
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function cssEscape(str) {
    return String(str).replace(/"/g, '\\"');
  }
})();
