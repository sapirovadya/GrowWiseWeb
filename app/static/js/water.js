let selectedWaterTypeForWaterPrice = null;

function selectWaterTypeForWater(type) {
    selectedWaterTypeForWaterPrice = type;
    closeChooseWaterTypeModal();

    // אחרי בחירת סוג מים, פותחים את מודל מחיר לקוב
    document.getElementById("waterPriceModal").style.display = "flex";
}
function closeChooseWaterTypeModal() {
    document.getElementById("chooseWaterTypeForWaterModal").style.display = "none";
}

function openWaterPriceModal() {
    document.getElementById("chooseWaterTypeForWaterModal").style.display = "flex";
}

function closeWaterPriceModal() {
    document.getElementById("waterPriceModal").style.display = "none";
    document.getElementById("waterPrice").value = "";
    document.getElementById("waterDate").value = "";
}

async function saveWaterPrice() {
    const waterPrice = document.getElementById("waterPrice").value;
    const waterDate = document.getElementById("waterDate").value;

    if (!waterPrice || !waterDate) {
        showAlert("שגיאה", "נא מלא את כל השדות", false);
        return;
    }
    if (waterPrice <= 0) {
        showAlert("שגיאה", "נא מלא מחיר חיובי גדול מ-0", false);
        return;
    }
    if (!selectedWaterTypeForWaterPrice) {
        showAlert("שגיאה", "נא לבחור סוג מים", false);
        return;
    }

    try {
        const response = await fetch("/expenses/water/add", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                price: parseFloat(waterPrice),
                date: waterDate,
                water_type: selectedWaterTypeForWaterPrice
            }),
        });

        const result = await response.json();
        if (response.ok) {
            showAlert("הצלחה", "התעריף נשמר בהצלחה!", false);
            closeWaterPriceModal();
        } else {
            showAlert("שגיאה", result.error, false);
        }
    } catch (error) {
        showAlert("שגיאה", "שגיאה בשליחת הנתונים לשרת.", false);
    }
}
