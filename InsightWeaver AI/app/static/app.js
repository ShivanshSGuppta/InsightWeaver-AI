(function () {
  const dash = window.__DASH__;
  if (!dash) return;

  function safeChart(id, labels, values, title) {
    const el = document.getElementById(id);
    if (!el) return;

    const ctx = el.getContext("2d");
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels || [],
        datasets: [{ label: title || "", data: values || [] }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: "#cbd5e1" } }, y: { ticks: { color: "#cbd5e1" } } }
      }
    });
  }

  if (dash.by_category) {
    safeChart("chartCategory", dash.by_category.labels, dash.by_category.values, "Amount");
  } else {
    safeChart("chartCategory", [], [], "Amount");
  }

  if (dash.by_month) {
    safeChart("chartMonth", dash.by_month.labels, dash.by_month.values, "Amount");
  } else {
    safeChart("chartMonth", [], [], "Amount");
  }
})();
