const state = {
  currentRun: null,
  packages: [],
};

const els = {
  form: document.querySelector("#plan-form"),
  query: document.querySelector("#user-query"),
  userId: document.querySelector("#user-id"),
  startDate: document.querySelector("#start-date"),
  endDate: document.querySelector("#end-date"),
  submit: document.querySelector("#submit-button"),
  refreshRuns: document.querySelector("#refresh-runs"),
  status: document.querySelector("#status"),
  health: document.querySelector("#health"),
  summary: document.querySelector("#summary"),
  packages: document.querySelector("#packages"),
  packageCount: document.querySelector("#package-count"),
  itinerary: document.querySelector("#itinerary"),
  selectedPackage: document.querySelector("#selected-package"),
  runs: document.querySelector("#runs"),
  memory: document.querySelector("#memory"),
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function formatTime(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.style.color = isError ? "#b91c1c" : "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }
  return data;
}

function buildPlanPayload() {
  const payload = {
    user_query: els.query.value,
    user_id: els.userId.value,
  };
  if (els.startDate.value && els.endDate.value) {
    payload.start_date = els.startDate.value;
    payload.end_date = els.endDate.value;
  }
  return payload;
}

function renderSummary(plan) {
  const brief = plan.trip_brief;
  const cost = plan.cost_breakdown || plan.recommended_package?.cost_breakdown;
  els.summary.hidden = false;
  els.summary.innerHTML = `
    <div class="metric"><span>Run</span><strong>#${escapeHtml(plan.run_id)}</strong></div>
    <div class="metric"><span>Route</span><strong>${escapeHtml(brief.origin)} to ${escapeHtml(brief.destination)}</strong></div>
    <div class="metric"><span>Dates</span><strong>${escapeHtml(brief.start_date)} to ${escapeHtml(brief.end_date)}</strong></div>
    <div class="metric"><span>Budget fit</span><strong>${formatCurrency(cost?.grand_total)}</strong></div>
  `;
}

function renderPackages(packages, recommendedId) {
  els.packageCount.textContent = packages.length ? `${packages.length} found` : "";
  if (!packages.length) {
    els.packages.className = "cards empty";
    els.packages.textContent = "No packages returned.";
    return;
  }

  els.packages.className = "cards";
  els.packages.innerHTML = packages
    .map((pkg) => {
      const cost = pkg.cost_breakdown;
      const isRecommended = pkg.package_id === recommendedId;
      const tags = [isRecommended ? "recommended" : "", ...(pkg.package_tags || [])]
        .filter(Boolean)
        .slice(0, 5);
      return `
        <article class="card">
          <div class="card-header">
            <div>
              <h3>${escapeHtml(pkg.title)}</h3>
              <div class="muted">${escapeHtml(pkg.summary)}</div>
            </div>
            <div class="price">${formatCurrency(cost.grand_total)}</div>
          </div>
          <div class="tags">
            ${tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}
          </div>
          <div class="facts">
            <div><strong>Flight:</strong> ${escapeHtml(pkg.flight.airline)} ${escapeHtml(pkg.flight.tier)}</div>
            <div><strong>Hotel:</strong> ${escapeHtml(pkg.hotel.name)}</div>
            <div><strong>Weather:</strong> ${escapeHtml(pkg.weather.expected_condition)}, ${escapeHtml(pkg.weather.avg_temp_c)} C</div>
            <div><strong>Score:</strong> ${escapeHtml(pkg.score)}</div>
          </div>
          <div class="card-actions">
            <button type="button" data-select-package="${escapeHtml(pkg.package_id)}">Select package</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderItinerary(data) {
  const days = data.itinerary || [];
  els.selectedPackage.textContent = data.selected_package_id ? data.selected_package_id : "";
  if (!days.length) {
    els.itinerary.className = "timeline empty";
    els.itinerary.textContent = "No itinerary generated yet.";
    return;
  }

  els.itinerary.className = "timeline";
  els.itinerary.innerHTML = days
    .map(
      (day) => `
        <section class="day">
          <h3>${escapeHtml(day.title)} <span class="muted">${escapeHtml(day.date)}</span></h3>
          ${day.items
            .map(
              (item) => `
                <div class="item">
                  <div class="time">${formatTime(item.start_at)}<br>${formatTime(item.end_at)}</div>
                  <div>
                    <div class="item-title">${escapeHtml(item.title)}</div>
                    <div class="muted">${escapeHtml(item.details || item.zone || item.item_type)}</div>
                  </div>
                </div>
              `,
            )
            .join("")}
        </section>
      `,
    )
    .join("");
}

function renderRuns(runs) {
  if (!runs.length) {
    els.runs.className = "list empty";
    els.runs.textContent = "No recent runs found.";
    return;
  }

  els.runs.className = "list";
  els.runs.innerHTML = runs
    .map(
      (run) => `
        <div class="run">
          <strong>#${escapeHtml(run.run_id)}</strong>
          <div>
            <div>${escapeHtml(run.user_query)}</div>
            <div class="muted">${escapeHtml(run.status)} · ${escapeHtml(run.created_at)}</div>
          </div>
          <button class="secondary" type="button" data-load-run="${escapeHtml(run.run_id)}">Load</button>
        </div>
      `,
    )
    .join("");
}

async function loadRuns() {
  const userId = els.userId.value.trim();
  const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  const data = await request(`/runs${query}`);
  renderRuns(data.runs || []);
  if (userId) {
    const memory = await request(`/users/${encodeURIComponent(userId)}/memory`);
    els.memory.className = "memory";
    els.memory.textContent = JSON.stringify(memory.memory || {}, null, 2);
  }
}

async function loadRun(runId) {
  const run = await request(`/runs/${runId}`);
  state.currentRun = run;
  state.packages = run.trip_packages || [];
  renderSummary(run);
  renderPackages(state.packages, run.recommended_package?.package_id);
  renderItinerary(run);
  setStatus(`Loaded run #${run.run_id}.`);
}

async function planTrip(event) {
  event.preventDefault();
  els.submit.disabled = true;
  setStatus("Planning trip...");
  try {
    const data = await request("/plan-trip", {
      method: "POST",
      body: JSON.stringify(buildPlanPayload()),
    });
    state.currentRun = data;
    state.packages = data.trip_packages || [];
    renderSummary(data);
    renderPackages(state.packages, data.recommended_package?.package_id);
    renderItinerary(data);
    await loadRuns();
    setStatus(`Trip planned. Run #${data.run_id} is ready.`);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    els.submit.disabled = false;
  }
}

async function selectPackage(packageId) {
  if (!state.currentRun?.run_id) {
    setStatus("Plan or load a run first.", true);
    return;
  }
  setStatus("Generating itinerary...");
  try {
    const data = await request(`/runs/${state.currentRun.run_id}/select-package`, {
      method: "POST",
      body: JSON.stringify({ package_id: packageId }),
    });
    state.currentRun = data;
    renderItinerary(data);
    await loadRuns();
    setStatus(`Selected ${packageId}. Itinerary generated.`);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function checkHealth() {
  try {
    const data = await request("/health");
    els.health.textContent = data.status === "ok" ? "API online" : "API reachable";
  } catch {
    els.health.textContent = "API offline";
    els.health.style.color = "#b91c1c";
  }
}

els.form.addEventListener("submit", planTrip);
els.refreshRuns.addEventListener("click", () => {
  setStatus("Loading recent runs...");
  loadRuns()
    .then(() => setStatus("Recent runs refreshed."))
    .catch((error) => setStatus(error.message, true));
});

document.addEventListener("click", (event) => {
  const selectButton = event.target.closest("[data-select-package]");
  if (selectButton) {
    selectPackage(selectButton.dataset.selectPackage);
    return;
  }

  const loadButton = event.target.closest("[data-load-run]");
  if (loadButton) {
    loadRun(loadButton.dataset.loadRun).catch((error) => setStatus(error.message, true));
  }
});

checkHealth();
loadRuns().catch(() => {});
