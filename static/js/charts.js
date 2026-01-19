const formatNumber = (value) => new Intl.NumberFormat("en-US").format(value);
const axisColor = "rgba(229, 240, 255, 0.78)";
const gridColor = "rgba(255, 255, 255, 0.08)";

const renderCharts = (data) => {
  if (typeof Chart === "undefined") {
    return;
  }

  const monthlyLabels = data.monthly.map((item) => item.month);
  const monthlyDays = data.monthly.map((item) => item.avg_days);
  const monthlyApps = data.monthly.map((item) => item.applications);

  new Chart(document.getElementById("monthlyDaysChart"), {
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
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: axisColor } },
        y: { grid: { color: gridColor }, ticks: { color: axisColor } }
      }
    }
  });

  new Chart(document.getElementById("visaTypeChart"), {
    type: "bar",
    data: {
      labels: data.by_visa_type.map((item) => item.visa_type),
      datasets: [
        {
          label: "Avg Days",
          data: data.by_visa_type.map((item) => item.avg_days),
          backgroundColor: "rgba(58, 123, 213, 0.8)"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: axisColor } },
        y: { grid: { color: gridColor }, ticks: { color: axisColor } }
      }
    }
  });

  new Chart(document.getElementById("applicationsChart"), {
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
          }
        }
      },
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: axisColor } },
        y: { grid: { color: gridColor }, ticks: { color: axisColor } }
      }
    }
  });
};

const loadTrends = async () => {
  try {
    const response = await fetch("/trends-data");
    if (!response.ok) {
      throw new Error("Unable to load trend data.");
    }
    const data = await response.json();
    renderCharts(data);
  } catch (error) {
    console.error(error);
  }
};

document.addEventListener("DOMContentLoaded", loadTrends);
