const formatNumber = (value) => new Intl.NumberFormat("en-US").format(value);
const axisColor = "rgba(229, 240, 255, 0.78)";
const gridColor = "rgba(255, 255, 255, 0.08)";

let monthlyChart = null;
let visaTypeChart = null;
let applicationsChart = null;
let countryChart = null;

const parseJsonResponse = async (response) => {
  const text = (await response.text()).trim();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error("Invalid server response.");
  }
};

const populateTrendsSelect = (select, options, placeholder) => {
  if (!select) {
    return;
  }
  const current = select.value;
  select.innerHTML = "";
  const placeholderOption = document.createElement("option");
  placeholderOption.value = placeholder.value;
  placeholderOption.textContent = placeholder.label;
  select.appendChild(placeholderOption);

  options.forEach((value) => {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = String(value);
    select.appendChild(option);
  });

  if (current && Array.from(select.options).some((opt) => opt.value === current)) {
    select.value = current;
  }
};

const buildTrendsUrl = (filters) => {
  const url = new URL("/api/trends", window.location.origin);
  if (filters.country && filters.country !== "all") {
    url.searchParams.set("country", filters.country);
  }
  if (filters.visaType && filters.visaType !== "all") {
    url.searchParams.set("visa_type", filters.visaType);
  }
  if (filters.year && filters.year !== "all") {
    url.searchParams.set("year", filters.year);
  }
  return url.toString();
};

const setupCanvas = (canvas) => {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  return { ctx, width: rect.width, height: rect.height };
};

const drawNoData = (ctx, width, height) => {
  ctx.fillStyle = "rgba(229, 240, 255, 0.7)";
  ctx.font = "14px Outfit, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("No data available", width / 2, height / 2);
};

const drawLineChartFallback = (canvas, values, color) => {
  const { ctx, width, height } = setupCanvas(canvas);
  ctx.clearRect(0, 0, width, height);
  if (!values.length) {
    drawNoData(ctx, width, height);
    return;
  }

  const padding = 28;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const spread = maxValue - minValue || 1;

  ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, padding + chartHeight);
  ctx.lineTo(padding + chartWidth, padding + chartHeight);
  ctx.stroke();

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = padding + (chartWidth / (values.length - 1 || 1)) * index;
    const y =
      padding +
      chartHeight -
      ((value - minValue) / spread) * chartHeight;
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();
};

const drawBarChartFallback = (canvas, values, color) => {
  const { ctx, width, height } = setupCanvas(canvas);
  ctx.clearRect(0, 0, width, height);
  if (!values.length) {
    drawNoData(ctx, width, height);
    return;
  }

  const padding = 28;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const maxValue = Math.max(...values) || 1;
  const barWidth = chartWidth / values.length;

  ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, padding + chartHeight);
  ctx.lineTo(padding + chartWidth, padding + chartHeight);
  ctx.stroke();

  ctx.fillStyle = color;
  values.forEach((value, index) => {
    const heightRatio = value / maxValue;
    const barHeight = chartHeight * heightRatio;
    const x = padding + index * barWidth + barWidth * 0.15;
    const y = padding + chartHeight - barHeight;
    const widthAdjusted = barWidth * 0.7;
    ctx.fillRect(x, y, widthAdjusted, barHeight);
  });
};

const updateKpis = (kpis = {}) => {
  const thisMonthEl = document.getElementById("kpiThisMonth");
  const avgWaitEl = document.getElementById("kpiAvgWait");
  const peakSeasonEl = document.getElementById("kpiPeakSeason");
  const peakDeltaEl = document.getElementById("kpiPeakDelta");

  if (thisMonthEl) {
    thisMonthEl.textContent = kpis.this_month_days
      ? `${kpis.this_month_days} Days`
      : "--";
  }
  if (avgWaitEl) {
    avgWaitEl.textContent = kpis.avg_wait_days ? `${kpis.avg_wait_days} Days` : "--";
  }
  if (peakSeasonEl) {
    peakSeasonEl.textContent = kpis.peak_season_label || "--";
  }
  if (peakDeltaEl) {
    const delta = Number.isFinite(kpis.peak_delta_pct) ? kpis.peak_delta_pct : 0;
    const label = delta === 0 ? "stable" : `${Math.abs(delta)}%`;
    peakDeltaEl.textContent = delta === 0 ? label : `${delta > 0 ? "up" : "down"} ${label}`;
    peakDeltaEl.classList.toggle("trend-up", delta > 0);
    peakDeltaEl.classList.toggle("trend-down", delta < 0);
    peakDeltaEl.classList.toggle("trend-stable", delta === 0);
  }
};

const renderCharts = (data) => {
  const monthlyLabels = data.months || [];
  const monthlyDays = data.seasonal_avg_days || [];
  const monthlyApps = data.monthly_volume || [];
  const countryLabels = data.country_labels || [];
  const countryDays = data.country_avg_days || [];
  const visaTypeLabels = data.visa_type_labels || [];
  const visaTypeValues = data.visa_type_avg_days || [];

  const hasData =
    monthlyDays.some((value) => value !== null && value !== undefined) ||
    monthlyApps.some((value) => value > 0) ||
    countryDays.length > 0 ||
    visaTypeValues.length > 0;

  updateKpis(data.kpis || {});

  if (!hasData) {
    if (monthlyChart) {
      monthlyChart.destroy();
      monthlyChart = null;
    }
    if (countryChart) {
      countryChart.destroy();
      countryChart = null;
    }
    if (visaTypeChart) {
      visaTypeChart.destroy();
      visaTypeChart = null;
    }
    if (applicationsChart) {
      applicationsChart.destroy();
      applicationsChart = null;
    }
    const monthlyCanvas = setupCanvas(document.getElementById("monthlyDaysChart"));
    drawNoData(monthlyCanvas.ctx, monthlyCanvas.width, monthlyCanvas.height);
    const countryCanvas = setupCanvas(document.getElementById("countryChart"));
    drawNoData(countryCanvas.ctx, countryCanvas.width, countryCanvas.height);
    const visaCanvas = setupCanvas(document.getElementById("visaTypeChart"));
    drawNoData(visaCanvas.ctx, visaCanvas.width, visaCanvas.height);
    const volumeCanvas = setupCanvas(document.getElementById("applicationsChart"));
    drawNoData(volumeCanvas.ctx, volumeCanvas.width, volumeCanvas.height);
    return;
  }

  if (typeof Chart === "undefined") {
    drawLineChartFallback(
      document.getElementById("monthlyDaysChart"),
      monthlyDays,
      "rgba(24, 224, 208, 0.9)"
    );
    drawBarChartFallback(
      document.getElementById("countryChart"),
      countryDays,
      "rgba(58, 123, 213, 0.8)"
    );
    drawBarChartFallback(
      document.getElementById("visaTypeChart"),
      visaTypeValues,
      "rgba(58, 123, 213, 0.8)"
    );
    drawBarChartFallback(
      document.getElementById("applicationsChart"),
      monthlyApps,
      "rgba(82, 240, 165, 0.7)"
    );
    return;
  }

  if (monthlyChart) {
    monthlyChart.destroy();
  }
  monthlyChart = new Chart(document.getElementById("monthlyDaysChart"), {
    type: "line",
    data: {
      labels: monthlyLabels,
      datasets: [
        {
          label: "Avg Days",
          data: monthlyDays,
          borderColor: "hsl(180, 60%, 45%)",
          backgroundColor: "rgba(24, 224, 208, 0.2)",
          tension: 0.4,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(8, 16, 30, 0.9)",
          borderColor: "rgba(24, 224, 208, 0.4)",
          borderWidth: 1,
          titleColor: "#e5f0ff",
          bodyColor: "#e5f0ff"
        }
      },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: axisColor } },
        y: { grid: { color: gridColor }, ticks: { color: axisColor } }
      }
    }
  });

  if (countryChart) {
    countryChart.destroy();
  }
  countryChart = new Chart(document.getElementById("countryChart"), {
    type: "bar",
    data: {
      labels: countryLabels,
      datasets: [
        {
          label: "Avg Days",
          data: countryDays,
          backgroundColor: "rgba(24, 224, 208, 0.75)",
          borderRadius: 8,
          barThickness: 16
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(8, 16, 30, 0.9)",
          borderColor: "rgba(24, 224, 208, 0.4)",
          borderWidth: 1,
          titleColor: "#e5f0ff",
          bodyColor: "#e5f0ff"
        }
      },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: axisColor } },
        y: { grid: { color: "transparent" }, ticks: { color: axisColor } }
      }
    }
  });

  if (visaTypeChart) {
    visaTypeChart.destroy();
  }
  visaTypeChart = new Chart(document.getElementById("visaTypeChart"), {
    type: "doughnut",
    data: {
      labels: visaTypeLabels,
      datasets: [
        {
          data: visaTypeValues,
          backgroundColor: [
            "rgba(24, 224, 208, 0.85)",
            "rgba(58, 123, 213, 0.85)",
            "rgba(82, 240, 165, 0.85)",
            "rgba(255, 191, 86, 0.85)"
          ],
          borderWidth: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: axisColor, boxWidth: 12 }
        },
        tooltip: {
          backgroundColor: "rgba(8, 16, 30, 0.9)",
          borderColor: "rgba(24, 224, 208, 0.4)",
          borderWidth: 1,
          titleColor: "#e5f0ff",
          bodyColor: "#e5f0ff",
          callbacks: {
            label: (context) => `${context.label}: ${context.raw} days`
          }
        }
      }
    }
  });

  if (applicationsChart) {
    applicationsChart.destroy();
  }
  applicationsChart = new Chart(document.getElementById("applicationsChart"), {
    type: "bar",
    data: {
      labels: monthlyLabels,
      datasets: [
        {
          label: "Applications",
          data: monthlyApps,
          backgroundColor: "rgba(82, 240, 165, 0.7)"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) =>
              `Applications: ${formatNumber(context.raw)}`
          },
          backgroundColor: "rgba(8, 16, 30, 0.9)",
          borderColor: "rgba(82, 240, 165, 0.4)",
          borderWidth: 1,
          titleColor: "#e5f0ff",
          bodyColor: "#e5f0ff"
        }
      },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: axisColor } },
        y: { grid: { color: gridColor }, ticks: { color: axisColor } }
      }
    }
  });
};

const loadTrends = async (filters = {}) => {
  try {
    const response = await fetch(buildTrendsUrl(filters));
    if (!response.ok) {
      throw new Error("Unable to load trend data.");
    }
    const data = await parseJsonResponse(response);
    if (!data) {
      throw new Error("Unable to load trend data.");
    }
    renderCharts(data);
  } catch (error) {
    if (window.trendsData && window.trendsData.months?.length) {
      renderCharts(window.trendsData);
    } else {
      console.error(error);
    }
  }
};

const loadTrendsOptions = async () => {
  const countrySelect = document.getElementById("filterCountry");
  const visaTypeSelect = document.getElementById("filterVisaType");
  const yearSelect = document.getElementById("filterYear");
  const initialOptions = window.trendsOptions || null;

  if (initialOptions) {
    populateTrendsSelect(countrySelect, initialOptions.countries, {
      value: "all",
      label: "All"
    });
    populateTrendsSelect(visaTypeSelect, initialOptions.visa_types, {
      value: "all",
      label: "All"
    });
    populateTrendsSelect(yearSelect, initialOptions.years, {
      value: "all",
      label: "All"
    });
  }

  try {
    const response = await fetch("/api/trends/meta");
    if (!response.ok) {
      throw new Error("Unable to load filter options.");
    }
    const data = await parseJsonResponse(response);
    if (!data) {
      throw new Error("Unable to load filter options.");
    }
    populateTrendsSelect(countrySelect, data.countries, {
      value: "all",
      label: "All"
    });
    populateTrendsSelect(visaTypeSelect, data.visa_types, {
      value: "all",
      label: "All"
    });
    populateTrendsSelect(yearSelect, data.years, {
      value: "all",
      label: "All"
    });
  } catch (error) {
    if (!initialOptions) {
      console.error(error);
    }
  }
};

const setupTrendsFilters = async () => {
  await loadTrendsOptions();
  const applyButton = document.getElementById("applyFilters");
  const countrySelect = document.getElementById("filterCountry");
  const visaTypeSelect = document.getElementById("filterVisaType");
  const yearSelect = document.getElementById("filterYear");

  const applyFilters = () => {
    loadTrends({
      country: countrySelect?.value || "all",
      visaType: visaTypeSelect?.value || "all",
      year: yearSelect?.value || "all"
    });
  };

  if (applyButton) {
    applyButton.addEventListener("click", applyFilters);
  }
  [countrySelect, visaTypeSelect, yearSelect].forEach((select) => {
    if (select) {
      select.addEventListener("change", applyFilters);
    }
  });

  if (window.trendsData && window.trendsData.months?.length) {
    renderCharts(window.trendsData);
  } else {
    applyFilters();
  }
};

document.addEventListener("DOMContentLoaded", setupTrendsFilters);
