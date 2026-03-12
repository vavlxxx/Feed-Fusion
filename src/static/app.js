const API_BASE = "/api/v1";
const PLACEHOLDER_IMAGE = "https://placehold.co/600x400";
const API_ENDPOINTS = {
  auth: "/auth/",
  channels: "/channels/",
  news: "/news/",
  subscriptions: "/subscriptions/",
  uploads: "/samples/",
  trainings: "/trainings/",
};
const ACCESS_TOKEN_KEY = "ff_access_token";
const NEWS_CATEGORIES = [
  { value: "Международные отношения", label: "Мир" },
  { value: "Культура", label: "Культура" },
  { value: "Наука и технологии", label: "Наука" },
  { value: "Общество", label: "Общество" },
  { value: "Экономика", label: "Экономика" },
  { value: "Происшествия", label: "Инциденты" },
  { value: "Спорт", label: "Спорт" },
  { value: "Здоровье", label: "Здоровье" },
];

const state = {
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  user: null,
  isAdmin: false,
  channels: [],
  channelMap: new Map(),
  subscriptions: [],
  subsByChannel: new Map(),
  newsCursor: null,
  hasNext: false,
  isLoading: false,
  uploads: [],
  trainings: [],
  selectedTrainingId: null,
  filters: {
    query: "",
    channelIds: [],
    categories: [],
    recentFirst: true,
    limit: 9,
  },
};

const dom = {
  views: document.querySelectorAll("[data-view]"),
  navLinks: document.querySelectorAll(".nav-link"),
  loginBtn: document.getElementById("loginBtn"),
  registerBtn: document.getElementById("registerBtn"),
  logoutBtn: document.getElementById("logoutBtn"),
  heroRefresh: document.getElementById("heroRefresh"),
  heroExplore: document.getElementById("heroExplore"),
  newsTotal: document.getElementById("newsTotal"),
  channelTotal: document.getElementById("channelTotal"),
  userState: document.getElementById("userState"),
  newsMeta: document.getElementById("newsMeta"),
  activeFilter: document.getElementById("activeFilter"),
  activeCategories: document.getElementById("activeCategories"),
  activeSort: document.getElementById("activeSort"),
  searchInput: document.getElementById("searchInput"),
  channelSelect: document.getElementById("channelSelect"),
  channelToggle: document.getElementById("channelToggle"),
  channelDropdown: document.getElementById("channelDropdown"),
  categorySelect: document.getElementById("categorySelect"),
  categoryToggle: document.getElementById("categoryToggle"),
  categoryDropdown: document.getElementById("categoryDropdown"),
  sortSelect: document.getElementById("sortSelect"),
  resetFilters: document.getElementById("resetFilters"),
  applyFilters: document.getElementById("applyFilters"),
  newsGrid: document.getElementById("newsGrid"),
  newsSentinel: document.getElementById("newsSentinel"),
  channelGrid: document.getElementById("channelGrid"),
  channelMeta: document.getElementById("channelMeta"),
  subsGrid: document.getElementById("subsGrid"),
  profileInfo: document.getElementById("profileInfo"),
  profileForm: document.getElementById("profileForm"),
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  channelCreateForm: document.getElementById("channelCreateForm"),
  adminChannelList: document.getElementById("adminChannelList"),
  sampleUploadForm: document.getElementById("sampleUploadForm"),
  sampleCsvFile: document.getElementById("sampleCsvFile"),
  refreshUploadsBtn: document.getElementById("refreshUploadsBtn"),
  uploadsList: document.getElementById("uploadsList"),
  sampleLabelForm: document.getElementById("sampleLabelForm"),
  sampleNewsId: document.getElementById("sampleNewsId"),
  sampleCategorySelect: document.getElementById("sampleCategorySelect"),
  trainModelForm: document.getElementById("trainModelForm"),
  refreshTrainingsBtn: document.getElementById("refreshTrainingsBtn"),
  trainingsList: document.getElementById("trainingsList"),
  adminStatChannels: document.getElementById("adminStatChannels"),
  adminStatUploads: document.getElementById("adminStatUploads"),
  adminStatTrainings: document.getElementById("adminStatTrainings"),
  adminStatActiveTrainings: document.getElementById("adminStatActiveTrainings"),
  adminStatBestAccuracy: document.getElementById("adminStatBestAccuracy"),
  uploadChart: document.getElementById("uploadChart"),
  uploadChartInfo: document.getElementById("uploadChartInfo"),
  trainingChart: document.getElementById("trainingChart"),
  trainingChartInfo: document.getElementById("trainingChartInfo"),
  trainingLossChart: document.getElementById("trainingLossChart"),
  trainingLossInfo: document.getElementById("trainingLossInfo"),
  trainingHistoryChart: document.getElementById("trainingHistoryChart"),
  trainingHistoryInfo: document.getElementById("trainingHistoryInfo"),
  trainingSnapshotTitle: document.getElementById("trainingSnapshotTitle"),
  trainingSnapshotState: document.getElementById("trainingSnapshotState"),
  trainingSnapshotMeta: document.getElementById("trainingSnapshotMeta"),
  trainingDetails: document.getElementById("trainingDetails"),
  trainingConfig: document.getElementById("trainingConfig"),
  trainingDetailsText: document.getElementById("trainingDetailsText"),
  toast: document.getElementById("toast"),
};

function showToast(message) {
  if (!dom.toast) return;
  dom.toast.textContent = message;
  dom.toast.hidden = false;
  clearTimeout(dom.toast._timer);
  dom.toast._timer = setTimeout(() => {
    dom.toast.hidden = true;
  }, 3200);
}

function setAccessToken(token) {
  if (token) {
    state.accessToken = token;
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    state.accessToken = null;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

async function apiFetch(path, options = {}) {
  const { skipAuth, retry, ...rest } = options;
  const headers = new Headers(rest.headers || {});
  if (!skipAuth && state.accessToken) {
    headers.set("Authorization", `Bearer ${state.accessToken}`);
  }
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...rest,
    headers,
  });

  if (response.status === 401 && !retry) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      return apiFetch(path, { ...options, retry: true });
    }
  }
  return response;
}

async function requestJson(path, options = {}) {
  const response = await apiFetch(path, options);
  if (!response.ok) {
    const message = await parseError(response);
    throw new Error(message);
  }
  return response.json();
}

async function parseError(response) {
  try {
    const data = await response.json();
    if (data?.detail) {
      if (typeof data.detail === "string") return data.detail;
      if (Array.isArray(data.detail)) return data.detail.map((item) => item.msg).join(", ");
    }
    if (data?.message) return data.message;
  } catch (_) {
    // ignore
  }
  return `Ошибка запроса (${response.status})`;
}

async function refreshTokens() {
  try {
    const response = await apiFetch(API_ENDPOINTS.auth + "refresh/", {
      method: "GET",
      skipAuth: true,
      retry: true,
    });
    if (!response.ok) return false;
    const data = await response.json();
    if (data?.access_token) {
      setAccessToken(data.access_token);
      return true;
    }
  } catch (_) {
    return false;
  }
  return false;
}

async function fetchProfile() {
  if (!state.accessToken) return false;
  try {
    const profile = await requestJson(API_ENDPOINTS.auth + "profile/");
    setUser(profile);
    return true;
  } catch (_) {
    setUser(null);
    return false;
  }
}

function setUser(user) {
  state.user = user || null;
  state.isAdmin = user?.role === "admin";
  if (!state.isAdmin) {
    state.uploads = [];
    state.trainings = [];
    state.selectedTrainingId = null;
  }
  updateAuthUI();
  renderProfile();
  renderSubscriptions();
  renderChannels();
  renderAdminChannels();
  renderUploads();
  renderTrainings();
  renderAdminSummary();
}

function updateAuthUI() {
  const authOnly = document.querySelectorAll(".auth-only");
  const adminOnly = document.querySelectorAll(".admin-only");
  authOnly.forEach((el) => (el.hidden = !state.user));
  adminOnly.forEach((el) => (el.hidden = !state.isAdmin));

  if (state.user) {
    dom.loginBtn.hidden = true;
    dom.registerBtn.hidden = true;
    dom.logoutBtn.hidden = false;
    dom.userState.textContent = state.user.username;
  } else {
    dom.loginBtn.hidden = false;
    dom.registerBtn.hidden = false;
    dom.logoutBtn.hidden = true;
    dom.userState.textContent = "Гость";
  }
}

function updateNavActive(route) {
  dom.navLinks.forEach((link) => {
    const target = link.getAttribute("href")?.replace("#/", "");
    link.classList.toggle("active", target === route);
  });
}

function showView(route) {
  dom.views.forEach((view) => {
    view.hidden = view.id !== route;
  });
  updateNavActive(route);
}

function requireAuth(route) {
  const adminRoutes = ["admin", "admin-channels", "admin-samples", "admin-training"];
  if (!state.user) {
    showToast("Нужна авторизация, чтобы продолжить.");
    location.hash = "#/auth";
    showView("auth");
    return false;
  }
  if (adminRoutes.includes(route) && !state.isAdmin) {
    showToast("Требуются права администратора.");
    location.hash = "#/news";
    showView("news");
    return false;
  }
  return true;
}

function truncate(text, limit = 160) {
  if (!text) return "";
  if (text.length <= limit) return text;
  return `${text.slice(0, limit).trim()}…`;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "0";
  return new Intl.NumberFormat("ru-RU").format(number);
}

function formatPercent(value, digits = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "n/a";
  return `${(number * 100).toFixed(digits)}%`;
}

function formatScalar(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Да" : "Нет";
  if (typeof value === "number") {
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(value < 1 ? 4 : 2).replace(/0+$/, "").replace(/\.$/, "");
  }
  return String(value);
}

function getMetricRows(metrics, key) {
  if (!metrics || typeof metrics !== "object") return [];
  return Array.isArray(metrics[key]) ? metrics[key] : [];
}

function toMetricSeries(rows, field) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row, index) => ({
      x: Number(row?.epoch ?? row?.step ?? index + 1),
      y: Number(row?.[field]),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
}

function getLastMetricPoint(metrics, key) {
  const rows = getMetricRows(metrics, key);
  return rows.length > 0 ? rows[rows.length - 1] : null;
}

function getBestMetricValue(metrics, key, field) {
  const rows = getMetricRows(metrics, key);
  const values = rows
    .map((row) => Number(row?.[field]))
    .filter((value) => Number.isFinite(value));
  if (values.length === 0) return null;
  return Math.max(...values);
}

function getTrainingBestAccuracy(training) {
  const valBest = getBestMetricValue(training?.metrics, "val", "accuracy");
  if (Number.isFinite(valBest)) return valBest;
  return getBestMetricValue(training?.metrics, "train", "accuracy");
}

function setStatusBadge(node, text, variant = "idle") {
  if (!node) return;
  node.textContent = text;
  node.classList.remove("is-live", "is-idle", "is-warn");
  node.classList.add(`is-${variant}`);
}

function renderDetailCards(container, items, emptyMessage) {
  if (!container) return;
  container.innerHTML = "";

  if (!items || items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = emptyMessage;
    container.appendChild(empty);
    return;
  }

  items.forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "detail-card";

    const title = document.createElement("span");
    title.textContent = label;

    const content = document.createElement("strong");
    content.textContent = value;

    card.appendChild(title);
    card.appendChild(content);
    container.appendChild(card);
  });
}

function renderConfigChips(config) {
  if (!dom.trainingConfig) return;
  dom.trainingConfig.innerHTML = "";

  if (!config || typeof config !== "object" || Object.keys(config).length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Конфиг обучения пока недоступен.";
    dom.trainingConfig.appendChild(empty);
    return;
  }

  Object.entries(config).forEach(([key, value]) => {
    const chip = document.createElement("div");
    chip.className = "config-chip";

    const label = document.createElement("span");
    label.textContent = key;

    const content = document.createElement("strong");
    content.textContent = formatScalar(value);

    chip.appendChild(label);
    chip.appendChild(content);
    dom.trainingConfig.appendChild(chip);
  });
}

function getCategoryLabel(value) {
  const item = NEWS_CATEGORIES.find((entry) => entry.value === value);
  return item?.label || value || "Без категории";
}

function updateActiveCategoriesChip() {
  if (!dom.activeCategories) return;
  const selected = state.filters.categories;
  if (!selected || selected.length === 0) {
    dom.activeCategories.textContent = "Все категории";
    return;
  }
  if (selected.length === 1) {
    dom.activeCategories.textContent = getCategoryLabel(selected[0]);
    return;
  }
  dom.activeCategories.textContent = `Категорий: ${selected.length}`;
}

function renderCategorySelect() {
  if (!dom.categoryDropdown) return;
  dom.categoryDropdown.innerHTML = "";

  NEWS_CATEGORIES.forEach((category) => {
    const label = document.createElement("label");
    label.className = "channel-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = category.value;
    checkbox.checked = state.filters.categories.includes(category.value);
    checkbox.addEventListener("change", () => {
      updateCategoryToggle();
    });

    const text = document.createElement("span");
    text.textContent = category.label;

    label.appendChild(checkbox);
    label.appendChild(text);
    dom.categoryDropdown.appendChild(label);
  });
  updateCategoryToggle();
}

function getSelectedCategoryValues() {
  if (!dom.categoryDropdown) return [];
  return Array.from(dom.categoryDropdown.querySelectorAll("input[type='checkbox']:checked")).map(
    (input) => input.value
  );
}

function updateCategoryToggle() {
  if (!dom.categoryToggle) return;
  const selected = getSelectedCategoryValues();
  if (selected.length === 0) {
    dom.categoryToggle.textContent = "Все категории";
    return;
  }
  if (selected.length === 1) {
    dom.categoryToggle.textContent = getCategoryLabel(selected[0]);
    return;
  }
  dom.categoryToggle.textContent = `Выбрано: ${selected.length}`;
}

function closeCategoryDropdown() {
  if (dom.categoryDropdown) {
    dom.categoryDropdown.hidden = true;
  }
}

function isClickInsideCategorySelect(event) {
  if (!dom.categorySelect) return false;
  if (event.composedPath) {
    return event.composedPath().includes(dom.categorySelect);
  }
  return dom.categorySelect.contains(event.target);
}

function clearCanvasChart(canvas, infoNode, message = "Нет данных для графика") {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#f7fbfa";
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = "#5f7572";
  ctx.font = '14px "Golos Text", sans-serif';
  ctx.textAlign = "center";
  ctx.fillText("Нет данных для графика", width / 2, height / 2);
  if (infoNode) {
    infoNode.textContent = message;
  }
}

function clearTrainingChart(message = "Выберите обучение для отображения метрик.") {
  clearCanvasChart(dom.trainingChart, dom.trainingChartInfo, message);
}

function drawChartLegend(ctx, x, y, color, label) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y - 8, 12, 12);
  ctx.fillStyle = "#173230";
  ctx.font = '12px "Golos Text", sans-serif';
  ctx.textAlign = "left";
  ctx.fillText(label, x + 18, y + 2);
}

function drawChartSeries(ctx, points, color) {
  if (points.length === 0) return;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2.25;
  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      ctx.lineTo(point.x, point.y);
    }
  });
  ctx.stroke();

  points.forEach((point) => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
    ctx.fill();
  });
}

function renderLineChart({
  canvas,
  infoNode,
  series,
  emptyMessage,
  infoText,
  valueFormatter = (value) => value.toFixed(2),
  fixedMin = null,
  fixedMax = null,
}) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const normalizedSeries = (series || []).map((item) => ({
    ...item,
    points: Array.isArray(item.points) ? item.points : [],
  }));
  const allPoints = normalizedSeries.flatMap((item) => item.points);

  if (allPoints.length === 0) {
    clearCanvasChart(canvas, infoNode, emptyMessage);
    return;
  }

  const width = canvas.width;
  const height = canvas.height;
  const padding = { left: 48, right: 18, top: 22, bottom: 34 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const minX = Math.min(...allPoints.map((point) => point.x));
  const maxX = Math.max(...allPoints.map((point) => point.x));
  const xSpan = Math.max(1, maxX - minX);

  let minY = Number.isFinite(fixedMin) ? fixedMin : Math.min(...allPoints.map((point) => point.y));
  let maxY = Number.isFinite(fixedMax) ? fixedMax : Math.max(...allPoints.map((point) => point.y));

  if (!Number.isFinite(fixedMin) || !Number.isFinite(fixedMax)) {
    if (minY === maxY) {
      const fallbackPad = minY === 0 ? 1 : Math.abs(minY) * 0.1;
      minY -= fallbackPad;
      maxY += fallbackPad;
    } else {
      const pad = (maxY - minY) * 0.08;
      if (!Number.isFinite(fixedMin)) {
        minY -= pad;
      }
      if (!Number.isFinite(fixedMax)) {
        maxY += pad;
      }
    }
  }

  if (Number.isFinite(fixedMin)) minY = fixedMin;
  if (Number.isFinite(fixedMax)) maxY = fixedMax;

  const ySpan = Math.max(0.0001, maxY - minY);
  const toCanvasX = (x) => padding.left + ((x - minX) / xSpan) * plotWidth;
  const toCanvasY = (y) => padding.top + (1 - (y - minY) / ySpan) * plotHeight;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#f7fbfa";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#d9e8e4";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + (plotHeight / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  ctx.strokeStyle = "#97b8b2";
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.moveTo(padding.left, padding.top);
  ctx.lineTo(padding.left, height - padding.bottom);
  ctx.lineTo(width - padding.right, height - padding.bottom);
  ctx.stroke();

  ctx.fillStyle = "#5f7572";
  ctx.font = '11px "Golos Text", sans-serif';
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i += 1) {
    const value = maxY - (ySpan / 4) * i;
    const y = padding.top + (plotHeight / 4) * i + 4;
    ctx.fillText(valueFormatter(value), padding.left - 8, y);
  }

  ctx.textAlign = "center";
  const xLabels = Array.from(new Set([minX, Math.round((minX + maxX) / 2), maxX]));
  xLabels.forEach((label) => {
    ctx.fillText(String(Math.round(label)), toCanvasX(label), height - 10);
  });

  normalizedSeries.forEach((item) => {
    const points = item.points.map((point) => ({
      x: toCanvasX(point.x),
      y: toCanvasY(point.y),
    }));
    drawChartSeries(ctx, points, item.color);
  });

  normalizedSeries.forEach((item, index) => {
    drawChartLegend(ctx, padding.left + index * 150, padding.top - 4, item.color, item.label);
  });

  if (infoNode) {
    infoNode.textContent = infoText;
  }
}

function renderTrainingChart(training) {
  if (!training) {
    clearTrainingChart();
    return;
  }

  const trainSeries = toMetricSeries(getMetricRows(training.metrics, "train"), "accuracy");
  const valSeries = toMetricSeries(getMetricRows(training.metrics, "val"), "accuracy");

  renderLineChart({
    canvas: dom.trainingChart,
    infoNode: dom.trainingChartInfo,
    series: [
      { label: "Train accuracy", color: "#1f6d63", points: trainSeries },
      { label: "Val accuracy", color: "#0f4c81", points: valSeries },
    ],
    emptyMessage: `Обучение #${training.id}: метрики accuracy пока отсутствуют.`,
    infoText: `Обучение #${training.id}: ${formatTrainingMetrics(training.metrics)}`,
    valueFormatter: (value) => formatPercent(value, 0),
    fixedMin: 0,
    fixedMax: 1,
  });
}

function renderTrainingLossChart(training) {
  if (!training) {
    clearCanvasChart(dom.trainingLossChart, dom.trainingLossInfo, "Выберите обучение для отображения loss.");
    return;
  }

  const trainSeries = toMetricSeries(getMetricRows(training.metrics, "train"), "loss");
  const valSeries = toMetricSeries(getMetricRows(training.metrics, "val"), "loss");
  const lastTrain = getLastMetricPoint(training.metrics, "train");
  const lastVal = getLastMetricPoint(training.metrics, "val");

  renderLineChart({
    canvas: dom.trainingLossChart,
    infoNode: dom.trainingLossInfo,
    series: [
      { label: "Train loss", color: "#c96835", points: trainSeries },
      { label: "Val loss", color: "#9354d0", points: valSeries },
    ],
    emptyMessage: `Обучение #${training.id}: метрики loss пока отсутствуют.`,
    infoText: `Train loss: ${formatScalar(lastTrain?.loss)}, val loss: ${formatScalar(
      lastVal?.loss
    )}`,
  });
}

function renderTrainingHistoryChart() {
  const sorted = [...state.trainings].sort((a, b) => Number(a.id) - Number(b.id));
  const points = sorted
    .map((training) => ({
      x: Number(training.id),
      y: Number(getTrainingBestAccuracy(training)),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));

  const bestTraining = [...state.trainings]
    .map((training) => ({ training, value: getTrainingBestAccuracy(training) }))
    .filter((item) => Number.isFinite(item.value))
    .sort((a, b) => Number(b.value) - Number(a.value))[0];

  renderLineChart({
    canvas: dom.trainingHistoryChart,
    infoNode: dom.trainingHistoryInfo,
    series: [{ label: "Best accuracy", color: "#1f6d63", points }],
    emptyMessage: "История запусков пока не содержит сохранённых метрик.",
    infoText: bestTraining
      ? `Лучший прогон: #${bestTraining.training.id}, accuracy ${formatPercent(bestTraining.value)}`
      : "История запусков пока не содержит сохранённых метрик.",
    valueFormatter: (value) => formatPercent(value, 0),
    fixedMin: 0,
    fixedMax: 1,
  });
}

function renderUploadChart() {
  const sorted = [...state.uploads].sort((a, b) => Number(a.id) - Number(b.id));
  const uploadPoints = sorted
    .map((item) => ({
      x: Number(item.id),
      y: Number(item.uploads),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
  const errorPoints = sorted
    .map((item) => ({
      x: Number(item.id),
      y: Number(item.errors),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));

  const totalUploads = state.uploads.reduce((sum, item) => sum + Number(item.uploads || 0), 0);
  const totalErrors = state.uploads.reduce((sum, item) => sum + Number(item.errors || 0), 0);

  renderLineChart({
    canvas: dom.uploadChart,
    infoNode: dom.uploadChartInfo,
    series: [
      { label: "Успешно", color: "#1f6d63", points: uploadPoints },
      { label: "Ошибки", color: "#c96835", points: errorPoints },
    ],
    emptyMessage: "История импортов пока отсутствует.",
    infoText: `Загружено: ${formatNumber(totalUploads)}, ошибок: ${formatNumber(totalErrors)}`,
    valueFormatter: (value) => formatNumber(Math.round(value)),
    fixedMin: 0,
  });
}

function fillCategorySelect(selectNode) {
  if (!selectNode) return;
  selectNode.innerHTML = "";
  NEWS_CATEGORIES.forEach((category) => {
    const option = document.createElement("option");
    option.value = category.value;
    option.textContent = category.label;
    selectNode.appendChild(option);
  });
}

function formatTrainingMetrics(metrics) {
  if (!metrics || typeof metrics !== "object") {
    return "Метрики отсутствуют";
  }

  const trainLast = getLastMetricPoint(metrics, "train");
  const valLast = getLastMetricPoint(metrics, "val");
  const bestVal = getBestMetricValue(metrics, "val", "accuracy");
  const parts = [
    trainLast ? `train ${formatPercent(trainLast.accuracy)}` : "train n/a",
    valLast ? `val ${formatPercent(valLast.accuracy)}` : "val n/a",
  ];

  if (Number.isFinite(bestVal)) {
    parts.push(`best val ${formatPercent(bestVal)}`);
  }

  return parts.join(" · ");
}

function renderAdminSummary() {
  if (!dom.adminStatChannels) return;

  const totalUploads = state.uploads.reduce((sum, item) => sum + Number(item.uploads || 0), 0);
  const activeTrainings = state.trainings.filter((item) => item.in_progress).length;
  const bestAccuracy = state.trainings
    .map((training) => getTrainingBestAccuracy(training))
    .filter((value) => Number.isFinite(value))
    .sort((a, b) => Number(b) - Number(a))[0];

  dom.adminStatChannels.textContent = formatNumber(state.channels.length);
  dom.adminStatUploads.textContent = formatNumber(totalUploads);
  dom.adminStatTrainings.textContent = formatNumber(state.trainings.length);
  dom.adminStatActiveTrainings.textContent = formatNumber(activeTrainings);
  dom.adminStatBestAccuracy.textContent = Number.isFinite(bestAccuracy)
    ? formatPercent(bestAccuracy)
    : "n/a";
}

function renderTrainingSnapshot(training) {
  if (!dom.trainingSnapshotTitle) return;

  if (!training) {
    dom.trainingSnapshotTitle.textContent = "Обучение не выбрано";
    setStatusBadge(dom.trainingSnapshotState, "Нет данных", "warn");
    dom.trainingSnapshotMeta.textContent =
      "Выберите обучение в истории, чтобы увидеть подробности запуска.";
    renderDetailCards(dom.trainingDetails, [], "Параметры запуска будут показаны здесь.");
    renderConfigChips(null);
    if (dom.trainingDetailsText) {
      dom.trainingDetailsText.textContent =
        "Подробности запуска появятся после выбора обучения.";
    }
    clearTrainingChart();
    clearCanvasChart(dom.trainingLossChart, dom.trainingLossInfo, "Выберите обучение для отображения loss.");
    return;
  }

  const trainRows = getMetricRows(training.metrics, "train");
  const valRows = getMetricRows(training.metrics, "val");
  const lastTrain = getLastMetricPoint(training.metrics, "train");
  const lastVal = getLastMetricPoint(training.metrics, "val");
  const bestAccuracy = getTrainingBestAccuracy(training);
  const detailItems = [
    ["ID обучения", `#${training.id}`],
    ["Устройство", formatScalar(training.device)],
    ["Epochs", formatScalar(training.config?.epochs ?? trainRows.length)],
    ["Лучшая accuracy", Number.isFinite(bestAccuracy) ? formatPercent(bestAccuracy) : "n/a"],
    ["Последняя train accuracy", lastTrain ? formatPercent(lastTrain.accuracy) : "n/a"],
    ["Последняя val accuracy", lastVal ? formatPercent(lastVal.accuracy) : "n/a"],
    ["Создано", formatDate(training.created_at) || "—"],
    ["Обновлено", formatDate(training.updated_at) || "—"],
  ];

  dom.trainingSnapshotTitle.textContent = `Обучение #${training.id}`;
  setStatusBadge(dom.trainingSnapshotState, training.in_progress ? "В процессе" : "Завершено", training.in_progress ? "live" : "idle");
  dom.trainingSnapshotMeta.textContent =
    valRows.length > 0
      ? `Зафиксировано ${trainRows.length} train-эпох и ${valRows.length} val-эпох.`
      : `Зафиксировано ${trainRows.length} train-эпох. Валидационные метрики отсутствуют.`;
  renderDetailCards(dom.trainingDetails, detailItems, "Параметры запуска будут показаны здесь.");
  renderConfigChips(training.config);
  if (dom.trainingDetailsText) {
    const modelDir = formatScalar(training.model_dir);
    dom.trainingDetailsText.textContent = training.details
      ? `${training.details} Путь к модели: ${modelDir}.`
      : `Путь к модели: ${modelDir}.`;
  }
  renderTrainingChart(training);
  renderTrainingLossChart(training);
}

function renderUploads() {
  if (!dom.uploadsList) return;
  dom.uploadsList.innerHTML = "";
  if (!state.isAdmin) {
    clearCanvasChart(dom.uploadChart, dom.uploadChartInfo, "История импортов недоступна.");
    renderAdminSummary();
    return;
  }

  if (state.uploads.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Загрузок пока нет.";
    dom.uploadsList.appendChild(empty);
    clearCanvasChart(dom.uploadChart, dom.uploadChartInfo, "История импортов пуста.");
    renderAdminSummary();
    return;
  }

  const sorted = [...state.uploads].sort((a, b) => Number(b.id) - Number(a.id));
  const fragment = document.createDocumentFragment();

  sorted.forEach((upload) => {
    const item = document.createElement("article");
    item.className = "timeline-card";

    const header = document.createElement("div");
    header.className = "timeline-header";

    const titleWrap = document.createElement("div");
    titleWrap.className = "timeline-title";

    const title = document.createElement("strong");
    title.textContent = `Импорт #${upload.id}`;

    const date = document.createElement("small");
    date.textContent = `Обновлено ${formatDate(upload.updated_at)}`;

    const status = document.createElement("span");
    status.className = "status-badge";
    setStatusBadge(status, upload.is_completed ? "Завершен" : "В процессе", upload.is_completed ? "idle" : "live");

    titleWrap.appendChild(title);
    titleWrap.appendChild(date);
    header.appendChild(titleWrap);
    header.appendChild(status);

    const metrics = document.createElement("div");
    metrics.className = "timeline-metrics";

    const uploadedPill = document.createElement("span");
    uploadedPill.className = "detail-pill";
    uploadedPill.textContent = `${formatNumber(upload.uploads)} загружено`;

    const errorPill = document.createElement("span");
    errorPill.className = "detail-pill";
    errorPill.textContent = `${formatNumber(upload.errors)} ошибок`;

    metrics.appendChild(uploadedPill);
    metrics.appendChild(errorPill);

    const note = document.createElement("p");
    note.className = "timeline-note muted";
    const details = Array.isArray(upload.details) ? upload.details.filter(Boolean) : [];
    note.textContent =
      details.length > 0
        ? details.slice(0, 2).join(" | ")
        : "Технические детали загрузки не зафиксированы.";

    item.appendChild(header);
    item.appendChild(metrics);
    item.appendChild(note);
    fragment.appendChild(item);
  });

  dom.uploadsList.appendChild(fragment);
  renderUploadChart();
  renderAdminSummary();
}

function renderTrainings() {
  if (!dom.trainingsList) return;
  dom.trainingsList.innerHTML = "";
  if (!state.isAdmin) {
    renderTrainingSnapshot(null);
    clearCanvasChart(dom.trainingHistoryChart, dom.trainingHistoryInfo, "История обучений недоступна.");
    renderAdminSummary();
    return;
  }

  if (state.trainings.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "История обучений пуста.";
    dom.trainingsList.appendChild(empty);
    state.selectedTrainingId = null;
    renderTrainingSnapshot(null);
    clearCanvasChart(dom.trainingHistoryChart, dom.trainingHistoryInfo, "История обучений пуста.");
    renderAdminSummary();
    return;
  }

  const sorted = [...state.trainings].sort((a, b) => Number(b.id) - Number(a.id));
  if (!state.selectedTrainingId || !sorted.some((item) => item.id === state.selectedTrainingId)) {
    state.selectedTrainingId = sorted[0].id;
  }

  const selectedTraining =
    sorted.find((item) => item.id === state.selectedTrainingId) || sorted[0];
  const fragment = document.createDocumentFragment();

  sorted.forEach((training) => {
    const item = document.createElement("article");
    item.className = "timeline-card training-item";
    item.classList.toggle("active", training.id === selectedTraining.id);

    const header = document.createElement("div");
    header.className = "timeline-header";

    const titleWrap = document.createElement("div");
    titleWrap.className = "timeline-title";

    const title = document.createElement("strong");
    title.textContent = `Обучение #${training.id}`;

    const date = document.createElement("small");
    date.textContent = `Создано ${formatDate(training.created_at)}`;

    const status = document.createElement("span");
    status.className = "status-badge";
    setStatusBadge(
      status,
      training.in_progress ? "В процессе" : "Завершено",
      training.in_progress ? "live" : "idle"
    );

    titleWrap.appendChild(title);
    titleWrap.appendChild(date);
    header.appendChild(titleWrap);
    header.appendChild(status);

    const metrics = document.createElement("div");
    metrics.className = "timeline-metrics";

    const accuracyPill = document.createElement("span");
    accuracyPill.className = "detail-pill";
    const bestAccuracy = getTrainingBestAccuracy(training);
    accuracyPill.textContent = Number.isFinite(bestAccuracy)
      ? `best ${formatPercent(bestAccuracy)}`
      : "best n/a";

    const metricSummary = document.createElement("span");
    metricSummary.className = "detail-pill";
    metricSummary.textContent = formatTrainingMetrics(training.metrics);

    const devicePill = document.createElement("span");
    devicePill.className = "detail-pill";
    devicePill.textContent = formatScalar(training.device);

    metrics.appendChild(accuracyPill);
    metrics.appendChild(metricSummary);
    metrics.appendChild(devicePill);

    const details = document.createElement("p");
    details.className = "timeline-note muted";
    details.textContent = training.details || `Путь к модели: ${formatScalar(training.model_dir)}`;

    item.appendChild(header);
    item.appendChild(metrics);
    item.appendChild(details);
    item.addEventListener("click", () => {
      state.selectedTrainingId = training.id;
      renderTrainings();
    });
    fragment.appendChild(item);
  });

  dom.trainingsList.appendChild(fragment);
  renderTrainingSnapshot(selectedTraining);
  renderTrainingHistoryChart();
  renderAdminSummary();
}

async function loadUploads() {
  if (!state.isAdmin) return;
  try {
    const data = await requestJson(API_ENDPOINTS.uploads);
    state.uploads = data.data || [];
    renderUploads();
  } catch (error) {
    showToast(error.message);
  }
}

async function loadTrainings() {
  if (!state.isAdmin) return;
  try {
    const data = await requestJson(API_ENDPOINTS.trainings);
    state.trainings = data.data || [];
    if (
      state.trainings.length > 0 &&
      !state.trainings.some((item) => item.id === state.selectedTrainingId)
    ) {
      const sorted = [...state.trainings].sort((a, b) => Number(b.id) - Number(a.id));
      state.selectedTrainingId = sorted[0].id;
    }
    renderTrainings();
  } catch (error) {
    showToast(error.message);
  }
}

async function loadChannels() {
  try {
    const data = await requestJson(API_ENDPOINTS.channels);
    state.channels = data.data || [];
    state.channelMap = new Map(state.channels.map((ch) => [ch.id, ch]));
    dom.channelTotal.textContent = state.channels.length;
    dom.channelMeta.textContent = `${state.channels.length} каналов`;
    renderChannelSelect();
    renderChannels();
    renderAdminChannels();
  } catch (error) {
    showToast(error.message);
  }
}

function renderChannelSelect() {
  if (!dom.channelDropdown) return;
  dom.channelDropdown.innerHTML = "";
  state.channels.forEach((channel) => {
    const label = document.createElement("label");
    label.className = "channel-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = String(channel.id);
    checkbox.checked = state.filters.channelIds.includes(checkbox.value);
    checkbox.addEventListener("change", () => {
      updateChannelToggle();
    });

    const text = document.createElement("span");
    text.textContent = channel.title;

    label.appendChild(checkbox);
    label.appendChild(text);
    dom.channelDropdown.appendChild(label);
  });
  updateChannelToggle();
}

function getSelectedChannelIds() {
  if (!dom.channelDropdown) return [];
  return Array.from(dom.channelDropdown.querySelectorAll("input[type='checkbox']:checked")).map(
    (input) => input.value
  );
}

function updateChannelToggle() {
  if (!dom.channelToggle) return;
  const selectedIds = getSelectedChannelIds();
  if (selectedIds.length === 0) {
    dom.channelToggle.textContent = "Все каналы";
    return;
  }
  if (selectedIds.length === 1) {
    dom.channelToggle.textContent =
      state.channelMap.get(Number(selectedIds[0]))?.title || "Канал";
    return;
  }
  dom.channelToggle.textContent = `Выбрано: ${selectedIds.length}`;
}

function getSelectedChannelNames() {
  const ids = getSelectedChannelIds();
  return ids
    .map((id) => state.channelMap.get(Number(id))?.title)
    .filter(Boolean);
}

function closeChannelDropdown() {
  if (dom.channelDropdown) {
    dom.channelDropdown.hidden = true;
  }
}

function isClickInsideChannelSelect(event) {
  if (!dom.channelSelect) return false;
  if (event.composedPath) {
    return event.composedPath().includes(dom.channelSelect);
  }
  return dom.channelSelect.contains(event.target);
}

async function loadNews({ reset = false } = {}) {
  if (state.isLoading) return;
  if (reset) {
    state.newsCursor = null;
    dom.newsGrid.innerHTML = "";
  }
  if (!reset && !state.hasNext) return;
  state.isLoading = true;
  const params = new URLSearchParams();
  params.set("limit", String(state.filters.limit));
  params.set("recent_first", String(state.filters.recentFirst));
  if (state.filters.query) params.set("query", state.filters.query);
  if (state.filters.channelIds.length > 0) {
    state.filters.channelIds.forEach((id) => params.append("channel_ids", id));
  }
  if (state.filters.categories.length > 0) {
    state.filters.categories.forEach((value) => params.append("categories", value));
  }
  if (!reset && state.newsCursor) params.set("search_after", state.newsCursor);

  try {
    const data = await requestJson(`${API_ENDPOINTS.news}?${params.toString()}`);
    const items = data.news || [];
    const totalCount = data.meta?.total_count ?? 0;
    const currentCount = reset ? 0 : dom.newsGrid.children.length;
    state.newsCursor = data.meta?.cursor || null;
    state.hasNext = Boolean(data.meta?.has_next);
    dom.newsTotal.textContent = totalCount;
    dom.newsMeta.textContent = `Показано ${currentCount + items.length} из ${totalCount}`;
    renderNews(items, !reset);
  } catch (error) {
    showToast(error.message);
  } finally {
    state.isLoading = false;
  }
}

function renderNews(items, append = false) {
  if (!append) dom.newsGrid.innerHTML = "";
  if (!append && items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Новостей по выбранным фильтрам не найдено.";
    dom.newsGrid.appendChild(empty);
    return;
  }
  const fragment = document.createDocumentFragment();
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "news-card";

    const img = document.createElement("img");
    img.src = item.image || PLACEHOLDER_IMAGE;
    img.alt = item.title || "news";

    const title = document.createElement("h3");
    title.className = "news-title";
    title.textContent = item.title || "Без названия";

    const summary = document.createElement("p");
    summary.className = "news-summary";
    const summaryText = truncate(item.summary || "", 180);
    summary.textContent = summaryText ? summaryText : "Отсутствует";

    const meta = document.createElement("div");
    meta.className = "news-meta";
    const channelName = state.channelMap.get(item.channel_id)?.title || `Канал #${item.channel_id}`;
    const categoryLabel = getCategoryLabel(item.category);
    meta.textContent = `ID: ${item.id} · Источник: ${item.source || channelName} · ${categoryLabel} · ${formatDate(item.published)}`;

    const actions = document.createElement("div");
    actions.className = "news-actions";
    const link = document.createElement("a");
    link.href = item.link;
    link.target = "_blank";
    link.rel = "noopener";
    link.className = "btn ghost";
    link.textContent = "Открыть источник";
    actions.appendChild(link);

    const imgContainer = document.createElement("div");
    imgContainer.className = "news-image";
    imgContainer.appendChild(img);

    const body = document.createElement("div");
    body.className = "news-body";

    body.appendChild(meta);
    body.appendChild(title);
    body.appendChild(summary);
    body.appendChild(actions);

    card.appendChild(imgContainer);
    card.appendChild(body);
    fragment.appendChild(card);
  });
  dom.newsGrid.appendChild(fragment);
}

async function loadSubscriptions() {
  if (!state.user) return;
  try {
    const data = await requestJson(API_ENDPOINTS.subscriptions);
    state.subscriptions = data.data || [];
    state.subsByChannel = new Map(state.subscriptions.map((sub) => [sub.channel_id, sub]));
    renderSubscriptions();
    renderChannels();
  } catch (error) {
    showToast(error.message);
  }
}

function renderChannels() {
  if (!dom.channelGrid) return;
  dom.channelGrid.innerHTML = "";
  const fragment = document.createDocumentFragment();
  state.channels.forEach((channel) => {
    const card = document.createElement("article");
    card.className = "panel channel-card";

    const title = document.createElement("h3");
    title.textContent = channel.title;

    const desc = document.createElement("p");
    desc.textContent = channel.description || "Описание отсутствует.";

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `ID: ${channel.id}`;

    const actions = document.createElement("div");
    actions.className = "actions";

    const link = document.createElement("a");
    link.href = channel.link;
    link.target = "_blank";
    link.rel = "noopener";
    link.className = "btn ghost";
    link.textContent = "Открыть RSS";

    actions.appendChild(link);

    if (state.user) {
      const subscribed = state.subsByChannel.has(channel.id);
      const button = document.createElement("button");
      button.className = subscribed ? "btn ghost" : "btn accent";
      button.textContent = subscribed ? "Отписаться" : "Подписаться";
      button.addEventListener("click", async () => {
        if (subscribed) {
          await unsubscribeChannel(channel.id);
        } else {
          await subscribeChannel(channel.id);
        }
      });
      actions.appendChild(button);
    }

    card.appendChild(title);
    card.appendChild(desc);
    card.appendChild(meta);
    card.appendChild(actions);
    fragment.appendChild(card);
  });
  dom.channelGrid.appendChild(fragment);
}

function renderSubscriptions() {
  if (!dom.subsGrid) return;
  dom.subsGrid.innerHTML = "";
  if (!state.user) return;
  if (state.subscriptions.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Пока нет активных подписок.";
    dom.subsGrid.appendChild(empty);
    return;
  }
  const fragment = document.createDocumentFragment();
  state.subscriptions.forEach((sub) => {
    const channel = state.channelMap.get(sub.channel_id);
    const card = document.createElement("article");
    card.className = "panel sub-card";

    const title = document.createElement("h3");
    title.textContent = channel?.title || `Канал #${sub.channel_id}`;

    const desc = document.createElement("p");
    desc.textContent = channel?.description || "Описание отсутствует.";

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `Последняя новость: #${sub.last_news_id}`;

    const actions = document.createElement("div");
    actions.className = "actions";
    const button = document.createElement("button");
    button.className = "btn ghost";
    button.textContent = "Отписаться";
    button.addEventListener("click", async () => {
      await unsubscribeChannel(sub.channel_id);
    });
    actions.appendChild(button);

    card.appendChild(title);
    card.appendChild(desc);
    card.appendChild(meta);
    card.appendChild(actions);
    fragment.appendChild(card);
  });
  dom.subsGrid.appendChild(fragment);
}

function renderProfile() {
  if (!dom.profileInfo) return;
  dom.profileInfo.innerHTML = "";
  if (!state.user) return;

  const items = [
    ["Пользователь", state.user.username],
    ["Роль", state.user.role],
    ["Имя", state.user.first_name || "—"],
    ["Фамилия", state.user.last_name || "—"],
    ["Telegram ID", state.user.telegram_id || "—"],
  ];

  items.forEach(([label, value]) => {
    const row = document.createElement("div");
    const labelEl = document.createElement("span");
    labelEl.textContent = `${label}: `;
    row.appendChild(labelEl);
    row.appendChild(document.createTextNode(value));
    dom.profileInfo.appendChild(row);
  });

  if (dom.profileForm) {
    dom.profileForm.first_name.value = state.user.first_name || "";
    dom.profileForm.last_name.value = state.user.last_name || "";
    dom.profileForm.telegram_id.value = state.user.telegram_id || "";
  }
}

function renderAdminChannels() {
  if (!dom.adminChannelList) return;
  dom.adminChannelList.innerHTML = "";
  if (!state.isAdmin) {
    renderAdminSummary();
    return;
  }

  if (state.channels.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Каналы пока не добавлены.";
    dom.adminChannelList.appendChild(empty);
    renderAdminSummary();
    return;
  }

  const fragment = document.createDocumentFragment();
  [...state.channels]
    .sort((a, b) => String(a.title).localeCompare(String(b.title), "ru"))
    .forEach((channel) => {
      const wrapper = document.createElement("div");
      wrapper.className = "panel admin-card";

      const title = document.createElement("h3");
      title.textContent = `${channel.title} (#${channel.id})`;

      const form = document.createElement("form");
      form.className = "inline-form";

      const titleField = buildField("Название", "title", channel.title);
      const linkField = buildField("RSS-ссылка", "link", channel.link, "url");
      const descField = buildTextarea("Описание", "description", channel.description || "");

      const actions = document.createElement("div");
      actions.className = "actions";

      const saveBtn = document.createElement("button");
      saveBtn.type = "submit";
      saveBtn.className = "btn accent";
      saveBtn.textContent = "Сохранить";

      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = "btn ghost";
      deleteBtn.textContent = "Удалить";
      deleteBtn.addEventListener("click", async () => {
        await deleteChannel(channel.id);
      });

      actions.appendChild(saveBtn);
      actions.appendChild(deleteBtn);

      form.appendChild(titleField);
      form.appendChild(linkField);
      form.appendChild(descField);
      form.appendChild(actions);

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = {};
        const titleValue = titleField.querySelector("input").value.trim();
        const linkValue = linkField.querySelector("input").value.trim();
        const descValue = descField.querySelector("textarea").value.trim();

        if (titleValue !== channel.title) payload.title = titleValue;
        if (linkValue !== channel.link) payload.link = linkValue;
        if (descValue !== (channel.description || "")) payload.description = descValue;

        if (Object.keys(payload).length === 0) {
          showToast("Нет изменений для сохранения.");
          return;
        }
        await updateChannel(channel.id, payload);
      });

      wrapper.appendChild(title);
      wrapper.appendChild(form);
      fragment.appendChild(wrapper);
    });

  dom.adminChannelList.appendChild(fragment);
  renderAdminSummary();
}

function buildField(labelText, name, value, type = "text") {
  const label = document.createElement("label");
  label.className = "field";
  const span = document.createElement("span");
  span.textContent = labelText;
  const input = document.createElement("input");
  input.type = type;
  input.name = name;
  input.value = value;
  label.appendChild(span);
  label.appendChild(input);
  return label;
}

function buildTextarea(labelText, name, value) {
  const label = document.createElement("label");
  label.className = "field";
  const span = document.createElement("span");
  span.textContent = labelText;
  const textarea = document.createElement("textarea");
  textarea.name = name;
  textarea.rows = 3;
  textarea.value = value;
  label.appendChild(span);
  label.appendChild(textarea);
  return label;
}

async function subscribeChannel(channelId) {
  try {
    await requestJson(`${API_ENDPOINTS.subscriptions}?channel_id=${channelId}`, {
      method: "POST",
    });
    showToast("Подписка добавлена.");
    await loadSubscriptions();
  } catch (error) {
    showToast(error.message);
  }
}

async function unsubscribeChannel(channelId) {
  const sub = state.subsByChannel.get(channelId);
  if (!sub) return;
  try {
    await requestJson(`${API_ENDPOINTS.subscriptions}?sub_id=${sub.id}`, {
      method: "DELETE",
    });
    showToast("Подписка удалена.");
    await loadSubscriptions();
  } catch (error) {
    showToast(error.message);
  }
}

async function updateChannel(channelId, payload) {
  try {
    await requestJson(`${API_ENDPOINTS.channels}${channelId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast("Канал обновлён.");
    await loadChannels();
  } catch (error) {
    showToast(error.message);
  }
}

async function deleteChannel(channelId) {
  try {
    await requestJson(`${API_ENDPOINTS.channels}${channelId}`, { method: "DELETE" });
    showToast("Канал удалён.");
    await loadChannels();
  } catch (error) {
    showToast(error.message);
  }
}

async function uploadTrainingCsv(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiFetch(API_ENDPOINTS.uploads, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

async function addLabeledSample(newsId, category) {
  const response = await apiFetch(
    `${API_ENDPOINTS.uploads}${newsId}?category=${encodeURIComponent(category)}`,
    { method: "POST" }
  );
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

function buildTrainPayload(formData) {
  const numberFields = [
    "epochs",
    "batch_size",
    "lr",
    "val_split",
    "embed_dim",
    "dropout",
  ];
  const payload = {};
  numberFields.forEach((field) => {
    const raw = String(formData.get(field) || "").trim();
    if (!raw) return;
    payload[field] = Number(raw);
  });
  payload.balance = formData.get("balance") === "on";
  return payload;
}

async function startManualTraining(payload) {
  return requestJson(API_ENDPOINTS.trainings, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function bindEvents() {
  dom.loginBtn.addEventListener("click", () => {
    location.hash = "#/auth";
  });
  dom.registerBtn.addEventListener("click", () => {
    location.hash = "#/auth";
  });
  dom.logoutBtn.addEventListener("click", () => {
    setAccessToken(null);
    setUser(null);
    showToast("Вы вышли из аккаунта.");
    location.hash = "#/news";
  });

  dom.heroRefresh.addEventListener("click", () => loadNews({ reset: true }));
  dom.heroExplore.addEventListener("click", () => {
    location.hash = "#/channels";
  });

  dom.applyFilters.addEventListener("click", () => {
    state.filters.query = dom.searchInput.value.trim();
    state.filters.channelIds = getSelectedChannelIds();
    state.filters.categories = getSelectedCategoryValues();
    state.filters.recentFirst = dom.sortSelect.value === "true";
    state.filters.limit = 9;
    closeChannelDropdown();
    closeCategoryDropdown();
    if (state.filters.channelIds.length === 0) {
      dom.activeFilter.textContent = "Все каналы";
    } else if (state.filters.channelIds.length === 1) {
      dom.activeFilter.textContent =
        state.channelMap.get(Number(state.filters.channelIds[0]))?.title || "Канал";
    } else {
      const names = getSelectedChannelNames();
      dom.activeFilter.textContent = names.length > 0 ? names.join(", ") : "Выбранные каналы";
    }
    updateActiveCategoriesChip();
    dom.activeSort.textContent = state.filters.recentFirst ? "Сначала новые" : "Сначала старые";
    loadNews({ reset: true });
  });

  dom.resetFilters.addEventListener("click", () => {
    state.filters = { query: "", channelIds: [], categories: [], recentFirst: true, limit: 9 };
    dom.searchInput.value = "";
    if (dom.channelDropdown) {
      Array.from(dom.channelDropdown.querySelectorAll("input[type='checkbox']")).forEach(
        (input) => {
          input.checked = false;
        }
      );
    }
    if (dom.categoryDropdown) {
      Array.from(dom.categoryDropdown.querySelectorAll("input[type='checkbox']")).forEach(
        (input) => {
          input.checked = false;
        }
      );
    }
    updateChannelToggle();
    updateCategoryToggle();
    dom.sortSelect.value = "true";
    dom.activeFilter.textContent = "Все каналы";
    dom.activeCategories.textContent = "Все категории";
    dom.activeSort.textContent = "Сначала новые";
    closeChannelDropdown();
    closeCategoryDropdown();
    loadNews({ reset: true });
  });

  dom.searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      dom.applyFilters.click();
    }
  });

  if (dom.channelToggle && dom.channelDropdown && dom.channelSelect) {
    dom.channelToggle.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeCategoryDropdown();
      dom.channelDropdown.hidden = !dom.channelDropdown.hidden;
    });

    dom.channelDropdown.addEventListener("click", (event) => {
      event.stopPropagation();
    });

  }

  if (dom.categoryToggle && dom.categoryDropdown && dom.categorySelect) {
    dom.categoryToggle.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeChannelDropdown();
      dom.categoryDropdown.hidden = !dom.categoryDropdown.hidden;
    });

    dom.categoryDropdown.addEventListener("click", (event) => {
      event.stopPropagation();
    });
  }

  document.addEventListener(
    "pointerdown",
    (event) => {
      if (!isClickInsideChannelSelect(event)) {
        closeChannelDropdown();
      }
      if (!isClickInsideCategorySelect(event)) {
        closeCategoryDropdown();
      }
    },
    true
  );

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeChannelDropdown();
      closeCategoryDropdown();
    }
  });

  dom.loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(dom.loginForm);
    const body = new URLSearchParams();
    body.set("username", String(formData.get("username") || ""));
    body.set("password", String(formData.get("password") || ""));

    try {
      const data = await requestJson(API_ENDPOINTS.auth + "login/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
        skipAuth: true,
      });
      setAccessToken(data.access_token);
      await fetchProfile();
      await loadSubscriptions();
      showToast("Добро пожаловать!");
      location.hash = "#/news";
    } catch (error) {
      showToast(error.message);
    }
  });

  dom.registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(dom.registerForm);
    const body = new URLSearchParams();
    body.set("username", String(formData.get("username") || ""));
    body.set("password", String(formData.get("password") || ""));

    try {
      await requestJson(API_ENDPOINTS.auth + "register/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
        skipAuth: true,
      });
      showToast("Аккаунт создан. Теперь войдите.");
      dom.registerForm.reset();
    } catch (error) {
      showToast(error.message);
    }
  });

  dom.profileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.user) return;

    const payload = {};
    const firstName = dom.profileForm.first_name.value.trim();
    const lastName = dom.profileForm.last_name.value.trim();
    const telegramId = dom.profileForm.telegram_id.value.trim();

    if (firstName) payload.first_name = firstName;
    if (lastName) payload.last_name = lastName;
    if (telegramId) payload.telegram_id = telegramId;

    if (Object.keys(payload).length === 0) {
      showToast("Заполните хотя бы одно поле.");
      return;
    }

    try {
      const profile = await requestJson(API_ENDPOINTS.auth + "profile/", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setUser(profile);
      showToast("Профиль обновлён.");
    } catch (error) {
      showToast(error.message);
    }
  });

  dom.channelCreateForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(dom.channelCreateForm);
    const payload = {
      title: String(formData.get("title") || "").trim(),
      link: String(formData.get("link") || "").trim(),
      description: String(formData.get("description") || "").trim(),
    };

    try {
      await requestJson(API_ENDPOINTS.channels, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      showToast("Канал добавлен.");
      dom.channelCreateForm.reset();
      await loadChannels();
    } catch (error) {
      showToast(error.message);
    }
  });

  if (dom.refreshUploadsBtn) {
    dom.refreshUploadsBtn.addEventListener("click", async () => {
      await loadUploads();
    });
  }

  if (dom.refreshTrainingsBtn) {
    dom.refreshTrainingsBtn.addEventListener("click", async () => {
      await loadTrainings();
    });
  }

  if (dom.sampleUploadForm) {
    dom.sampleUploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = dom.sampleCsvFile?.files?.[0];
      if (!file) {
        showToast("Выберите CSV-файл.");
        return;
      }

      try {
        const result = await uploadTrainingCsv(file);
        showToast(`Импорт принят. ID: ${result.upload_id}`);
        dom.sampleUploadForm.reset();
        await loadUploads();
      } catch (error) {
        showToast(error.message);
      }
    });
  }

  if (dom.sampleLabelForm) {
    dom.sampleLabelForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const newsId = Number(dom.sampleNewsId?.value || 0);
      const category = String(dom.sampleCategorySelect?.value || "").trim();
      if (!newsId || !category) {
        showToast("Укажите ID новости и категорию.");
        return;
      }

      try {
        await addLabeledSample(newsId, category);
        showToast("Пример добавлен в обучающую выборку.");
        dom.sampleLabelForm.reset();
        fillCategorySelect(dom.sampleCategorySelect);
      } catch (error) {
        showToast(error.message);
      }
    });
  }

  if (dom.trainModelForm) {
    dom.trainModelForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(dom.trainModelForm);
      const payload = buildTrainPayload(formData);
      try {
        const result = await startManualTraining(payload);
        showToast(`Обучение запущено. ID: ${result.training_id}`);
        await loadTrainings();
      } catch (error) {
        showToast(error.message);
      }
    });
  }

  window.addEventListener("hashchange", handleRoute);
}

async function handleRoute() {
  const rawRoute = location.hash.replace("#/", "") || "news";
  const routeAliases = {
    "admin-channels": "admin",
    "admin-samples": "admin",
    "admin-training": "admin",
  };
  const normalizedRoute = routeAliases[rawRoute] || rawRoute;
  const availableRoutes = new Set(Array.from(dom.views).map((view) => view.id));
  const route = availableRoutes.has(normalizedRoute) ? normalizedRoute : "news";
  if (route !== rawRoute) {
    location.hash = `#/${route}`;
    return;
  }

  const protectedRoutes = ["subscriptions", "profile", "admin"];
  if (protectedRoutes.includes(route)) {
    if (!requireAuth(route)) return;
  }
  showView(route);

  if (route === "news") {
    await loadNews({ reset: state.newsCursor === null });
  }
  if (route === "channels") {
    renderChannels();
  }
  if (route === "subscriptions") {
    await loadSubscriptions();
  }
  if (route === "profile") {
    await fetchProfile();
  }
  if (route === "admin") {
    await Promise.all([loadChannels(), loadUploads(), loadTrainings()]);
  }
}

async function bootstrap() {
  bindEvents();
  renderCategorySelect();
  fillCategorySelect(dom.sampleCategorySelect);
  updateActiveCategoriesChip();
  clearTrainingChart();
  clearCanvasChart(dom.trainingLossChart, dom.trainingLossInfo, "Выберите обучение для отображения loss.");
  clearCanvasChart(
    dom.trainingHistoryChart,
    dom.trainingHistoryInfo,
    "История обучений появится после первой сессии."
  );
  clearCanvasChart(dom.uploadChart, dom.uploadChartInfo, "История импортов появится после загрузки данных.");
  renderTrainingSnapshot(null);
  renderAdminSummary();
  await loadChannels();

  if (state.accessToken) {
    const ok = await fetchProfile();
    if (!ok) {
      const refreshed = await refreshTokens();
      if (refreshed) await fetchProfile();
    }
  } else {
    const refreshed = await refreshTokens();
    if (refreshed) await fetchProfile();
  }

  if (state.user) {
    await loadSubscriptions();
  }

  dom.searchInput.value = state.filters.query;
  dom.sortSelect.value = String(state.filters.recentFirst);
  updateActiveCategoriesChip();

  await handleRoute();

  if (dom.newsSentinel) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            loadNews({ reset: false });
          }
        });
      },
      { rootMargin: "200px" }
    );
    observer.observe(dom.newsSentinel);
  }
}

bootstrap();
