document.addEventListener("DOMContentLoaded", async function () {

    // --- גרף דו"ח חודשי ---
    const canvas = document.getElementById('incomeExpenseChart');
    if (canvas) {
        const expense = parseFloat(canvas.dataset.expense);
        const income = parseFloat(canvas.dataset.income);
        const ctx = canvas.getContext('2d');

        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['הוצאות', 'הכנסות'],
                datasets: [{
                    label: 'דו"ח חודשי',
                    data: [expense, income],
                    backgroundColor: ['#E53935', '#4CAF50']
                }]
            },
            options: {
                responsive: true
            }
        });

        const balance = income - expense;
        const balanceStatus = document.getElementById("balanceStatus");

        if (balanceStatus) {
            if (balance > 0) {
                balanceStatus.classList.add("alert", "alert-success");
                balanceStatus.innerHTML = `החודש הצלחת להגיע לתזרים חיובי - <span dir="ltr" style="unicode-bidi: plaintext;">${balance.toFixed(2)}₪</span>`;
            } else if (balance < 0) {
                balanceStatus.classList.add("alert", "alert-danger");
                balanceStatus.innerHTML = `החודש סיימת עם תזרים שלילי - <span dir="ltr" style="unicode-bidi: plaintext;">${balance.toFixed(2)}₪</span>, לא נורא תנסה חודש הבא להגיע לתוצאות טובות יותר`;
            } else {
                balanceStatus.classList.add("alert", "alert-secondary");
                balanceStatus.textContent = "החודש הסתיים עם תזרים מאוזן.";
            }
        }
    }

    // --- גרף שנתי ---
    const yearlyCanvas = document.getElementById("yearlyIncomeExpenseChart");
    if (yearlyCanvas) {
        const rawData = yearlyCanvas.dataset.chart;
        const data = JSON.parse(rawData);

        const labels = data.map(item => item.month);
        const incomeData = data.map(item => item.income);
        const expenseData = data.map(item => item.expense);

        new Chart(yearlyCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'הכנסות',
                        data: incomeData,
                        backgroundColor: '#4CAF50',
                        stack: 'combined'
                    },
                    {
                        label: 'הוצאות',
                        data: expenseData,
                        backgroundColor: '#E53935',
                        stack: 'combined'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' }
                },
                scales: {
                    x: { stacked: true, ticks: { font: { size: 14 } } },
                    y: { stacked: true, beginAtZero: true, ticks: { font: { size: 14 } } }
                }
            }
        });
    }

    // --- גרף עוגה שנתי ---
    const pieCtx = document.getElementById('yearlyPieChart');
    if (pieCtx) {
        const pieData = JSON.parse(pieCtx.dataset.chart);
        new Chart(pieCtx, {
            type: 'pie',
            data: {
                labels: pieData.labels,
                datasets: [{
                    data: pieData.data,
                    backgroundColor: pieData.colors
                }]
            },
            options: { responsive: true }
        });
    }
    // --- גרף קו תזרים ---
    const lineCtx = document.getElementById('cashFlowChart');
    if (lineCtx) {
        const trendData = JSON.parse(lineCtx.dataset.chart);
        console.log("📊 Trend Data:", trendData);
        new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: trendData.labels,
                datasets: [
                    {
                        label: 'תזרים',
                        data: trendData.balance,
                        borderColor: 'blue',
                        backgroundColor: 'blue',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' },
                    title: {
                        display: true,
                        text: 'תזרים של שלוש השנים האחרונות',
                        font: { size: 18 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString() + ' ₪';
                            }
                        }
                    }
                }
            }
        });
    }

    // --- טעינת שמות חלקות ---
    const plotSelect = document.getElementById("plot_name");
    const urlParams = new URLSearchParams(window.location.search);
    const selectedPlot = urlParams.get("plot_name");
    const selectedSow = urlParams.get("sow_date");
    if (plotSelect) {
        fetch("/reports/get_plot_names")
            .then(res => res.json())
            .then(data => {
                data.forEach(name => {
                    const option = document.createElement("option");
                    option.value = name;
                    option.textContent = name;
                    if (selectedPlot === name) option.selected = true;
                    plotSelect.appendChild(option);
                    plotSelect.appendChild(option);
                });
                if (selectedPlot) {
                    fetch(`/reports/get_sow_dates?plot_name=${encodeURIComponent(selectedPlot)}`)
                        .then(res => res.json())
                        .then(data => {
                            sowSelect.innerHTML = "";

                            if (data.length <= 1) {
                                sowSelect.style.display = "none";
                                sowDateLabel.style.display = "none";

                                if (data.length === 1) {
                                    const opt = document.createElement("option");
                                    opt.value = data[0];
                                    opt.textContent = data[0];
                                    opt.selected = true;
                                    sowSelect.appendChild(opt);
                                }
                            } else {
                                sowSelect.style.display = "inline-block";
                                sowDateLabel.style.display = "inline-block";

                                const defaultOpt = document.createElement("option");
                                defaultOpt.value = "";
                                defaultOpt.textContent = "בחר...";
                                sowSelect.appendChild(defaultOpt);

                                data.forEach(date => {
                                    const opt = document.createElement("option");
                                    opt.value = date;
                                    opt.textContent = date;
                                    if (selectedSow === date) opt.selected = true;
                                    sowSelect.appendChild(opt);
                                });
                            }
                        });
                }
            });
    }

    // --- טעינת תאריכי sow_date ---
    const sowSelect = document.getElementById("sow_date");
    const sowDateLabel = document.querySelector("label[for='sow_date']");
    if (plotSelect && sowSelect) {
        plotSelect.addEventListener("change", () => {
            const selectedPlot = plotSelect.value;
            if (!selectedPlot) return;

            fetch(`/reports/get_sow_dates?plot_name=${encodeURIComponent(selectedPlot)}`)
                .then(res => res.json())
                .then(data => {
                    sowSelect.innerHTML = "";

                    if (data.length <= 1) {
                        sowSelect.style.display = "none";
                        sowDateLabel.style.display = "none";

                        if (data.length === 1) {
                            const option = document.createElement("option");
                            option.value = data[0];
                            option.textContent = data[0];
                            option.selected = true;
                            sowSelect.appendChild(option);
                        }
                    } else {
                        sowSelect.style.display = "inline-block";
                        sowDateLabel.style.display = "inline-block";

                        const defaultOption = document.createElement("option");
                        defaultOption.value = "";
                        defaultOption.textContent = "בחר...";
                        sowSelect.appendChild(defaultOption);

                        data.forEach(date => {
                            const option = document.createElement("option");
                            option.value = date;
                            option.textContent = date;
                            sowSelect.appendChild(option);
                        });
                    }
                });
        });
    }
    const vehiclePieCanvas = document.getElementById('vehicleExpensesPieChart');
    if (vehiclePieCanvas) {
        const labels = JSON.parse(vehiclePieCanvas.dataset.labels);
        const data = JSON.parse(vehiclePieCanvas.dataset.values);
        const colors = JSON.parse(vehiclePieCanvas.dataset.colors);

        new Chart(vehiclePieCanvas, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: {
                        display: true,
                        text: 'התפלגות הוצאות לפי קטגוריה',
                        font: {
                            size: 18
                        }
                    }
                }
            }
        });
    }
});