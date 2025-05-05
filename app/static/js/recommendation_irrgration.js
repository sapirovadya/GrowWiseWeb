/* recommendation irrgration*/
/* recommendation irrigation */

document.addEventListener("DOMContentLoaded", function () {
    const irrigationButton = document.getElementById("getIrrigationButton");

    if (!irrigationButton) {
        console.warn("❌ לא נמצא כפתור עם id='getIrrigationButton'");
        return;
    }

    irrigationButton.addEventListener("click", async function () {
        const modal = document.getElementById("growthForecastModal");
        const forecastTitle = document.querySelector("#growthForecastModal .modal-title");
        const recommendationText = document.getElementById("growthForecastText");

        forecastTitle.textContent = "המלצת השקיה";
        recommendationText.innerHTML = "<p>טוען המלצת השקיה...</p>";
        modal.style.display = "flex";

        const cropType = this.getAttribute("data-crop");

        if (!cropType || cropType.trim() === "" || cropType.toLowerCase() === "none") {
            recommendationText.innerHTML = `<p style="color: red;">שגיאה: טרם נבחר גידול. לא ניתן לחשב המלצת השקיה.</p>`;
            return;
        }

        console.log("✅ נשלח גידול:", cropType);

        try {
            const response = await fetch("/weather/irrigation_recommendation", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ crop_type: cropType })
            });

            if (!response.ok) {
                throw new Error("שגיאה בטעינת המלצה מהשרת");
            }

            const data = await response.json();

            if (data.irrigation_advice) {
                recommendationText.innerHTML = data.irrigation_advice;
            } else {
                recommendationText.innerHTML = `<p>לא התקבלה המלצה להשקיה.</p>`;
            }

        } catch (error) {
            console.error("שגיאה בשליפת המלצה:", error);
            recommendationText.innerHTML = `<p style="color: red;">שגיאה: ${error.message}</p>`;
        }
    });
});


