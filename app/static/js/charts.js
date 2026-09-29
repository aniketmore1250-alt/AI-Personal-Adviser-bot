document.addEventListener('DOMContentLoaded', () => {
  if (!window.Chart) return;
  const colors = ['#2B78E4', '#17A673', '#D9912D', '#8C75D8', '#D85A63', '#6B7B8D'];
  const read = (element) => { try { return JSON.parse(element.dataset.chart || '{}'); } catch { return {}; } };
  const options = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 7 } } }, scales: { y: { beginAtZero: true, grid: { color: '#edf1f5' }, ticks: { callback: (value) => value >= 1000 ? `${Math.round(value / 1000)}k` : value } }, x: { grid: { display: false } } } };
  const trend = document.querySelector('#trendChart');
  if (trend) {
    const values = read(trend);
    new Chart(trend, { type: 'line', data: { labels: values.map((item) => item.month.slice(5)), datasets: [
      { label: 'Income', data: values.map((item) => item.income), borderColor: '#2B78E4', backgroundColor: 'rgba(43,120,228,.08)', fill: true, tension: .35 },
      { label: 'Expenses', data: values.map((item) => item.expenses), borderColor: '#17A673', backgroundColor: 'transparent', tension: .35 },
    ] }, options });
  }
  const incomeExpense = document.querySelector('#incomeExpenseChart');
  if (incomeExpense) {
    const values = read(incomeExpense);
    new Chart(incomeExpense, { type: 'bar', data: { labels: values.map((item) => item.month.slice(5)), datasets: [
      { label: 'Income', data: values.map((item) => item.income), backgroundColor: '#2B78E4', borderRadius: 5 },
      { label: 'Expenses', data: values.map((item) => item.expenses), backgroundColor: '#B9F5D6', borderRadius: 5 },
    ] }, options });
  }
  const expense = document.querySelector('#expenseChart');
  if (expense) {
    const values = read(expense); const labels = Object.keys(values);
    new Chart(expense, { type: 'doughnut', data: { labels, datasets: [{ data: Object.values(values), backgroundColor: colors, borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { display: false }, tooltip: { callbacks: { label: (item) => ` ${item.label}: ${item.formattedValue}` } } } } });
  }
  const savings = document.querySelector('#savingsChart');
  if (savings) {
    const values = read(savings); const saved = Number(values.saved || 0); const target = Number(values.target_low || 0);
    new Chart(savings, { type: 'doughnut', data: { labels: ['Saved', 'Remaining'], datasets: [{ data: [saved, Math.max(target - saved, 0)], backgroundColor: ['#17A673', '#E5F0EA'], borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { display: false }, tooltip: { callbacks: { label: (item) => ` ${item.label}: ${item.formattedValue}` } } } } });
  }
});
