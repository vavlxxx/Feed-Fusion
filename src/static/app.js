const API_BASE = "/api/v1";
const PLACEHOLDER_IMAGE = "https://placehold.co/600x400";
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
  trainingChart: document.getElementById("trainingChart"),
  trainingChartInfo: document.getElementById("trainingChartInfo"),
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
    const response = await apiFetch("/auth/refresh/", { method: "GET", skipAuth: true, retry: true });
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
    const profile = await requestJson("/auth/profile/");
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
  const adminRoutes = ["admin-channels", "admin-samples", "admin-training"];
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

function clearTrainingChart(message = "Выберите обучение для отображения метрик.") {
  if (!dom.trainingChart || !dom.trainingChartInfo) return;
  const ctx = dom.trainingChart.getContext("2d");
  if (!ctx) return;

  const width = dom.trainingChart.width;
  const height = dom.trainingChart.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = "#6f5c84";
  ctx.font = '14px "Golos Text", sans-serif';
  ctx.textAlign = "center";
  ctx.fillText("Нет данных для графика", width / 2, height / 2);
  dom.trainingChartInfo.textContent = message;
}

function toAccuracySeries(rows) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row, index) => ({
      x: Number(row?.epoch ?? row?.step ?? index + 1),
      y: Number(row?.accuracy),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
}

function drawLine(ctx, points, color, radius = 3) {
  if (points.length === 0) return;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2;
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
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawLegend(ctx, x, y, color, label) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y - 9, 12, 12);
  ctx.fillStyle = "#4c1d95";
  ctx.font = '12px "Golos Text", sans-serif';
  ctx.textAlign = "left";
  ctx.fillText(label, x + 18, y);
}

function renderTrainingChart(training) {
  if (!dom.trainingChart || !dom.trainingChartInfo) return;
  const ctx = dom.trainingChart.getContext("2d");
  if (!ctx) return;

  const width = dom.trainingChart.width;
  const height = dom.trainingChart.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  if (!training) {
    clearTrainingChart();
    return;
  }

  const trainSeries = toAccuracySeries(training.metrics?.train);
  const valSeries = toAccuracySeries(training.metrics?.val);
  const allSeries = [...trainSeries, ...valSeries];

  if (allSeries.length === 0) {
    clearTrainingChart(`Обучение #${training.id}: метрики пока отсутствуют.`);
    return;
  }

  const padding = { left: 42, right: 18, top: 20, bottom: 30 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const maxX = Math.max(...allSeries.map((point) => point.x));
  const minX = Math.min(...allSeries.map((point) => point.x));
  const xSpan = Math.max(1, maxX - minX);
  const yMin = 0;
  const yMax = 1;
  const ySpan = yMax - yMin;

  const toCanvasX = (x) => padding.left + ((x - minX) / xSpan) * plotWidth;
  const toCanvasY = (y) => padding.top + (1 - (y - yMin) / ySpan) * plotHeight;

  ctx.strokeStyle = "#e4d8fb";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + (plotHeight / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  ctx.strokeStyle = "#b9a5e8";
  ctx.lineWidth = 1.3;
  ctx.beginPath();
  ctx.moveTo(padding.left, padding.top);
  ctx.lineTo(padding.left, height - padding.bottom);
  ctx.lineTo(width - padding.right, height - padding.bottom);
  ctx.stroke();

  ctx.fillStyle = "#6f5c84";
  ctx.font = '11px "Golos Text", sans-serif';
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i += 1) {
    const value = (1 - i / 4).toFixed(2);
    const y = padding.top + (plotHeight / 4) * i + 4;
    ctx.fillText(value, padding.left - 6, y);
  }

  ctx.textAlign = "center";
  const firstEpoch = Math.round(minX);
  const lastEpoch = Math.round(maxX);
  ctx.fillText(String(firstEpoch), padding.left, height - 8);
  ctx.fillText(String(lastEpoch), width - padding.right, height - 8);

  const trainPoints = trainSeries.map((point) => ({
    x: toCanvasX(point.x),
    y: toCanvasY(point.y),
  }));
  const valPoints = valSeries.map((point) => ({
    x: toCanvasX(point.x),
    y: toCanvasY(point.y),
  }));

  drawLine(ctx, trainPoints, "#6d28d9");
  drawLine(ctx, valPoints, "#14b8a6");

  drawLegend(ctx, padding.left + 8, padding.top - 4, "#6d28d9", "Train accuracy");
  drawLegend(ctx, padding.left + 160, padding.top - 4, "#14b8a6", "Val accuracy");
  dom.trainingChartInfo.textContent = `Обучение #${training.id}: ${formatTrainingMetrics(
    training.metrics
  )}`;
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

  const trainRows = Array.isArray(metrics.train) ? metrics.train : [];
  const valRows = Array.isArray(metrics.val) ? metrics.val : [];
  const trainLast = trainRows.length > 0 ? trainRows[trainRows.length - 1] : null;
  const valLast = valRows.length > 0 ? valRows[valRows.length - 1] : null;

  const trainPart = trainLast
    ? `train acc: ${Number(trainLast.accuracy ?? 0).toFixed(3)}`
    : "train acc: n/a";
  const valPart = valLast
    ? `val acc: ${Number(valLast.accuracy ?? 0).toFixed(3)}`
    : "val acc: n/a";

  return `${trainPart}, ${valPart}`;
}

function renderUploads() {
  if (!dom.uploadsList) return;
  dom.uploadsList.innerHTML = "";
  if (!state.isAdmin) return;

  if (state.uploads.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Загрузок пока нет.";
    dom.uploadsList.appendChild(empty);
    return;
  }

  const sorted = [...state.uploads].sort((a, b) => Number(b.id) - Number(a.id));
  const fragment = document.createDocumentFragment();

  sorted.forEach((upload) => {
    const item = document.createElement("div");
    item.className = "compact-item";
    const title = document.createElement("strong");
    title.textContent = `Импорт #${upload.id}`;

    const stats = document.createElement("small");
    stats.textContent = `uploads: ${upload.uploads}, errors: ${upload.errors}`;

    const status = document.createElement("small");
    status.textContent = upload.is_completed ? "Статус: завершен" : "Статус: в процессе";

    const date = document.createElement("small");
    date.textContent = `Обновлено: ${formatDate(upload.updated_at)}`;

    item.appendChild(title);
    item.appendChild(stats);
    item.appendChild(status);
    item.appendChild(date);
    fragment.appendChild(item);
  });

  dom.uploadsList.appendChild(fragment);
}

function renderTrainings() {
  if (!dom.trainingsList) return;
  dom.trainingsList.innerHTML = "";
  if (!state.isAdmin) {
    clearTrainingChart();
    return;
  }

  if (state.trainings.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "История обучений пуста.";
    dom.trainingsList.appendChild(empty);
    state.selectedTrainingId = null;
    clearTrainingChart("История обучений пуста.");
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
    const item = document.createElement("div");
    item.className = "compact-item training-item";
    item.classList.toggle("active", training.id === selectedTraining.id);

    const title = document.createElement("strong");
    title.textContent = `Обучение #${training.id}`;

    const status = document.createElement("small");
    status.textContent = training.in_progress ? "Статус: в процессе" : "Статус: завершено";

    const metrics = document.createElement("small");
    metrics.textContent = formatTrainingMetrics(training.metrics);

    const details = document.createElement("small");
    details.textContent = training.details || "Без подробностей";

    item.appendChild(title);
    item.appendChild(status);
    item.appendChild(metrics);
    item.appendChild(details);
    item.addEventListener("click", () => {
      state.selectedTrainingId = training.id;
      renderTrainings();
    });
    fragment.appendChild(item);
  });

  dom.trainingsList.appendChild(fragment);
  renderTrainingChart(selectedTraining);
}

async function loadUploads() {
  if (!state.isAdmin) return;
  try {
    const data = await requestJson("/samples/");
    state.uploads = data.data || [];
    renderUploads();
  } catch (error) {
    showToast(error.message);
  }
}

async function loadTrainings() {
  if (!state.isAdmin) return;
  try {
    const data = await requestJson("/trainings/");
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
    const data = await requestJson("/channels/");
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
    const data = await requestJson(`/news/?${params.toString()}`);
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
    const data = await requestJson("/subscriptions/");
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
  if (!state.isAdmin) return;

  const fragment = document.createDocumentFragment();
  state.channels.forEach((channel) => {
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
    await requestJson(`/subscriptions/?channel_id=${channelId}`, { method: "POST" });
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
    await requestJson(`/subscriptions/?sub_id=${sub.id}`, { method: "DELETE" });
    showToast("Подписка удалена.");
    await loadSubscriptions();
  } catch (error) {
    showToast(error.message);
  }
}

async function updateChannel(channelId, payload) {
  try {
    await requestJson(`/channels/${channelId}`, {
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
    await requestJson(`/channels/${channelId}`, { method: "DELETE" });
    showToast("Канал удалён.");
    await loadChannels();
  } catch (error) {
    showToast(error.message);
  }
}

async function uploadTrainingCsv(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiFetch("/samples/", {
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
    `/samples/${newsId}?category=${encodeURIComponent(category)}`,
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
  return requestJson("/trainings/", {
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
      const data = await requestJson("/auth/login/", {
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
      await requestJson("/auth/register/", {
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
      const profile = await requestJson("/auth/profile/", {
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
      await requestJson("/channels/", {
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
  const availableRoutes = new Set(Array.from(dom.views).map((view) => view.id));
  const route = availableRoutes.has(rawRoute) ? rawRoute : "news";
  if (route !== rawRoute) {
    location.hash = "#/news";
  }

  const protectedRoutes = [
    "subscriptions",
    "profile",
    "admin-channels",
    "admin-samples",
    "admin-training",
  ];
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
  if (route === "admin-channels") {
    renderAdminChannels();
  }
  if (route === "admin-samples") {
    await loadUploads();
  }
  if (route === "admin-training") {
    await loadTrainings();
  }
}

async function bootstrap() {
  bindEvents();
  renderCategorySelect();
  fillCategorySelect(dom.sampleCategorySelect);
  updateActiveCategoriesChip();
  clearTrainingChart();
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
