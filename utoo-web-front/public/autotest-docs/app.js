(() => {
  const navEl = document.getElementById("nav");
  const contentEl = document.getElementById("content");
  const crumbEl = document.getElementById("crumb");
  const searchEl = document.getElementById("nav-search");
  const btnSidebar = document.getElementById("btn-sidebar");
  const btnPdf = document.getElementById("btn-pdf");
  let navData = null;
  let flat = [];
  let currentItem = null;

  function qs() {
    return (location.hash || "#home").replace(/^#/, "").split("&")[0] || "home";
  }

  function findItem(id) {
    return flat.find((x) => x.id === id) || flat[0];
  }

  function walkPages(nodes, out) {
    for (const n of nodes || []) {
      if (n.file) out.push(n);
      if (n.children) walkPages(n.children, out);
    }
  }

  function renderNav(filter = "") {
    const q = (filter || "").trim().toLowerCase();
    navEl.innerHTML = "";

    function matchLabel(label) {
      return !q || String(label || "").toLowerCase().includes(q);
    }

    function appendLeaf(parent, child) {
      if (!matchLabel(child.label) && !matchLabel(child.id)) return false;
      const a = document.createElement("a");
      a.href = `#${child.id}`;
      a.dataset.id = child.id;
      a.textContent = child.label;
      if (child.ready === false) a.classList.add("todo");
      parent.appendChild(a);
      return true;
    }

    function appendGroup(parent, sec, depth) {
      const hasKids = Array.isArray(sec.children) && sec.children.length;
      if (!hasKids) {
        if (sec.file) return appendLeaf(parent, sec);
        return false;
      }

      // Category / section with nested children
      const fold = document.createElement("details");
      fold.className = depth === 0 ? "nav-section" : "nav-cat";
      fold.open = true;
      const sum = document.createElement("summary");
      sum.textContent = sec.label;
      fold.appendChild(sum);
      const box = document.createElement("div");
      box.className = "nav-children";
      let any = false;
      for (const child of sec.children) {
        if (child.children && !child.file) {
          if (appendGroup(box, child, depth + 1)) any = true;
        } else if (appendLeaf(box, child)) {
          any = true;
        }
      }
      if (!any && q) return false;
      if (!any && !sec.file) {
        // empty group still show when not filtering
        if (q) return false;
      }
      fold.appendChild(box);
      parent.appendChild(fold);
      return true;
    }

    for (const sec of navData.sections) {
      if (sec.children) {
        appendGroup(navEl, sec, 0);
      } else if (matchLabel(sec.label)) {
        appendLeaf(navEl, sec);
      }
    }
    if (currentItem) markActive(currentItem.id);
  }

  function markActive(id) {
    navEl.querySelectorAll("a").forEach((a) => {
      a.classList.toggle("active", a.dataset.id === id);
    });
    // Expand ancestors of active link
    const active = navEl.querySelector(`a[data-id="${CSS.escape(id)}"]`);
    if (active) {
      let p = active.parentElement;
      while (p) {
        if (p.tagName === "DETAILS") p.open = true;
        p = p.parentElement;
      }
    }
  }

  function enhanceSteps() {
    const heads = [...contentEl.querySelectorAll("h2")];
    const overview = heads.find((h) => /步骤一览/.test(h.textContent || ""));
    const stepHeads = heads.filter((h) => /^[①②③④⑤⑥⑦⑧⑨⑩]/.test((h.textContent || "").trim()));
    stepHeads.forEach((h, i) => {
      if (!h.id) h.id = `doc-step-${i + 1}`;
      h.classList.add("step-anchor");
    });
    if (!overview || !stepHeads.length) return;
    let list = overview.nextElementSibling;
    while (list && list.tagName !== "OL" && list.tagName !== "UL") {
      list = list.nextElementSibling;
    }
    if (!list) return;
    [...list.children].forEach((li, i) => {
      if (!stepHeads[i] || li.querySelector("a.step-jump")) return;
      const text = li.textContent.trim();
      const a = document.createElement("a");
      a.href = `#${stepHeads[i].id}`;
      a.className = "step-jump";
      a.textContent = text;
      a.addEventListener("click", (e) => {
        e.preventDefault();
        stepHeads[i].scrollIntoView({ behavior: "smooth", block: "start" });
      });
      li.textContent = "";
      li.appendChild(a);
    });
  }

  function updatePdfButton(item) {
    const isTest = item && String(item.id || "").startsWith("test-");
    btnPdf.hidden = !isTest;
    if (isTest) btnPdf.textContent = `下载 PDF · ${item.label}`;
  }

  async function loadPage(item) {
    currentItem = item;
    markActive(item.id);
    crumbEl.textContent = item.label;
    updatePdfButton(item);
    contentEl.innerHTML = `<p class="muted">加载 ${item.label}…</p>`;
    try {
      const res = await fetch(`./${item.file}?t=${Date.now()}`);
      if (!res.ok) throw new Error(`${res.status} ${item.file}`);
      const html = await res.text();
      contentEl.innerHTML = html;
      contentEl.querySelectorAll("img").forEach((img) => {
        const src = img.getAttribute("src") || "";
        if (src && !src.startsWith("http") && !src.startsWith("./") && !src.startsWith("/")) {
          img.src = `./${src}`;
        }
      });
      enhanceSteps();
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch (err) {
      contentEl.innerHTML = `<div class="callout">页面加载失败：${String(err)}</div>`;
    }
  }

  function onHash() {
    const item = findItem(qs());
    loadPage(item);
  }

  btnSidebar.addEventListener("click", () => {
    document.body.classList.toggle("sidebar-collapsed");
  });

  function safeFileName(name) {
    return String(name || "试验")
      .replace(/[\\/:*?"<>|]+/g, "_")
      .replace(/\s+/g, "")
      .slice(0, 80);
  }

  async function waitImages(root) {
    const imgs = [...root.querySelectorAll("img")];
    await Promise.all(
      imgs.map(
        (img) =>
          img.complete
            ? Promise.resolve()
            : new Promise((resolve) => {
                img.addEventListener("load", resolve, { once: true });
                img.addEventListener("error", resolve, { once: true });
              })
      )
    );
  }

  btnPdf.addEventListener("click", async () => {
    if (typeof html2pdf !== "function") {
      alert("PDF 组件未加载，请刷新页面后重试。");
      return;
    }
    const title = (currentItem && currentItem.label) || "试验操作说明";
    const filename = `SolarAutoTest_${safeFileName(title)}.pdf`;
    const prev = btnPdf.textContent;
    btnPdf.disabled = true;
    btnPdf.textContent = "正在生成 PDF…";
    try {
      await waitImages(contentEl);
      await html2pdf()
        .set({
          margin: [10, 10, 12, 10],
          filename,
          image: { type: "jpeg", quality: 0.92 },
          html2canvas: { scale: 2, useCORS: true, logging: false },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
          pagebreak: { mode: ["css", "legacy"] },
        })
        .from(contentEl)
        .save();
    } catch (err) {
      alert(`生成 PDF 失败：${err}`);
    } finally {
      btnPdf.disabled = false;
      btnPdf.textContent = prev;
    }
  });

  searchEl.addEventListener("input", () => {
    renderNav(searchEl.value);
  });

  async function boot() {
    const res = await fetch("./nav.json");
    navData = await res.json();
    flat = [];
    walkPages(navData.sections, flat);
    renderNav();
    onHash();
    window.addEventListener("hashchange", onHash);
  }

  boot().catch((e) => {
    contentEl.innerHTML = `<div class="callout">无法加载目录：${e}</div>`;
  });
})();
