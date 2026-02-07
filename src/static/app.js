const API_BASE = "/api/v1";
const PLACEHOLDER_IMAGE = "https://placehold.co/600x400";
const ACCESS_TOKEN_KEY = "ff_access_token";

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
  filters: {
    query: "",
    channelIds: [],
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
  activeSort: document.getElementById("activeSort"),
  searchInput: document.getElementById("searchInput"),
  channelSelect: document.getElementById("channelSelect"),
  channelToggle: document.getElementById("channelToggle"),
  channelDropdown: document.getElementById("channelDropdown"),
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
  updateAuthUI();
  renderProfile();
  renderSubscriptions();
  renderChannels();
  renderAdminChannels();
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
  if (!state.user) {
    showToast("Нужна авторизация, чтобы продолжить.");
    location.hash = "#/auth";
    showView("auth");
    return false;
  }
  if (route === "admin" && !state.isAdmin) {
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
    meta.textContent = `Источник: ${item.source || channelName} · ${formatDate(item.published)}`;

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
    state.filters.recentFirst = dom.sortSelect.value === "true";
    state.filters.limit = 9;
    closeChannelDropdown();
    if (state.filters.channelIds.length === 0) {
      dom.activeFilter.textContent = "Все каналы";
    } else if (state.filters.channelIds.length === 1) {
      dom.activeFilter.textContent =
        state.channelMap.get(Number(state.filters.channelIds[0]))?.title || "Канал";
    } else {
      const names = getSelectedChannelNames();
      dom.activeFilter.textContent = names.length > 0 ? names.join(", ") : "Выбранные каналы";
    }
    dom.activeSort.textContent = state.filters.recentFirst ? "Сначала новые" : "Сначала старые";
    loadNews({ reset: true });
  });

  dom.resetFilters.addEventListener("click", () => {
    state.filters = { query: "", channelIds: [], recentFirst: true, limit: 9 };
    dom.searchInput.value = "";
    if (dom.channelDropdown) {
      Array.from(dom.channelDropdown.querySelectorAll("input[type='checkbox']")).forEach(
        (input) => {
          input.checked = false;
        }
      );
    }
    updateChannelToggle();
    dom.sortSelect.value = "true";
    dom.activeFilter.textContent = "Все каналы";
    dom.activeSort.textContent = "Сначала новые";
    closeChannelDropdown();
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
      dom.channelDropdown.hidden = !dom.channelDropdown.hidden;
    });

    dom.channelDropdown.addEventListener("click", (event) => {
      event.stopPropagation();
    });

    document.addEventListener(
      "pointerdown",
      (event) => {
        if (!isClickInsideChannelSelect(event)) {
          closeChannelDropdown();
        }
      },
      true
    );

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeChannelDropdown();
      }
    });
  }

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

  window.addEventListener("hashchange", handleRoute);
}

async function handleRoute() {
  const route = location.hash.replace("#/", "") || "news";
  if (["subscriptions", "profile", "admin"].includes(route)) {
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
    renderAdminChannels();
  }
}

async function bootstrap() {
  bindEvents();
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

  await loadNews({ reset: true });
  handleRoute();

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
