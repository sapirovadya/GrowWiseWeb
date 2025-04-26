/* recommendation irrgration*/
const irrigationButton = document.getElementById("getIrrigationButton");

if (irrigationButton) {
    irrigationButton.addEventListener("click", async function () {
        const modal = document.getElementById("growthForecastModal");
        const forecastTitle = document.querySelector("#growthForecastModal .modal-title");
        const recommendationText = document.getElementById("growthForecastText");

        forecastTitle.textContent = "המלצת השקיה";
        recommendationText.innerHTML = "<p> טוען המלצת השקיה...</p>";
        modal.style.display = "flex";

        const cropType = document.getElementById("crop").textContent.trim();

        if (!cropType) {
            recommendationText.innerHTML = `<p style="color: red;"> שגיאה: סוג הגידול לא נמצא.</p>`;
            return;
        }

        try {
            const response = await fetch("/weather/irrigation_recommendation", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ crop_type: cropType })
            });

            if (!response.ok) {
                throw new Error("שגיאה בטעינת המלצה");
            }

            const data = await response.json();
            recommendationText.innerHTML = `
                <p>${data.irrigation_advice || "לא נמצאו נתוני השקיה."}</p>
            `;
        } catch (error) {
            recommendationText.innerHTML = `<p style="color: red;"> שגיאה: ${error.message}</p>`;
        }
    });
}


