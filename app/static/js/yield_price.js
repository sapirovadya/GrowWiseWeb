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

        data.plots.forEach(plot => {
            const option = document.createElement("option");
            option.value = plot.plot_name;
            option.textContent = plot.plot_name;
            plotSelect.appendChild(option);
        });
    } catch (error) {
        console.error("שגיאה בטעינת רשימת החלקות:", error);
    }
}
async function fetchCropDetails() {
    const plotName = document.getElementById("plotName").value;
    const sow_date = document.getElementById("sowDate").value;
    if (!plotName || !sowDate) return;

    try {
        const response = await fetch(`/Plots/get_crop_details?plot_name=${plotName}&sow_date=${sow_date}`);
        const data = await response.json();

        if (data.error) {
            document.getElementById("crop").value = "לא נמצא";
            document.getElementById("cropYield").value = 0;
            return;
        }
        document.getElementById("crop").value = data.crop || "לא נמצא";
        document.getElementById("cropYield").value = data.crop_yield || 0;

    } catch (error) {
        console.error("שגיאה בשליפת פרטי היבול:", error);
    }
}

// save Yield Price
async function saveYieldPrice() {
    const plotName = document.getElementById("plotName").value;
    const sow_date = document.getElementById("sowDate").value;
    const pricePerKg = document.getElementById("pricePerKg").value;

    if (!plotName || !sow_date || !pricePerKg || pricePerKg <= 0) {
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
            body: JSON.stringify({ plot_name: plotName, sow_date: sow_date, price_yield: pricePerKg }),
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

async function fetchSowDates() {
    const plotName = document.getElementById("plotName").value.trim();
    if (!plotName) return;

    try {
        const response = await fetch(`/Plots/get_sow_dates?plot_name=${plotName}`);
        const data = await response.json();

        const sowDateSelect = document.getElementById("sowDate");
        sowDateSelect.innerHTML = '<option value="">בחר תאריך זריעה</option>';

        if (data.dates.length === 0) {
            sowDateSelect.innerHTML = '<option value="">אין תאריכים זמינים</option>';
            showAlert("שגיאה", "אין תאריכי זריעה זמינים עבור החלקה שנבחרה.", { restoreForm: false });
            return;
        }
        data.dates.forEach(date => {
            const option = document.createElement("option");
            option.value = date;
            option.textContent = date;
            sowDateSelect.appendChild(option);
        });
        sowDateSelect.addEventListener("change", fetchCropDetails);
    } catch (error) {
        console.error("שגיאה בשליפת תאריכי זריעה:", error);
        showAlert("שגיאה", "שגיאה בלתי צפויה בעת שליפת תאריכי הזריעה.", { restoreForm: false });
    }
}