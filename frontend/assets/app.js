/* Flux-Capacitor - lógica da UI */
const API = "/api/v1";
const LS_KEY = "flux.apiKey";

const state = { presentation: null, currentSlideId: null, attachments: [] };

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function getApiKey() {
  let k = $("#apiKey").value || localStorage.getItem(LS_KEY);
  if (!k) {
    k = prompt("Informe sua API Key (X-API-Key). Padrão: change-me-flux-capacitor-key", "change-me-flux-capacitor-key");
    if (k) localStorage.setItem(LS_KEY, k);
  }
  $("#apiKey").value = k || "";
  return k || "";
}

function toast(msg, ms) {
  const el = $("#toast");
  el.textContent = msg;
  el.style.display = "block";
  el.classList.add("show");
  const duration = ms || Math.min(10000, 2600 + msg.length * 40);
  setTimeout(() => { el.classList.remove("show"); el.style.display = "none"; }, duration);
}

function formatApiError(body, status) {
  if (!body) return `HTTP ${status}`;
  const d = body.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    return d.map((e) => {
      const loc = Array.isArray(e.loc) ? e.loc.slice(1).join(".") : "";
      return `${loc ? loc + ": " : ""}${e.msg || JSON.stringify(e)}`;
    }).join(" · ");
  }
  if (d && typeof d === "object") return JSON.stringify(d);
  return `HTTP ${status}`;
}

async function api(path, opts = {}) {
  const key = getApiKey();
  const res = await fetch(API + path, {
    ...opts,
    headers: { "Content-Type": "application/json", "X-API-Key": key, ...(opts.headers || {}) },
  });
  if (!res.ok) {
    let body = null;
    try { body = await res.json(); } catch {}
    throw new Error(formatApiError(body, res.status));
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

async function apiRaw(path) {
  const key = getApiKey();
  const res = await fetch(API + path, { headers: { "X-API-Key": key } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res;
}

function goStep(n) {
  $$(".step-panel").forEach((p) => p.classList.add("hidden"));
  $(`#step-${n}`).classList.remove("hidden");
  const stepperWrap = $("#stepper-wrap");
  if (n === 0) {
    stepperWrap.classList.add("hidden");
    loadDashboard();
  } else {
    if (n === 1) renderAttachments();
    stepperWrap.classList.remove("hidden");
    $$("#stepper .step").forEach((s) => {
      const i = parseInt(s.dataset.step, 10);
      s.classList.toggle("active", i === n);
      s.classList.toggle("done", i < n);
    });
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---------- dashboard ----------
async function loadDashboard() {
  try {
    const items = await api("/presentations");
    const grid = $("#dashboard-grid");
    const empty = $("#dashboard-empty");
    grid.innerHTML = "";
    if (!items.length) {
      empty.classList.remove("hidden");
      grid.classList.add("hidden");
      return;
    }
    empty.classList.add("hidden");
    grid.classList.remove("hidden");
    items.forEach((p) => grid.appendChild(dashCard(p)));
    lucide.createIcons();
  } catch (e) {
    toast("Erro ao carregar: " + e.message);
  }
}

function dashCard(p) {
  const card = document.createElement("div");
  card.className = "bg-white rounded-3xl shadow-soft border border-flux-100 p-5 flex flex-col gap-3 hover:shadow-lg transition";
  const updated = new Date(p.updated_at).toLocaleString("pt-BR");
  const badge = p.status === "draft"
    ? '<span class="text-xs px-2 py-0.5 rounded-full bg-flux-100 text-flux-600 font-medium">rascunho</span>'
    : '<span class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">finalizada</span>';
  card.innerHTML = `
    <div class="flex items-start justify-between gap-2">
      <h3 class="font-display font-bold text-lg leading-tight line-clamp-2">${escapeHtml(p.title)}</h3>
      ${badge}
    </div>
    <p class="text-sm text-flux-soft line-clamp-2">${escapeHtml(p.topic || "")}</p>
    <p class="text-xs text-flux-soft mt-auto">Atualizada em ${updated}</p>
    <div class="flex flex-wrap gap-2 pt-2 border-t border-flux-100">
      <button class="btn-secondary text-xs" data-act="open"><i data-lucide="edit-3" class="w-3.5 h-3.5"></i> Abrir</button>
      <button class="btn-secondary text-xs" data-act="html"><i data-lucide="external-link" class="w-3.5 h-3.5"></i> HTML</button>
      <button class="btn-secondary text-xs" data-act="download"><i data-lucide="download" class="w-3.5 h-3.5"></i> .html</button>
      <button class="btn-secondary text-xs" data-act="md"><i data-lucide="file-text" class="w-3.5 h-3.5"></i> .md</button>
      <button class="icon-btn text-flux-600 ml-auto" data-act="delete" title="Excluir"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
    </div>
  `;
  card.querySelector('[data-act="open"]').addEventListener("click", () => openPresentation(p.id));
  card.querySelector('[data-act="html"]').addEventListener("click", () => openHtmlInNewTab(p.id));
  card.querySelector('[data-act="download"]').addEventListener("click", () => downloadHtml(p.id, p.title));
  card.querySelector('[data-act="md"]').addEventListener("click", () => downloadMd(p.id, p.title));
  card.querySelector('[data-act="delete"]').addEventListener("click", () => deletePresentation(p.id));
  return card;
}

async function openPresentation(id) {
  try {
    state.presentation = await api(`/presentations/${id}`);
    state.currentSlideId = null;
    renderEditor();
    goStep(3);
  } catch (e) {
    toast("Erro: " + e.message);
  }
}

async function openHtmlInNewTab(id) {
  const key = encodeURIComponent(getApiKey());
  // abre num blob para não precisar mandar header em nova aba
  try {
    const res = await apiRaw(`/presentations/${id}/export/html`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) {
    toast("Erro: " + e.message);
  }
}

async function downloadHtml(id, title) {
  try {
    const res = await apiRaw(`/presentations/${id}/export/html`);
    const blob = await res.blob();
    triggerDownload(blob, slugify(title || "flux-capacitor") + ".html");
  } catch (e) { toast("Erro: " + e.message); }
}

async function downloadMd(id, title) {
  try {
    const res = await apiRaw(`/presentations/${id}/markdown`);
    const blob = await res.blob();
    triggerDownload(blob, slugify(title || "flux-capacitor") + ".md");
  } catch (e) { toast("Erro: " + e.message); }
}

async function deletePresentation(id) {
  if (!confirm("Excluir esta apresentação permanentemente?")) return;
  try {
    await api(`/presentations/${id}`, { method: "DELETE" });
    toast("Apresentação excluída");
    loadDashboard();
  } catch (e) { toast("Erro: " + e.message); }
}

// ---------- passo 1: uploads ----------
function renderAttachments() {
  const ul = $("#attachments-list");
  ul.innerHTML = "";
  if (!state.attachments.length) {
    ul.innerHTML = '<li class="text-xs text-flux-soft italic">Nenhum arquivo anexado.</li>';
    return;
  }
  state.attachments.forEach((a) => {
    const li = document.createElement("li");
    li.className = "flex items-center gap-3 p-3 rounded-xl border border-flux-200 bg-flux-50";
    const icon = a.kind === "image" ? "image" : "file-text";
    const kb = (a.size_bytes / 1024).toFixed(1);
    li.innerHTML = `
      <i data-lucide="${icon}" class="w-4 h-4 text-flux-500"></i>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-semibold truncate">${escapeHtml(a.filename)}</div>
        <div class="text-xs text-flux-soft">${a.mime_type} · ${kb} KB ${a.has_text ? "· texto extraído" : ""}</div>
      </div>
      <button class="icon-btn" data-id="${a.id}" title="Remover"><i data-lucide="x" class="w-4 h-4"></i></button>`;
    li.querySelector("button").addEventListener("click", () => removeAttachment(a.id));
    ul.appendChild(li);
  });
  lucide.createIcons();
}

async function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(API + "/uploads", {
    method: "POST",
    headers: { "X-API-Key": getApiKey() },
    body: fd,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function removeAttachment(id) {
  try {
    await fetch(API + "/uploads/" + id, {
      method: "DELETE",
      headers: { "X-API-Key": getApiKey() },
    });
  } catch {}
  state.attachments = state.attachments.filter((a) => a.id !== id);
  renderAttachments();
}

$("#f-files").addEventListener("change", async (e) => {
  const files = Array.from(e.target.files || []);
  e.target.value = "";
  for (const f of files) {
    try {
      const att = await uploadFile(f);
      state.attachments.push(att);
      renderAttachments();
    } catch (err) {
      toast(`Erro em ${f.name}: ${err.message}`);
    }
  }
});

// ---------- passo 1: gerar ----------
$("#btn-generate").addEventListener("click", async () => {
  const topic = $("#f-topic").value.trim();
  if (!topic) return toast("Preencha o tópico");
  goStep(2);
  try {
    const p = await api("/presentations", {
      method: "POST",
      body: JSON.stringify({
        topic,
        audience: $("#f-audience").value || null,
        tone: $("#f-tone").value,
        language: $("#f-language").value,
        num_slides: parseInt($("#f-num").value, 10) || 8,
        theme: "modern-soft",
        attachment_ids: state.attachments.map((a) => a.id),
      }),
    });
    state.presentation = p;
    state.currentSlideId = null;
    state.attachments = [];  // limpa para próximo deck
    renderAttachments();
    renderEditor();
    goStep(3);
  } catch (e) {
    toast("Erro: " + e.message);
    goStep(1);
  }
});

// ---------- passo 3: editor ----------
function renderEditor() {
  const p = state.presentation;
  $("#slide-count").textContent = p.slides.length;
  const ul = $("#slides-list");
  ul.innerHTML = "";
  p.slides.forEach((s, i) => {
    const li = document.createElement("li");
    li.className = "slide-item" + (s.id === state.currentSlideId ? " active" : "");
    li.innerHTML = `
      <span class="num">${String(i + 1).padStart(2, "0")}</span>
      <span class="t flex-1">${escapeHtml(s.title || "(sem título)")}</span>
      <span class="slide-move">
        <button data-act="up" title="Mover para cima" ${i === 0 ? "disabled" : ""}>▲</button>
        <button data-act="down" title="Mover para baixo" ${i === p.slides.length - 1 ? "disabled" : ""}>▼</button>
      </span>
    `;
    li.addEventListener("click", (e) => {
      const act = e.target.closest("[data-act]")?.dataset.act;
      if (act === "up") return moveSlide(s.id, -1);
      if (act === "down") return moveSlide(s.id, +1);
      selectSlide(s.id);
    });
    ul.appendChild(li);
  });
  if (!state.currentSlideId && p.slides.length) selectSlide(p.slides[0].id);
  lucide.createIcons();
}

function selectSlide(id) {
  state.currentSlideId = id;
  const s = state.presentation.slides.find((x) => x.id === id);
  if (!s) return;
  $("#ed-index").textContent = (s.order_index + 1);
  $("#ed-type").textContent = s.visual_type || "prose";
  $("#ed-title-preview").textContent = s.title || "—";
  $("#ed-title").value = s.title || "";
  $("#ed-content").value = s.content_md || "";
  $("#ed-icon").value = s.icon || "";
  $("#ed-image").value = s.image_keyword || "";
  $("#ed-transition").value = s.transition || "fade";
  $("#ed-notes").value = s.notes || "";
  $$(".slide-item").forEach((el) => el.classList.remove("active"));
  const idx = state.presentation.slides.findIndex((x) => x.id === id);
  const node = $$(".slide-item")[idx];
  if (node) node.classList.add("active");
  $("#refine-box").classList.add("hidden");
}

$("#btn-save-slide").addEventListener("click", async () => {
  const id = state.currentSlideId;
  if (!id) return;
  try {
    const updated = await api(`/slides/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        title: $("#ed-title").value,
        content_md: $("#ed-content").value,
        icon: $("#ed-icon").value || null,
        image_keyword: $("#ed-image").value || null,
        transition: $("#ed-transition").value,
        notes: $("#ed-notes").value || null,
      }),
    });
    const idx = state.presentation.slides.findIndex((x) => x.id === id);
    state.presentation.slides[idx] = { ...state.presentation.slides[idx], ...updated };
    renderEditor();
    toast("Slide salvo");
  } catch (e) { toast("Erro: " + e.message); }
});

$("#btn-delete-slide").addEventListener("click", async () => {
  const id = state.currentSlideId;
  if (!id || !confirm("Excluir este slide?")) return;
  try {
    await api(`/slides/${id}`, { method: "DELETE" });
    state.presentation.slides = state.presentation.slides.filter((x) => x.id !== id);
    state.currentSlideId = state.presentation.slides[0]?.id || null;
    renderEditor();
    toast("Slide excluído");
  } catch (e) { toast("Erro: " + e.message); }
});

$("#btn-refine").addEventListener("click", () => {
  $("#refine-box").classList.toggle("hidden");
  $("#refine-instruction").focus();
});
$("#btn-refine-cancel").addEventListener("click", () => $("#refine-box").classList.add("hidden"));

$("#btn-refine-apply").addEventListener("click", async () => {
  const id = state.currentSlideId;
  const instruction = $("#refine-instruction").value.trim();
  if (!id || !instruction) return toast("Descreva o ajuste");
  try {
    $("#btn-refine-apply").disabled = true;
    const updated = await api(`/slides/${id}/refine`, {
      method: "POST",
      body: JSON.stringify({ instruction }),
    });
    const idx = state.presentation.slides.findIndex((x) => x.id === id);
    state.presentation.slides[idx] = { ...state.presentation.slides[idx], ...updated };
    renderEditor();
    selectSlide(id);
    $("#refine-instruction").value = "";
    $("#refine-box").classList.add("hidden");
    toast("Slide refinado pela IA");
  } catch (e) { toast("Erro: " + e.message); }
  finally { $("#btn-refine-apply").disabled = false; }
});

$("#btn-goto-preview").addEventListener("click", async () => {
  try {
    state.presentation = await api(`/presentations/${state.presentation.id}`);
    await renderPreview();
    goStep(4);
  } catch (e) { toast("Erro: " + e.message); }
});

// adicionar / duplicar / mover slide
$("#btn-add-slide").addEventListener("click", async () => {
  try {
    const body = { after_slide_id: state.currentSlideId || null, title: "Novo slide", content_md: "Escreva aqui...", icon: "sparkles", visual_type: "prose" };
    const created = await api(`/presentations/${state.presentation.id}/slides`, { method: "POST", body: JSON.stringify(body) });
    state.presentation = await api(`/presentations/${state.presentation.id}`);
    state.currentSlideId = created.id;
    renderEditor();
    toast("Slide adicionado");
  } catch (e) { toast("Erro: " + e.message); }
});

$("#btn-dup-slide").addEventListener("click", async () => {
  if (!state.currentSlideId) return toast("Selecione um slide");
  try {
    const created = await api(`/presentations/${state.presentation.id}/slides/${state.currentSlideId}/duplicate`, { method: "POST" });
    state.presentation = await api(`/presentations/${state.presentation.id}`);
    state.currentSlideId = created.id;
    renderEditor();
    toast("Slide duplicado");
  } catch (e) { toast("Erro: " + e.message); }
});

async function moveSlide(id, delta) {
  const slides = state.presentation.slides;
  const idx = slides.findIndex((x) => x.id === id);
  const target = idx + delta;
  if (target < 0 || target >= slides.length) return;
  const reordered = [...slides];
  [reordered[idx], reordered[target]] = [reordered[target], reordered[idx]];
  try {
    const updated = await api(`/presentations/${state.presentation.id}/reorder`, {
      method: "POST",
      body: JSON.stringify({ ordered_ids: reordered.map((s) => s.id) }),
    });
    state.presentation.slides = updated;
    renderEditor();
  } catch (e) { toast("Erro: " + e.message); }
}

// ---------- passo 4: preview ----------
async function renderPreview() {
  const p = state.presentation;
  $("#md-output").textContent = p.markdown || "";
  try {
    const res = await apiRaw(`/presentations/${p.id}/export/html`);
    const blob = await res.blob();
    state.previewBlob = blob;
    if (state.previewBlobUrl) URL.revokeObjectURL(state.previewBlobUrl);
    state.previewBlobUrl = URL.createObjectURL(blob);
    $("#preview-frame").src = state.previewBlobUrl;
  } catch (e) { toast("Erro no preview: " + e.message); }
}

$("#btn-copy-md").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("#md-output").textContent);
  toast("Markdown copiado");
});
$("#btn-download-md").addEventListener("click", () => {
  const blob = new Blob([$("#md-output").textContent], { type: "text/markdown" });
  triggerDownload(blob, slugify(state.presentation.title || "flux-capacitor") + ".md");
});
$("#btn-download-html").addEventListener("click", async () => {
  const title = state.presentation?.title || "flux-capacitor";
  if (state.previewBlob) {
    triggerDownload(state.previewBlob, slugify(title) + ".html");
  } else {
    await downloadHtml(state.presentation.id, title);
  }
});
$("#btn-open-html").addEventListener("click", () => openHtmlInNewTab(state.presentation.id));
$("#btn-back-edit").addEventListener("click", () => goStep(3));
$("#btn-new").addEventListener("click", () => {
  state.presentation = null;
  state.currentSlideId = null;
  state.attachments = [];
  $("#f-topic").value = "";
  renderAttachments();
  goStep(1);
});

// ---------- System Prompts modal ----------
const promptsState = { items: [], current: null };

async function openPromptsModal() {
  $("#prompts-modal").classList.remove("hidden");
  try {
    promptsState.items = await api("/prompts");
    renderPromptsList();
  } catch (e) { toast("Erro: " + e.message); }
}

function closePromptsModal() {
  $("#prompts-modal").classList.add("hidden");
  promptsState.current = null;
  $("#prompt-editor").classList.add("hidden");
  $("#prompt-placeholder").classList.remove("hidden");
}
window.closePromptsModal = closePromptsModal;

function renderPromptsList() {
  const ul = $("#prompts-list");
  ul.innerHTML = "";
  promptsState.items.forEach((p) => {
    const li = document.createElement("li");
    li.className = "prompt-item" + (p.key === promptsState.current?.key ? " active" : "");
    const dot = p.is_default ? '<span class="dot-default" title="Padrão"></span>' : '<span class="dot-edited" title="Editado"></span>';
    li.innerHTML = `${dot}<div class="flex-1 min-w-0"><div class="font-semibold text-sm truncate">${escapeHtml(p.label)}</div><div class="text-xs text-flux-soft font-mono truncate">${p.key}</div></div>`;
    li.addEventListener("click", () => selectPrompt(p.key));
    ul.appendChild(li);
  });
  lucide.createIcons();
}

function selectPrompt(key) {
  const p = promptsState.items.find((x) => x.key === key);
  if (!p) return;
  promptsState.current = p;
  $("#prompt-placeholder").classList.add("hidden");
  $("#prompt-editor").classList.remove("hidden");
  $("#pe-label").textContent = p.label;
  $("#pe-desc").textContent = p.description;
  $("#pe-vars").textContent = p.variables.length ? "Variáveis: " + p.variables.map((v) => "{" + v + "}").join(" · ") : "Sem variáveis";
  $("#pe-content").value = p.content;
  $("#pe-status").textContent = p.is_default ? "Usando padrão" : "Personalizado · atualizado " + new Date(p.updated_at).toLocaleString("pt-BR");
  renderPromptsList();
}

$("#btn-open-prompts").addEventListener("click", openPromptsModal);
$("#pe-save").addEventListener("click", async () => {
  const p = promptsState.current;
  if (!p) return;
  try {
    await api(`/prompts/${p.key}`, { method: "PATCH", body: JSON.stringify({ content: $("#pe-content").value }) });
    promptsState.items = await api("/prompts");
    selectPrompt(p.key);
    toast("Prompt salvo");
  } catch (e) { toast("Erro: " + e.message); }
});
$("#pe-reset").addEventListener("click", async () => {
  const p = promptsState.current;
  if (!p || !confirm("Restaurar este prompt ao padrão do sistema?")) return;
  try {
    await api(`/prompts/${p.key}/reset`, { method: "POST" });
    promptsState.items = await api("/prompts");
    selectPrompt(p.key);
    toast("Prompt restaurado");
  } catch (e) { toast("Erro: " + e.message); }
});

// ---------- util ----------
function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}
function slugify(s) { return (s || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "flux"; }
function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

// ---------- boot ----------
(function init() {
  const saved = localStorage.getItem(LS_KEY);
  if (saved) $("#apiKey").value = saved;
  $("#apiKey").addEventListener("change", (e) => localStorage.setItem(LS_KEY, e.target.value));
  goStep(0);
})();
