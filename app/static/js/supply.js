async function saveSupply() {
    let sessionEmail;

    if (sessionRole === "manager") {
        sessionEmail = sessionUserEmail;
    } else {
        sessionEmail = sessionManagerEmail;
    }
    const category = document.getElementById("productCategory").value;
    let productName;
    if (category === "גידול") {
        productName = document.getElementById("productName").value.trim();

        const cropList = document.getElementById("cropList");
        const isValid = Array.from(cropList.options).some(opt => opt.value === productName);
        const errorDiv = document.getElementById("productNameError");

        if (!isValid) {
            errorDiv.style.display = "block";
            document.getElementById("productName").setCustomValidity("מוצר זה לא קיים");
            document.getElementById("productName").reportValidity();
            return;
        } else {
            errorDiv.style.display = "none";
            document.getElementById("productName").setCustomValidity("");
        }
    } else {
        productName = document.getElementById("productNameInput").value.trim();
    }

    const quantity = parseFloat(document.getElementById("quantity").value);
    const unitPrice = parseFloat(document.getElementById("unitPrice").value);
    const purchaseDate = document.getElementById("purchaseDate").value;

    if (!productName || isNaN(quantity) || quantity <= 0 || isNaN(unitPrice) || unitPrice <= 0 || !purchaseDate) {
        showAlert("שגיאה", "נא להזין מספרים גדולים מ-0 לכמות ולמחיר!", true);
        return;
    }

    const supplyData = {
        category: category,
        name: productName,
        quantity: quantity,
        email: sessionEmail
    };

    const purchaseData = {
        category: category,
        name: productName,
        quantity: quantity,
        unit_price: unitPrice,
        purchase_date: purchaseDate,
    };

    try {
        const response = await fetch("/supply/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(supplyData),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "שגיאה בהוספת הפריט למלאי");
        }

        const purchaseResponse = await fetch("/expenses/purchase/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(purchaseData),
        });

        if (!purchaseResponse.ok) {
            throw new Error("שגיאה בהוספת הרכישה למערכת");
        }

        showAlert("הצלחה", "המוצר נוסף בהצלחה!", false);
        closeSupplyModal();

    } catch (error) {
        console.error("שגיאה בהוספת המוצר:", error);
        showAlert("שגיאה", error.message, true, supplyData);
    }
}


async function openSupplyModal(category) {
    document.getElementById("productCategory").value = category;
    const productNameContainer = document.getElementById("productNameContainer");

    if (category === "גידול") {
        productNameContainer.innerHTML = `
        <label for="productName">שם המוצר:</label>
        <input list="cropList" id="productName" name="productName" class="form-control" required placeholder="הכנס שם גידול">
        <datalist id="cropList"></datalist>
        <div id="productNameError" class="text-danger mt-1" style="display:none;">מוצר זה לא קיים - אנא בחר מוצר מהרשימה</div>
    `;

        const productNameInput = document.getElementById("productName");
        const cropList = document.getElementById("cropList");

        try {
            const response = await fetch("/static/data/crops_data.json");
            const data = await response.json();

            cropList.innerHTML = "";
            data.forEach(cat => {
                cat.values.forEach(crop => {
                    const option = document.createElement("option");
                    option.value = crop;
                    cropList.appendChild(option);
                });
            });

            // 🔍 בדיקת קיום ברשימה
            productNameInput.addEventListener("input", () => {
                const value = productNameInput.value.trim();
                const valid = Array.from(cropList.options).some(option => option.value === value);
                document.getElementById("productNameError").style.display = valid || !value ? "none" : "block";
                productNameInput.setCustomValidity(valid || !value ? "" : "מוצר לא קיים");
            });

        } catch (error) {
            console.error("שגיאה בטעינת רשימת הגידולים:", error);
        }
    } else {

        productNameContainer.innerHTML = `
            <label for="productNameInput">שם המוצר:</label>
            <input type="text" id="productNameInput" placeholder="הכנס שם מוצר" required>
        `;
    }

    document.getElementById("supplyModal").style.display = "block";
}

function closeSupplyModal() {
    const modal = document.getElementById("supplyModal");
    if (modal) {
        modal.style.display = "none";

        document.getElementById("productCategory").value = "";
        if (document.getElementById("productName")) {
            document.getElementById("productName").value = "";
        }
        if (document.getElementById("productNameInput")) {
            document.getElementById("productNameInput").value = "";
        }
        document.getElementById("quantity").value = "";
        document.getElementById("unitPrice").value = "";
        document.getElementById("purchaseDate").value = "";
    }
    const alertCloseButton = document.querySelector(".alert-close");
    if (alertCloseButton) {
        alertCloseButton.addEventListener("click", function () {
            window.location.reload();
        });
    }
}

function reopenSupplyModal(previousData) {
    document.getElementById("productCategory").value = previousData.category;
    if (previousData.category === "גידול") {
        document.getElementById("productName").value = previousData.name;
    } else {
        document.getElementById("productNameInput").value = previousData.name;
    }
    document.getElementById("quantity").value = previousData.quantity;
    document.getElementById("supplyModal").style.display = "block";
}

async function editSupply(productName, currentQuantity) {
    selectedProduct = productName;
    selectedCategory = "";

    const modal = document.getElementById("editSupplyModal");
    if (!modal) {
        return;
    }

    try {
        const response = await fetch(`/supply/get_category?name=${encodeURIComponent(productName)}`);
        const data = await response.json();

        if (!response.ok || !data.category) {
            throw new Error("שגיאה בשליפת קטגוריית המוצר");
        }

        selectedCategory = data.category;

        document.getElementById("editProductName").value = productName;
        document.getElementById("editQuantity").value = "";
        document.getElementById("editUnitPrice").value = "";
        document.getElementById("editPurchaseDate").value = "";
        modal.style.display = "block";

    } catch (error) {
        showAlert("שגיאה", "לא ניתן לטעון את פרטי המוצר", true);
    }
}

async function purchaseSupply() {
    if (!selectedProduct) {
        showAlert("שגיאה", "לא נבחר מוצר לרכישה!", true);
        return;
    }
    const quantityToAdd = parseFloat(document.getElementById("editQuantity").value);
    const unitPrice = parseFloat(document.getElementById("editUnitPrice").value);
    const purchaseDate = document.getElementById("editPurchaseDate").value;

    if (!selectedProduct || isNaN(quantityToAdd) || quantityToAdd <= 0 || isNaN(unitPrice) || unitPrice <= 0 || !purchaseDate) {
        showAlert("שגיאה", "נא להזין ערכים תקינים!", true);
        return;
    }

    const purchaseData = {
        name: selectedProduct,
        category: selectedCategory,
        quantity: quantityToAdd,
        unit_price: unitPrice,
        purchase_date: purchaseDate
    };

    try {
        const supplyResponse = await fetch("/supply/update_supply_quantity", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: selectedProduct,
                category: selectedCategory,
                quantity: quantityToAdd
            })
        });

        if (!supplyResponse.ok) {
            throw new Error("שגיאה בעדכון הכמות בטבלת המלאי");
        }

        const purchaseResponse = await fetch("/expenses/purchase/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(purchaseData),
        });

        if (!purchaseResponse.ok) {
            throw new Error("שגיאה בהוספת הרכישה למערכת");
        }

        showAlert("הצלחה", "הרכישה נשמרה בהצלחה!", false);

        closeEditSupplyModal();

    } catch (error) {
        showAlert("שגיאה", error.message, true);
    }
}

function closeEditSupplyModal() {
    const modal = document.getElementById("editSupplyModal");
    if (modal) {
        modal.style.display = "none";

        document.getElementById("editQuantity").value = "";
        document.getElementById("editUnitPrice").value = "";
        document.getElementById("editPurchaseDate").value = "";
    }

    const alertCloseButton = document.querySelector(".alert-close");
    if (alertCloseButton) {
        alertCloseButton.addEventListener("click", function () {
            window.location.reload();
        });
    }
}


function openSaleModal(productName) {
    document.getElementById("saleProductName").value = productName;
    document.getElementById("saleQuantity").value = "";
    document.getElementById("saleUnitPrice").value = "";
    document.getElementById("saleModal").style.display = "block";
}

function closeSaleModal() {
    document.getElementById("saleModal").style.display = "none";
}

async function submitSale() {
    const name = document.getElementById("saleProductName").value;
    const quantity = parseFloat(document.getElementById("saleQuantity").value);
    const unit_price = parseFloat(document.getElementById("saleUnitPrice").value);
    const sale_date = document.getElementById("saleDate").value;

    if (!name || isNaN(quantity) || quantity <= 0 || isNaN(unit_price) || unit_price <= 0 || !sale_date) {
        showAlert("שגיאה", "נא למלא את כל השדות עם ערכים תקינים!", true);
        return;
    }

    try {
        const response = await fetch("/supply/add_sale", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, quantity, unit_price, sale_date })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "שגיאה בשמירת המכירה");
        }

        showAlert("הצלחה", "המכירה נשמרה בהצלחה!", false);
        closeSaleModal();
        setTimeout(() => location.reload(), 1000);
    } catch (error) {
        showAlert("שגיאה", error.message, true);
        document.getElementById("saleModal").style.display = "block";
    }
}


function openUpdateInventoryModal(productName, category) {
    document.getElementById("updateProductName").value = productName;

    fetch(`/supply/get_quantity?name=${encodeURIComponent(productName)}&category=${encodeURIComponent(category)}`)
        .then(response => response.json())
        .then(data => {
            if (data.quantity !== undefined) {
                document.getElementById("currentQuantity").value = data.quantity;
                document.getElementById("updateInventoryModal").style.display = "block";
            } else {
                showAlert("שגיאה", data.error || "לא ניתן לטעון את הכמות", true);
            }
        })
        .catch(error => {
            console.error("שגיאה בשליפת כמות:", error);
            showAlert("שגיאה", "שגיאה בטעינת הכמות", true);
        });
}


function closeUpdateInventoryModal() {
    document.getElementById("updateInventoryModal").style.display = "none";
}

async function submitInventoryUpdate() {
    const name = document.getElementById("updateProductName").value;
    const newQuantity = parseFloat(document.getElementById("currentQuantity").value);

    if (isNaN(newQuantity) || newQuantity < 0) {
        showAlert("שגיאה", "נא להזין כמות חיובית או אפס", true);
        return;
    }

    try {
        const response = await fetch("/supply/update_inventory_quantity", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, new_quantity: newQuantity })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "שגיאה בעדכון הכמות");
        }

        showAlert("הצלחה", "כמות עודכנה בהצלחה!", false);
        closeUpdateInventoryModal();
        setTimeout(() => location.reload(), 1000);
    } catch (error) {
        console.error("שגיאה:", error);
        showAlert("שגיאה", error.message, true);
    }
}