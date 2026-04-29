(() => {
  const SAMPLES = {
    memory: `int x = 0 ;\nint y = 4 ;\nx = 2 * y ;`,
    lexer: `int counter = 10;\nfloat ratio = 3.14;\nstring name = "compiler";\nwhile (counter > 0) {\n    counter = counter - 1;\n}`,
    "if-valid": `int x = 5;\nint y = 10;\nif (x == 5 && y > 0) {\n    x = x + 1;\n}`,
    "if-invalid": `int x = 0;\nif (x + 5) {\n    x = 1;\n}`,
    undeclared: `int x = 0;\ny = 1;`,
    full: `int a = 2 ;\nint b = 3 ;\nint c = 0 ;\nc = a * b + 1 ;\nif (c > 5 && a == 2) {\n    c = c - 1 ;\n}`,
  };

  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  const editor = CodeMirror.fromTextArea(document.getElementById("editor"), {
    mode: "text/x-csrc",
    theme: "dracula",
    lineNumbers: true,
    matchBrackets: true,
    autoCloseBrackets: true,
    indentUnit: 4,
    tabSize: 4,
    lineWrapping: true,
    extraKeys: {
      "Ctrl-Enter": runAnalysis,
      "Cmd-Enter": runAnalysis,
    },
  });
  editor.setValue(SAMPLES.memory);

  const $ = (id) => document.getElementById(id);
  const tabButtons = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll("[data-panel]");

  let lastResult = { tokens: [], errors: [], memory: [], counts: {} };
  let currentStep = 0;
  let errorMarks = [];
  let debounceTimer = null;

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  function switchTab(tab) {
    tabButtons.forEach((b) => b.classList.toggle("tab-active", b.dataset.tab === tab));
    panels.forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== tab));
  }

  $("run-btn").addEventListener("click", runAnalysis);
  $("clear-btn").addEventListener("click", () => {
    editor.setValue("");
    renderResult({ tokens: [], errors: [], memory: [], counts: {} });
  });

  $("snippet-select").addEventListener("change", (e) => {
    if (e.target.value && SAMPLES[e.target.value]) {
      editor.setValue(SAMPLES[e.target.value]);
      e.target.value = "";
      runAnalysis();
    }
  });

  editor.on("change", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runAnalysis, 400);
  });

  $("export-json").addEventListener("click", () => {
    download("tokens.json", JSON.stringify(lastResult, null, 2), "application/json");
  });
  $("export-csv").addEventListener("click", () => {
    const rows = [["#", "Token", "Type", "Line", "Col"]];
    lastResult.tokens.forEach((t, i) => rows.push([i + 1, t.value, t.type, t.line, t.col]));
    const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    download("tokens.csv", csv, "text/csv");
  });

  $("step-prev").addEventListener("click", () => setStep(currentStep - 1));
  $("step-next").addEventListener("click", () => setStep(currentStep + 1));
  $("step-slider").addEventListener("input", (e) => setStep(parseInt(e.target.value, 10)));

  async function runAnalysis() {
    const source = editor.getValue();
    setStatus("busy", "Running");
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ source }),
      });
      if (!res.ok) throw new Error("Server error");
      const data = await res.json();
      renderResult(data);
      setStatus(data.errors.length ? "error" : "ok", data.errors.length ? `${data.errors.length} error${data.errors.length > 1 ? "s" : ""}` : "Ready");
    } catch (err) {
      setStatus("error", "Network error");
    }
  }

  function setStatus(kind, label) {
    const pill = $("status-pill");
    pill.className = "status-pill" + (kind === "busy" ? " busy" : kind === "error" ? " error" : "");
    pill.textContent = label;
  }

  function renderResult(data) {
    lastResult = data;
    renderTokens(data);
    renderErrors(data);
    renderMemory(data);
    updateBadges(data);
    paintEditorErrors(data.errors || []);
  }

  function updateBadges(data) {
    $("tab-count-tokens").textContent = (data.tokens || []).length;
    $("tab-count-errors").textContent = (data.errors || []).length;
    $("tab-count-memory").textContent = (data.memory || []).length;
  }

  function renderTokens(data) {
    const tbody = $("token-tbody");
    const tokens = data.tokens || [];
    tbody.innerHTML = "";
    $("tokens-empty").style.display = tokens.length ? "none" : "flex";

    tokens.forEach((t, i) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="idx">${i + 1}</td>
        <td class="tok">${escape(t.value)}</td>
        <td><span class="type-pill t-${t.type}">${t.type}</span></td>
        <td class="pos">${t.line}</td>
        <td class="pos">${t.col}</td>`;
      tbody.appendChild(tr);
    });

    const legend = $("token-legend");
    legend.innerHTML = "";
    const counts = data.counts || {};
    Object.entries(counts).sort((a, b) => b[1] - a[1]).forEach(([type, n]) => {
      const chip = document.createElement("span");
      chip.className = `legend-chip t-${type}`;
      chip.innerHTML = `<span class="swatch"></span>${type} <strong>${n}</strong>`;
      legend.appendChild(chip);
    });
  }

  function renderErrors(data) {
    const list = $("errors-list");
    const errs = data.errors || [];
    list.innerHTML = "";
    $("errors-empty").style.display = errs.length ? "none" : "flex";

    errs.forEach((e) => {
      const card = document.createElement("div");
      card.className = "error-card";
      card.innerHTML = `
        <svg class="error-icon w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div>
          <div class="error-msg">${escape(e.message)}</div>
          <div class="error-loc">line ${e.line}, col ${e.col}</div>
        </div>`;
      card.addEventListener("click", () => {
        editor.focus();
        editor.setCursor({ line: Math.max(0, e.line - 1), ch: Math.max(0, e.col - 1) });
      });
      list.appendChild(card);
    });
  }

  function renderMemory(data) {
    const trace = data.memory || [];
    const ctrls = $("memory-controls");
    const empty = $("memory-empty");

    if (!trace.length) {
      ctrls.classList.add("hidden");
      empty.style.display = "flex";
      $("mem-vars").innerHTML = "";
      $("mem-trace").innerHTML = "";
      return;
    }
    ctrls.classList.remove("hidden");
    empty.style.display = "none";

    const slider = $("step-slider");
    slider.max = trace.length - 1;
    if (currentStep > trace.length - 1) currentStep = trace.length - 1;
    slider.value = currentStep;

    const list = $("mem-trace");
    list.innerHTML = "";
    trace.forEach((step, i) => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="trace-line">L${step.line}</span><span style="color:#34d399;font-weight:700">${escape(step.var)}</span> <span style="color:var(--slate-500)">=</span> ${escape(step.expression)} <span class="trace-arrow">→</span><span class="trace-val">${escape(formatValue(step.value))}</span>`;
      li.addEventListener("click", () => setStep(i));
      list.appendChild(li);
    });

    setStep(currentStep);
  }

  function setStep(i) {
    const trace = lastResult.memory || [];
    if (!trace.length) return;
    currentStep = Math.max(0, Math.min(trace.length - 1, i));
    const slider = $("step-slider");
    slider.value = currentStep;
    const pct = trace.length > 1 ? (currentStep / (trace.length - 1)) * 100 : 100;
    slider.style.setProperty("--fill", pct + "%");
    $("step-label").textContent = `Step ${currentStep + 1} / ${trace.length}`;

    const step = trace[currentStep];
    const prev = currentStep > 0 ? trace[currentStep - 1].all_vars : {};
    const vars = step.all_vars || {};
    const varsBox = $("mem-vars");
    varsBox.innerHTML = "";
    Object.entries(vars).forEach(([name, value]) => {
      const row = document.createElement("div");
      const changed = prev[name] !== value;
      row.className = "mem-var-row" + (changed ? " changed" : "");
      row.innerHTML = `
        <div>
          <span class="mem-var-name">${escape(name)}</span><span class="mem-var-eq">=</span><span class="mem-var-value">${escape(formatValue(value))}</span>
        </div>
        <span class="mem-var-line">L${step.line}</span>`;
      varsBox.appendChild(row);
    });

    document.querySelectorAll("#mem-trace li").forEach((li, idx) => {
      li.classList.toggle("active", idx === currentStep);
    });
    const activeLi = document.querySelector("#mem-trace li.active");
    if (activeLi) activeLi.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function paintEditorErrors(errors) {
    errorMarks.forEach((m) => m.clear());
    errorMarks = [];
    errors.forEach((e) => {
      const line = Math.max(0, e.line - 1);
      const ch = Math.max(0, e.col - 1);
      const mark = editor.markText(
        { line, ch },
        { line, ch: ch + 1 },
        { className: "cm-error-marker", title: e.message }
      );
      errorMarks.push(mark);
    });
  }

  function formatValue(v) {
    if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(4).replace(/\.?0+$/, "");
    if (typeof v === "string") return `"${v}"`;
    if (typeof v === "boolean") return v ? "true" : "false";
    return String(v);
  }

  function escape(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function download(name, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  }

  runAnalysis();
})();
