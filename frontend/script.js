/**
 * API 根地址（不要末尾 /）。
 * 优先级：index.html 里 <meta name="api-base" content="https://你的后端">；
 * 未配置时：本地 8000 同源留空；127.0.0.1 其它端口指向本地后端；其余视为与页面同源（仅后端托管时）。
 */
function resolveApiBaseUrl() {
  const meta = document.querySelector('meta[name="api-base"]');
  const fromMeta = meta?.getAttribute("content")?.trim();
  if (fromMeta) return fromMeta.replace(/\/$/, "");
  const { hostname, port } = window.location;
  if (hostname === "127.0.0.1" || hostname === "localhost") {
    // 仅「静态页单独起在 5500」时指向本机后端；Docker 9000 / uvicorn 8000 等与 API 同源
    if (port === "5500") return "http://127.0.0.1:8000";
    return "";
  }
  return "";
}

const API_BASE_URL = resolveApiBaseUrl();

const analyzeBtn = document.getElementById("analyzeBtn");
const copyJsonBtn = document.getElementById("copyJsonBtn");
const statusEl = document.getElementById("status");
const rawJsonEl = document.getElementById("rawJson");
const summaryPanel = document.getElementById("summaryPanel");
const resultsSection = document.getElementById("resultsSection");
const resumeFileInput = document.getElementById("resumeFile");
const fileNameEl = document.getElementById("fileName");

function pct01(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(100, n <= 1 ? n * 100 : n));
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function parseApiError(data) {
  const d = data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    return d
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) return item.msg;
        try {
          return JSON.stringify(item);
        } catch {
          return "校验错误";
        }
      })
      .join("；");
  }
  if (d && typeof d === "object") return JSON.stringify(d);
  return "请求失败";
}

function setStatus(text, variant = "muted") {
  if (!statusEl) return;
  statusEl.textContent = text;
  statusEl.className = `status status--${variant}`;
}

function setLoading(isLoading) {
  if (!analyzeBtn) return;
  analyzeBtn.disabled = isLoading;
  analyzeBtn.classList.toggle("is-loading", isLoading);
  const label = analyzeBtn.querySelector(".btn__label");
  if (label) {
    label.textContent = isLoading ? "分析中…" : "上传并分析";
  }
}

function tag(text, kind) {
  const cls =
    kind === "jd" ? "tag tag--jd" : kind === "cv" ? "tag tag--cv" : kind === "hit" ? "tag tag--hit" : "tag tag--placeholder";
  return `<span class="${cls}">${escapeHtml(text)}</span>`;
}

function renderChips(items, kind) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) return tag("暂无", "neutral");
  return list.map((k) => tag(String(k), kind)).join("");
}

function renderSummary(data) {
  if (!summaryPanel || !resultsSection) return;
  const parse = data.parse || {};
  const match = data.match || {};
  const ai = parse.ai_result || {};
  const basic = ai.basic_info || {};
  const jobInfo = ai.job_info || {};
  const bg = ai.background_info || {};

  const scoreOverall = pct01(match.overall_score);
  const skill = pct01(match.skill_match_rate);
  const exp = pct01(match.experience_relevance);
  const edu = pct01(match.education_relevance);

  summaryPanel.innerHTML = `
    <div class="metric-board">
      <h3 class="metric-board__title">匹配概览</h3>
      <div class="metric-board__grid">
        <article class="metric-card">
          <div class="metric-card__label">综合匹配</div>
          <div class="metric-card__value">${escapeHtml(String(match.overall_score ?? "—"))}</div>
          <div class="metric-card__bar"><span class="metric-card__bar-fill" style="width:${scoreOverall}%"></span></div>
        </article>
        <article class="metric-card">
          <div class="metric-card__label">技能匹配</div>
          <div class="metric-card__value">${escapeHtml(String(match.skill_match_rate ?? "—"))}</div>
          <div class="metric-card__bar"><span class="metric-card__bar-fill" style="width:${skill}%"></span></div>
        </article>
        <article class="metric-card">
          <div class="metric-card__label">经验相关</div>
          <div class="metric-card__value">${escapeHtml(String(match.experience_relevance ?? "—"))}</div>
          <div class="metric-card__bar"><span class="metric-card__bar-fill" style="width:${exp}%"></span></div>
        </article>
        <article class="metric-card">
          <div class="metric-card__label">学历相关</div>
          <div class="metric-card__value">${escapeHtml(String(match.education_relevance ?? "—"))}</div>
          <div class="metric-card__bar"><span class="metric-card__bar-fill" style="width:${edu}%"></span></div>
        </article>
      </div>
    </div>

    <div class="summary-card">
      <div class="summary-card__title">匹配摘要</div>
      <p class="summary-card__text">${escapeHtml(match.summary || "暂无摘要")}</p>
    </div>

    <div class="results-row">
      <section class="subpanel" aria-labelledby="info-heading">
        <h3 id="info-heading" class="subpanel__title">关键信息</h3>
        <div class="info-grid">
          ${[
            ["姓名", basic.name],
            ["电话", basic.phone],
            ["邮箱", basic.email],
            ["地址", basic.address],
            ["求职意向", jobInfo.job_intention],
            ["期望薪资", jobInfo.expected_salary],
            ["年限", bg.years_of_experience],
          ]
            .map(
              ([label, val]) => `
            <div class="info-item">
              <span class="info-item__label">${escapeHtml(label)}</span>
              <span class="info-item__value">${escapeHtml(val != null && String(val).trim() !== "" ? String(val) : "—")}</span>
            </div>`
            )
            .join("")}
        </div>
      </section>

      <section class="subpanel" aria-labelledby="kw-heading">
        <h3 id="kw-heading" class="subpanel__title">关键词分析</h3>
        <div class="kw-block">
          <h4 class="kw-block__heading">JD 关键词</h4>
          <div class="chips">${renderChips(match.jd_keywords, "jd")}</div>
        </div>
        <div class="kw-block">
          <h4 class="kw-block__heading">简历关键词</h4>
          <div class="chips">${renderChips(match.resume_keywords, "cv")}</div>
        </div>
        <div class="kw-block">
          <h4 class="kw-block__heading">交集</h4>
          <div class="chips">${renderChips(match.keyword_overlap, "hit")}</div>
        </div>
      </section>
    </div>
  `;

  resultsSection.hidden = false;
  requestAnimationFrame(() => {
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function updateFileNameDisplay() {
  if (!fileNameEl || !resumeFileInput) return;
  const f = resumeFileInput.files?.[0];
  fileNameEl.textContent = f ? f.name : "";
}

function bindFileUi() {
  resumeFileInput?.addEventListener("change", updateFileNameDisplay);

  const fileDrop = document.querySelector(".file-field");
  if (fileDrop && resumeFileInput) {
    ["dragenter", "dragover"].forEach((ev) => {
      fileDrop.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileDrop.style.borderColor = "var(--accent)";
      });
    });
    ["dragleave", "drop"].forEach((ev) => {
      fileDrop.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileDrop.style.borderColor = "";
      });
    });
    fileDrop.addEventListener("drop", (e) => {
      const dt = e.dataTransfer?.files;
      if (dt?.length) {
        const file = dt[0];
        if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          resumeFileInput.files = dataTransfer.files;
          updateFileNameDisplay();
        } else {
          setStatus("请上传 PDF 格式的简历文件", "bad");
        }
      }
    });
  }
}

analyzeBtn?.addEventListener("click", async () => {
  const apiBase = API_BASE_URL.replace(/\/$/, "");
  const fileInput = document.getElementById("resumeFile");
  const file = fileInput?.files?.[0];
  const jd = document.getElementById("jobDescription")?.value.trim() || "";

  if (!file) {
    setStatus("请先选择一份 PDF 简历", "bad");
    return;
  }
  if (jd.length < 20) {
    setStatus("岗位描述至少需要 20 个字符，请补充 JD 内容", "bad");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("job_description", jd);

  setLoading(true);
  setStatus("正在上传并分析，预计需要数十秒…", "warn");
  if (rawJsonEl) rawJsonEl.textContent = "请求处理中…";

  try {
    const resp = await fetch(`${apiBase}/api/v1/resume/analyze`, {
      method: "POST",
      body: formData,
    });
    let data;
    try {
      data = await resp.json();
    } catch {
      throw new Error("服务器返回了非 JSON 响应");
    }
    if (!resp.ok) throw new Error(parseApiError(data));
    if (rawJsonEl) rawJsonEl.textContent = JSON.stringify(data, null, 2);
    renderSummary(data);
    setStatus("分析完成，结果已更新", "ok");
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    setStatus(`无法完成分析：${msg}`, "bad");
    if (rawJsonEl) rawJsonEl.textContent = `出错：${msg}`;
  } finally {
    setLoading(false);
  }
});

copyJsonBtn?.addEventListener("click", async () => {
  if (!rawJsonEl) return;
  const text = rawJsonEl.textContent || "";
  if (!text.trim() || text.startsWith("等待") || text.startsWith("请求处理") || text.startsWith("出错")) {
    setStatus("暂无可复制的 JSON，请先完成一次分析", "warn");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    copyJsonBtn.classList.add("is-done");
    const label = copyJsonBtn.querySelector(".btn__label");
    const prev = label?.textContent;
    if (label) label.textContent = "已复制";
    setStatus("JSON 已复制到剪贴板", "ok");
    window.setTimeout(() => {
      copyJsonBtn.classList.remove("is-done");
      if (label && prev) label.textContent = prev;
    }, 2200);
  } catch {
    setStatus("复制失败，请检查浏览器剪贴板权限", "bad");
  }
});

bindFileUi();
updateFileNameDisplay();
