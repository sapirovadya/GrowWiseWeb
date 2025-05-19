async function openYieldPriceModal() {
    document.getElementById("yieldPriceModal").style.display = "flex";
    await fetchPlots();
}

function closeYieldPriceModal() {
    document.getElementById("yieldPriceModal").style.display = "none";
}

async function fetchPlots() {
    try {
        const response = await fetch("/Plots/get_harvested_plots");
        const data = await response.json();

        const plotSelect = document.getElementById("plotName");
        plotSelect.innerHTML = '<option value="">בחר חלקה</option>';

        const uniqueNames = new Set();
        data.plots.forEach(plot => {
            if (!uniqueNames.has(plot.plot_name)) {
                uniqueNames.add(plot.plot_name);

                const option = document.createElement("option");
                option.value = plot.plot_name;
                option.textContent = plot.plot_name;
                plotSelect.appendChild(option);
            }
        });
        plotSelect.addEventListener("change", fetchHarvestDates);
    } catch (error) {
        console.error("שגיאה בטעינת רשימת החלקות:", error);
    }
}
async function fetchCropDetails() {
    const plotName = document.getElementById("plotName").value;
    const harvest_date = document.getElementById("harvestDate").value;
    if (!plotName || !harvest_date) return;

    try {
        const response = await fetch(`/Plots/get_crop_details?plot_name=${plotName}&sow_date=${harvest_date}`);
        const data = await response.json();

        if (data.error) {
            document.getElementById("crop").value = "לא נמצא";
            document.getElementById("cropYield").value = 0;
            return;
        }

        document.getElementById("crop").value = data.crop || "לא נמצא";
        document.getElementById("cropYield").value = data.crop_yield ?? 0;
    } catch (error) {
        console.error("שגיאה בשליפת פרטי היבול:", error);
    }
}



// save Yield Price
async function saveYieldPrice() {
    const plotName = document.getElementById("plotName").value;
    const harvest_date = document.getElementById("harvestDate").value;
    const pricePerKg = document.getElementById("pricePerKg").value;
    const selectedOption = document.getElementById("plotName").selectedOptions[0];
    const plotId = selectedOption.dataset.plotId;
    if (!plotName || !harvest_date || !pricePerKg || pricePerKg <= 0) {
        showAlert("שגיאה", "נא למלא את כל השדות כראוי.", {
            restoreForm: true,
            formId: "yieldPriceForm",
            modalId: "yieldPriceModal"
        });
        return;
    }

    try {
        const response = await fetch("/Plots/update_price_yield", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                plot_id: plotId,
                plot_name: plotName,
                sow_date: harvest_date,
                price_yield: pricePerKg
            }),
        });

        if (response.ok) {
            showAlert("הצלחה", "המחיר נשמר בהצלחה!", {
                isSuccess: true,
                closeModal: closeYieldPriceModal,
                refreshPage: true
            });
        } else {
            const data = await response.json();
            showAlert("שגיאה", `שגיאה: ${data.error}`, {
                restoreForm: true,
                formId: "yieldPriceForm",
                modalId: "yieldPriceModal"
            });
        }
    } catch (error) {
        console.error("שגיאה בשמירת הנתונים:", error);
        showAlert("שגיאה", "שגיאה בלתי צפויה בעת שמירת הנתונים.", {
            restoreForm: true,
            formId: "yieldPriceForm",
            modalId: "yieldPriceModal"
        });
    }
}

async function fetchHarvestDates() {
    const plotName = document.getElementById("plotName").value.trim();
    if (!plotName) return;

    try {
        const response = await fetch(`/Plots/get_harvest_dates?plot_name=${plotName}`);
        const data = await response.json();

        const dateSelect = document.getElementById("harvestDate");
        dateSelect.innerHTML = '<option value="">בחר תאריך קציר</option>';

        if (data.dates.length === 0) {
            dateSelect.innerHTML = '<option value="">אין תאריכים זמינים</option>';
            showAlert("שגיאה", "אין תאריכי קציר זמינים עבור החלקה שנבחרה.");
            return;
        }

        data.dates.forEach(date => {
            const option = document.createElement("option");
            option.value = date;
            option.textContent = date;
            dateSelect.appendChild(option);
        });

        dateSelect.addEventListener("change", fetchCropDetails);
    } catch (error) {
        console.error("שגיאה בשליפת תאריכי קציר:", error);
        showAlert("שגיאה", "שגיאה בלתי צפויה בעת שליפת תאריכי הקציר.");
    }
}
