/* Fuel */

function openFuelTypeModal() {
    document.getElementById("fuelTypeModal").classList.add("show");
}

function closeFuelTypeModal() {
    document.getElementById("fuelTypeModal").classList.remove("show");
}


function openRefuelModal(type) {
    closeFuelTypeModal();
    document.getElementById("fuelEntryForm").style.display = "flex";
    document.getElementById("refuelType").value = type;

    const dateField = document.getElementById("refuelDate");
    const monthField = document.getElementById("month");

    if (type === "דלקן") {
        document.getElementById("monthField").style.display = "block";
        document.getElementById("dateField").style.display = "none";

        dateField.value = "";
        dateField.removeAttribute("required");
        monthField.setAttribute("required", "required");

    } else {
        document.getElementById("monthField").style.display = "none";
        document.getElementById("dateField").style.display = "block";

        monthField.value = "";
        monthField.removeAttribute("required");
        dateField.setAttribute("required", "required");
    }

    loadVehicleNumbers();
}


function closeRefuelModal() {
    document.getElementById("fuelEntryForm").style.display = "none";
}

async function loadVehicleNumbers() {
    try {
        const response = await fetch("/expenses/get_vehicles");
        if (!response.ok) {
            throw new Error(`שגיאה בטעינת מספרי הרכב: ${response.status}`);
        }

        const vehicles = await response.json();
        if (vehicles.message) {
            showAlert("שגיאה", vehicles.message, { restoreForm: false });
            return;
        }

        const vehicleSelect = document.getElementById("vehicleNumber");

        vehicleSelect.innerHTML = '<option value="">בחר מספר רכב</option>';
        vehicles.forEach(num => {
            const option = document.createElement("option");
            option.value = num;
            option.textContent = num;
            vehicleSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading vehicles:", error);
        showAlert("שגיאה", "שגיאה בטעינת מספרי הרכבים.", {
            restoreForm: false
        });
    }
}

async function saveFuelExpense() {
    const vehicleNumber = document.getElementById("vehicleNumber").value;
    const refuelType = document.getElementById("refuelType").value;

    const refuelDateInput = document.getElementById("refuelDate");
    const monthSelect = document.getElementById("month");

    const refuelDate = refuelDateInput.style.display !== "none" ? refuelDateInput.value : null;
    const selectedMonth = monthSelect.style.display !== "none" ? monthSelect.value : null;

    const currentYear = new Date().getFullYear();
    const month = selectedMonth ? `${currentYear}-${selectedMonth}` : null;

    const fuelAmount = parseFloat(document.getElementById("fuelAmount").value);
    const cost = parseFloat(document.getElementById("cost").value);

    if (!vehicleNumber || (!refuelDate && !month) || isNaN(fuelAmount) || isNaN(cost)) {
        showAlert("שגיאה", "נא למלא את כל השדות הנדרשים.", {
            restoreForm: true,
            formId: "fuelForm",
            modalId: "fuelEntryForm"
        });
        return;
    }

    if (fuelAmount <= 0 || cost <= 0) {
        showAlert("שגיאה", "כמות הדלק והעלות חייבים להיות מספרים גדולים מ-0.", {
            restoreForm: true,
            formId: "fuelForm",
            modalId: "fuelEntryForm"
        });
        return;
    }

    const data = {
        vehicle_number: vehicleNumber,
        refuel_type: refuelType,
        refuel_date: refuelDate,
        month: month,
        fuel_amount: fuelAmount,
        cost: cost
    };

    try {
        const response = await fetch("/expenses/add_fuel_expense", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            showAlert("הצלחה", "הוצאה נשמרה בהצלחה!", {
                isSuccess: true,
                closeModal: "fuelEntryForm",
                refreshPage: true
            });
        } else {
            showAlert("שגיאה", "שגיאה בהוספת הוצאה.", {
                restoreForm: true,
                formId: "fuelForm",
                modalId: "fuelEntryForm"
            });
        }
    } catch (error) {
        console.error("Error saving fuel expense:", error);
        showAlert("שגיאה", "שגיאה בלתי צפויה בשרת.", {
            restoreForm: true,
            formId: "fuelForm",
            modalId: "fuelEntryForm"
        });
    }
}

