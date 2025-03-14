(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();


    // Initiate the wowjs
    new WOW().init();


    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.sticky-top').addClass('shadow-sm').css('top', '0px');
        } else {
            $('.sticky-top').removeClass('shadow-sm').css('top', '-150px');
        }
    });


    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({ scrollTop: 0 }, 1500, 'easeInOutExpo');
        return false;
    });


    // Modal Video
    var $videoSrc;
    $('.btn-play').click(function () {
        $videoSrc = $(this).data("src");
    });
    console.log($videoSrc);
    $('#videoModal').on('shown.bs.modal', function (e) {
        $("#video").attr('src', $videoSrc + "?autoplay=1&amp;modestbranding=1&amp;showinfo=0");
    })
    $('#videoModal').on('hide.bs.modal', function (e) {
        $("#video").attr('src', $videoSrc);
    })


    // Product carousel
    $(".product-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        margin: 25,
        loop: true,
        center: true,
        dots: false,
        nav: true,
        navText: [
            '<i class="bi bi-chevron-left"></i>',
            '<i class="bi bi-chevron-right"></i>'
        ],
        responsive: {
            0: {
                items: 1
            },
            576: {
                items: 1
            },
            768: {
                items: 2
            },
            992: {
                items: 3
            }
        }
    });


    // Testimonial carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        items: 1,
        loop: true,
        dots: true,
        nav: false,
    });

})(jQuery);

/* Notification */

function showNotificationBadge(newNotificationsCount) {
    const badge = document.getElementById("notificationBadge");
    if (newNotificationsCount > 0) {
        badge.style.display = "flex";
        badge.textContent = newNotificationsCount;
    } else {
        badge.style.display = "none";
    }
}


function toggleNotifications() {
    const modal = document.getElementById("notificationModal");
    const badge = document.getElementById("notificationBadge");

    if (modal.style.display === "none" || modal.style.display === "") {
        modal.style.display = "block";

        badge.style.display = "none";
        fetch("/users/mark_notifications_seen", { method: "POST" })
            .catch(error => console.error("Error marking notifications as seen:", error));

        fetch("/users/get_notifications")
            .then(response => response.json())
            .then(data => {
                const notificationsList = document.getElementById("notifications-list");
                if (data.notifications.length > 0) {
                    notificationsList.innerHTML = data.notifications
                        .map(notification => `
                            <div class="notification-item">
                                <p><strong>תוכן:</strong> ${notification.content}</p>
                                <p><strong>מייל:</strong> ${notification.employee_email || "לא זמין"}</p>
                                <hr>
                            </div>
                        `)
                        .join("");
                } else {
                    notificationsList.innerHTML = "<p>אין התראות חדשות.</p>";
                }
            })
            .catch(error => console.error("Error fetching notifications:", error));
    } else {
        modal.style.display = "none";
    }
}

function closeNotifications() {
    const modal = document.getElementById("notificationModal");
    modal.style.display = "none";
    document.removeEventListener("click", closeOnOutsideClick);
}

function closeOnOutsideClick(event) {
    const modal = document.getElementById("notificationModal");
    const notificationIcon = document.getElementById("notificationIcon");
    if (!modal.contains(event.target) && event.target !== notificationIcon) {
        closeNotifications();
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    if (document.getElementById("attendanceTableBody")) {
        loadAttendanceRecords();
    }

    if (document.getElementById("attendanceManagerTableBody")) {
        loadManagerAttendanceRecords();
    }

    try {
        const notificationsResponse = await fetch("/users/get_notifications");
        const notificationsData = await notificationsResponse.json();

        showNotificationBadge(notificationsData.new_notifications_count);

    } catch (error) {
        console.error("Error fetching notifications:", error);
    }
});


/* Logout */

function logout() {
    fetch('/users/logout', {
        method: 'POST',
        credentials: 'same-origin'
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            showAlert('שגיאה במהלך הניתוק.');
        }
    }).catch(error => {
        console.error('שגיאה בלתי צפויה:', error);
    });
}

// catagory of crop
// async function loadCategories() {
//     const categorySelect = document.getElementById('cropCategory');
//     categorySelect.innerHTML = '<option value="none">ללא</option>';

//     try {
//         const response = await fetch('/Plots/get_crop_categories');
//         if (!response.ok) {
//             throw new Error(`שגיאה בטעינת קטגוריות: ${response.status}`);
//         }

//         const data = await response.json();

//         data.categories.forEach(category => {
//             const option = document.createElement('option');
//             option.value = category;
//             option.textContent = category;
//             categorySelect.appendChild(option);
//         });
//         categorySelect.addEventListener('change', () => {
//             const selectedCategory = categorySelect.value;
//             loadCrops(selectedCategory);
//         });

//     } catch (error) {
//         console.error('שגיאה בטעינת קטגוריות:', error);
//         showAlert('שגיאה', 'שגיאה בעת טעינת הקטגוריות.', { restoreForm: false }); // הצגת הודעה למשתמש
//     }
// }
//update irrigation
function checkAndOpenIrrigationModal(plotId) {
    document.getElementById('irrigationModal').setAttribute('data-plot-id', plotId);
    document.getElementById('irrigationModal').style.display = 'flex';
}


function closeIrrigationModal() {
    const modal = document.getElementById('irrigationModal');
    if (modal) {
        modal.style.display = 'none';
        document.getElementById('irrigationAmount').value = '';
    }
}


async function updateIrrigation() {
    const irrigationAmount = document.getElementById('irrigationAmount').value;
    const plotId = document.getElementById('irrigationModal').getAttribute('data-plot-id');

    if (!irrigationAmount || isNaN(irrigationAmount) || irrigationAmount <= 0) {
        showAlert('שגיאה', 'נא להזין כמות השקיה תקינה.', {
            restoreForm: true,
            formId: 'irrigationForm',
            modalId: 'irrigationModal'
        });
        return;
    }

    try {
        const response = await fetch(`/Plots/update_irrigation/${plotId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ irrigation_amount: parseFloat(irrigationAmount) })
        });

        if (response.ok) {
            showAlert('הצלחה', 'ההשקיה עודכנה בהצלחה!', {
                isSuccess: true,
                redirectUrl: `/Plots/plot_details?id=${plotId}`
            });
        } else {
            const errorData = await response.json();
            showAlert('שגיאה', `שגיאה: ${errorData.error}`, {
                restoreForm: true,
                formId: 'irrigationForm',
                modalId: 'irrigationModal'
            });
        }
    } catch (error) {
        console.error(error);
        showAlert('שגיאה', 'שגיאה בעת שליחת הבקשה לשרת.', {
            restoreForm: true,
            formId: 'irrigationForm',
            modalId: 'irrigationModal'
        });
    }
}

// update plots
let selectedPlotId = null;
async function openUpdateModal(plotId) {
    if (!plotId) {
        console.error("שגיאה: לא התקבל ID חוקי לחלקה.");
        return;
    }
    selectedPlotId = plotId;
    const modal = document.getElementById("updateModal");
    let cropSelect = document.getElementById("crop");
    let cropCategoryDiv = document.getElementById("cropCategoryDiv");
    cropCategoryDiv.style.display = "none";

    modal.style.display = "flex";
    modal.setAttribute("data-plot-id", plotId);

    try {
        const response = await fetch("/supply/available_crops");
        if (!response.ok) throw new Error("שגיאה בטעינת הגידולים");

        const crops = await response.json();
        cropSelect.innerHTML = '<option value="none">ללא</option>';

        crops.forEach(crop => {
            if (crop.quantity > 0) {
                let option = document.createElement("option");
                option.value = crop.name;
                option.textContent = `${crop.name} (זמין: ${crop.quantity} ק"ג)`;
                option.dataset.quantity = crop.quantity;
                cropSelect.appendChild(option);
            }
        });
        cropDiv.style.display = crops.length > 1 ? "block" : "none";

    } catch (error) {
        console.error("שגיאה בטעינת הגידולים:", error);
    }
}

function resetCropField() {
    const cropSelect = document.getElementById('crop');
    const cropDiv = document.getElementById('cropDiv');
    cropDiv.style.display = 'none';
    cropSelect.innerHTML = '<option value="none">ללא</option>'; // איפוס
}

async function submitUpdate() {
    const plotId = selectedPlotId;

    if (!plotId) {
        showAlert("שגיאה", "לא ניתן לעדכן ללא ID חלקה.");
        return;
    }
    await updateCropCategory();
    const cropCategoryElement = document.getElementById("cropCategory");

    let cropCategory = cropCategoryElement.value;
    if (!cropCategory || cropCategory === "none") {
        cropCategory = cropCategoryElement.getAttribute("data-category") || "none";
    }
    const cropField = document.getElementById("crop");
    const sowDateField = document.getElementById("sowDate");
    const quantityPlantedField = document.getElementById("quantityPlanted");

    const crop = cropField.value;
    const sowDate = sowDateField.value;
    const quantityPlanted = parseFloat(quantityPlantedField.value);

    if (!crop || crop === "none") {
        showAlert("שגיאה", "נא לבחור גידול.");
        return;
    }
    if (!sowDate) {
        showAlert("שגיאה", "נא למלא את תאריך הזריעה.");
        return;
    }
    if (!quantityPlanted || quantityPlanted <= 0) {
        showAlert("שגיאה", "נא למלא כמות זריעה תקינה (בק״ג).");
        return;
    }
    const today = new Date().toISOString().split('T')[0];
    if (sowDate > today) {
        showAlert("שגיאה", "לא ניתן להזין תאריך עתידי לזריעה.");
        return;
    }
    try {
        const response = await fetch(`/Plots/update_plot/${plotId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                crop_category: cropCategory,
                crop: crop,
                sow_date: sowDate,
                quantity_planted: quantityPlanted
            })
        });

        if (response.ok) {
            showAlert("הצלחה", "החלקה התעדכנה בהצלחה!", {
                isSuccess: true,
                redirectUrl: `/Plots/plot_details?id=${plotId}`
            });
        } else {
            const errorData = await response.json();
            showAlert("שגיאה", errorData.error, { restoreForm: true, formId: "updatePlotForm", modalId: "updateModal" });
        }
    } catch (error) {
        showAlert("שגיאה", "שגיאה בלתי צפויה בעדכון.");
    }
}

function closeUpdateModal() {
    const modal = document.getElementById('updateModal');
    modal.style.display = 'none';
    document.getElementById('updatePlotForm').reset();
    document.getElementById("cropCategoryDiv").style.display = "none";
}

function closeGrowthForecastModal() {
    const modal = document.getElementById("growthForecastModal");
    modal.style.display = "none";
}

// archive model
function openArchiveModal(plotId) {
    selectedPlotId = plotId;
    const modal = document.getElementById('archiveModal');
    modal.style.display = 'flex';
}


function closeArchiveModal() {
    const modal = document.getElementById('archiveModal');
    modal.style.display = 'none';
    document.getElementById('cropYield').value = '';
}

async function finalizePlot() {
    const cropYield = document.getElementById('cropYield').value;
    const priceYield = document.getElementById("priceYield").value || null;
    if (!cropYield || cropYield <= 0) {
        showAlert('נא להזין כמות יבול תקינה.');
        return;
    }

    try {
        const response = await fetch(`/Plots/archive_plot/${selectedPlotId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                harvest_date: new Date().toISOString().split('T')[0], // today
                crop_yield: parseFloat(cropYield),
                price_yield: priceYield ? parseFloat(priceYield) : null
            })
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            showAlert('החלקה הועברה לארכיון בהצלחה!', null, '/Plots/track_greenhouse');
        } else {
            const errorData = await response.json();
            showAlert(`שגיאה: ${errorData.error}`);
        }
    } catch (error) {
        console.error(error);
        showAlert('שגיאה בעת שליחת הבקשה לשרת.');
    }
}

// plot form

async function openPlotForm(type) {
    setTimeout(() => {
        const plotTypeInput = document.getElementById("plotType");
        plotTypeInput.value = type;
    }, 100); // 

    let plotFormModal = document.getElementById('plotFormModal');
    let cropSelect = document.getElementById('crop');
    let cropCategoryField = document.getElementById('cropCategory');
    let selectTypeModal = document.getElementById('selectTypeModal');
    let cropDiv = document.getElementById('cropDiv');
    let sowDateDiv = document.getElementById('sowDateDiv');
    let quantityPlantedDiv = document.getElementById('quantityPlantedDiv');

    selectTypeModal.style.display = 'none';
    plotFormModal.style.display = 'flex';
    // איפוס הטופס
    document.getElementById('plotForm').reset();
    sowDateDiv.style.display = 'none';
    quantityPlantedDiv.style.display = 'none';

    try {
        const response = await fetch("/supply/available_crops");
        if (!response.ok) throw new Error("שגיאה בטעינת רשימת הגידולים");

        const crops = await response.json();
        cropSelect.innerHTML = '<option value="none">ללא</option>';

        crops.forEach(crop => {
            if (crop.quantity > 0) {
                let option = document.createElement("option");
                option.value = crop.name;
                option.textContent = `${crop.name} (זמין: ${crop.quantity} ק"ג)`;
                option.dataset.quantity = crop.quantity;
                cropSelect.appendChild(option);
            }
        });

        cropDiv.style.display = crops.length > 1 ? "block" : "none";


    } catch (error) {
        console.error("שגיאה בטעינת רשימת הגידולים:", error);
    }
    document.getElementById('crop').addEventListener('change', function () {
        updateCropCategory();
        const selectedCrop = this.value;
        const sowDateDiv = document.getElementById('sowDateDiv');
        const quantityPlantedDiv = document.getElementById('quantityPlantedDiv');
        const cropCategoryField = document.getElementById('cropCategory');

        if (selectedCrop === "none") {
            sowDateDiv.style.display = 'none';
            quantityPlantedDiv.style.display = 'none';
            cropCategoryField.value = "none";
        } else {
            sowDateDiv.style.display = 'block';
            quantityPlantedDiv.style.display = 'block';
        }

    });

    document.getElementById('quantityPlanted').addEventListener('input', function () {
        const selectedCrop = document.getElementById("crop");
        const quantityPlantedInput = this;
        const availableQuantity = parseFloat(selectedCrop.options[selectedCrop.selectedIndex].dataset.quantity);

        if (quantityPlantedInput.value > availableQuantity) {
            showAlert("שגיאה", `הזנת מספר הגדול יותר מהכמות במלאי - אתה יכול לשתול עד ${availableQuantity} ק"ג.`);
            quantityPlantedInput.value = availableQuantity;
        }
    });
}




async function savePlot() {
    const plotTypeInput = document.getElementById('plotType');
    const plotNameField = document.getElementById('plotName');
    const lengthField = document.getElementById('length');
    const widthField = document.getElementById('width');
    const cropCategoryField = document.getElementById('cropCategory');
    const cropField = document.getElementById('crop');
    const sowDateField = document.getElementById('sowDate');
    const quantityPlantedField = document.getElementById('quantityPlanted');

    if (!plotTypeInput.value.trim()) {
        showAlert("שגיאה", "סוג החלקה הוא שדה חובה.");
        return;
    }
    if (!plotNameField.value.trim()) {
        showAlert("שגיאה", "שם החלקה הוא שדה חובה.");
        return;
    }
    if (!lengthField.value.trim() || parseFloat(lengthField.value) <= 0) {
        showAlert("שגיאה", "אורך חייב להיות מספר חיובי.");
        return;
    }
    if (!widthField.value.trim() || parseFloat(widthField.value) <= 0) {
        showAlert("שגיאה", "רוחב חייב להיות מספר חיובי.");
        return;
    }

    let cropCategory = cropField.value === "none" ? "none" : cropCategoryField.value;
    let crop = cropField.value !== "none" ? cropField.value : "none";
    let sowDate = sowDateField && sowDateField.value ? sowDateField.value : "";
    let quantityPlanted = quantityPlantedField && quantityPlantedField.value ? parseFloat(quantityPlantedField.value) : "";
    const today = new Date().toISOString().split('T')[0];
    if (sowDate && sowDate > today) {
        showAlert("שגיאה", "לא ניתן להזין תאריך עתידי לזריעה.");
        return;
    }
    const plotData = {
        plot_type: plotTypeInput.value.trim(),
        plot_name: plotNameField.value.trim(),
        length: parseFloat(lengthField.value),
        width: parseFloat(widthField.value),
        crop_category: cropCategory,
        crop: crop,
        sow_date: sowDate,
        quantity_planted: quantityPlanted
    };

    try {
        const response = await fetch('/Plots/save_plot', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(plotData)
        });

        if (response.ok) {
            showAlert("הצלחה", "החלקה נשמרה בהצלחה!", { isSuccess: true, redirectUrl: "/Plots/track_greenhouse" });
        } else {
            const errorData = await response.json();
            showAlert("שגיאה", errorData.error);
        }
    } catch (error) {
        showAlert("שגיאה", "שגיאה בלתי צפויה בשמירה.");
    }
}

// plots view
const plots = [];

async function loadPlots() {
    try {
        const response = await fetch('/Plots/get_plots');
        if (!response.ok) {
            throw new Error('שגיאה בטעינת החלקות.');
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }
        plots.push(...data.plots);
        renderMultipleView();
    } catch (error) {
        console.error(error.message);
        showAlert(error.message);
    }
}

let currentPlotIndex = 0;


function renderMultipleView() {
    const container = document.getElementById("plotsContainer");
    container.innerHTML = "";
    if (plots.length === 0) {
        container.innerHTML = "<p style='text-align:center;'>אין חלקות פעילות להצגה.</p>";
        return;
    }

    plots.forEach(plot => {
        const plotContainer = document.createElement("div");
        plotContainer.classList.add("plot-container");
        plotContainer.style.cursor = "pointer";

        plotContainer.onclick = () => {
            window.location.href = `/Plots/plot_details?id=${plot._id}`;
        };

        const circleDiv = document.createElement("div");
        circleDiv.classList.add("plot-circle");

        const img = document.createElement("img");
        img.src = plot.plot_type === "חלקה" ? "/static/img/land.png" : "/static/img/green_house.png";
        circleDiv.appendChild(img);

        const nameDiv = document.createElement("div");
        nameDiv.classList.add("plot-name");
        nameDiv.textContent = plot.plot_name;

        plotContainer.appendChild(circleDiv);
        plotContainer.appendChild(nameDiv);
        container.appendChild(plotContainer);
    });
}

function updateSingleView() {
    const singleView = document.getElementById("singleView");

    if (plots.length === 0) {
        singleView.innerHTML = "<p style='text-align:center;'>אין חלקות פעילות להצגה.</p>";
        return;
    }
    const plot = plots[currentPlotIndex];

    document.getElementById("plotTitle").textContent = plot.plot_name;
    document.getElementById("plotImage").src =
        plot.plot_type === "חלקה" ? "/static/img/land.png" : "/static/img/green_house.png";

    const plotDetailsLink = document.getElementById("plotDetailsLink");
    plotDetailsLink.href = `/Plots/plot_details?id=${plot._id}`;

    document.getElementById("plottype").textContent = plot.plot_type || "לא זמין";
    document.getElementById("plotLength").textContent = plot.length || "לא זמין";
    document.getElementById("plotWidth").textContent = plot.width || "לא זמין";
    document.getElementById("plotCrop").textContent =
        plot.crop === "none" ? " טרם נבחר גידול" : (plot.crop || "לא זמין");

    document.getElementById("sowdate").textContent =
        plot.sow_date === "" ? "טרם בוצעה זריעה" : (plot.sow_date || "לא זמין");

    document.getElementById("lastIrrigationDate").textContent =
        plot.last_irrigation_date == null ? "טרם בוצעה השקייה" : plot.last_irrigation_date;

    document.getElementById("totalIrrigationAmount").textContent =
        plot.total_irrigation_amount == null ? "0" : plot.total_irrigation_amount;
}

function closePlotForm() {
    const plotFormModal = document.getElementById('plotFormModal');
    plotFormModal.style.display = 'none';

    const form = document.getElementById('plotForm');
    form.reset();
    document.getElementById('cropDiv').style.display = 'none';
    document.getElementById('sowDateDiv').style.display = 'none';
    document.getElementById('quantityPlantedDiv').style.display = 'none';
}


// profile 
function saveChanges() {
    const firstName = document.getElementById("firstName").value.trim();
    const lastName = document.getElementById("lastName").value.trim();
    const email = document.getElementById("email").value.trim();

    if (!firstName) {
        showAlert("שגיאה", "נא להזין שם פרטי.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    if (/[^a-zA-Zא-ת\s]/.test(firstName)) {
        showAlert("שגיאה", "שם פרטי יכול להכיל רק אותיות בעברית או באנגלית.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    if (!lastName) {
        showAlert("שגיאה", "נא להזין שם משפחה.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    if (/[^a-zA-Zא-ת\s]/.test(lastName)) {
        showAlert("שגיאה", "שם משפחה יכול להכיל רק אותיות בעברית או באנגלית.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!email) {
        showAlert("שגיאה", "נא להזין כתובת אימייל.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    if (!emailPattern.test(email)) {
        showAlert("שגיאה", "כתובת האימייל אינה תקינה. יש להזין כתובת חוקית.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    const formData = new FormData(document.getElementById("profileForm"));

    fetch('/users/save_profile', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert("הצלחה", data.message, { refreshPage: true });
            } else {
                showAlert("שגיאה", data.message, { restoreForm: true, formId: "profileForm" });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert("שגיאה", "אירעה שגיאה בשמירת השינויים.", { restoreForm: true, formId: "profileForm" });
        });
}

// my team
let currentEmployeeEmail = "";
function openEmployeeModal(id, firstName, lastName, email, role, isApproved) {
    const modal = document.getElementById("detailsModal");
    const firstNameField = document.getElementById("detail-first-name");
    const lastNameField = document.getElementById("detail-last-name");
    const emailField = document.getElementById("detail-email");
    const roleField = document.getElementById("detail-role");
    const actions = document.getElementById("modal-actions");
    // הגדרת תרגום התפקיד
    const roleText = role === "employee" ? "עובד" : role === "co_manager" ? "שותף" : "לא ידוע";
    // הגדרת נתונים בחלון הקופץ
    firstNameField.textContent = firstName;
    lastNameField.textContent = lastName;
    emailField.textContent = email;
    roleField.textContent = roleText;
    actions.innerHTML = "";
    if (isApproved == 0) {
        actions.innerHTML = `
            <button class="btn btn-success btn-lg" onclick="approveUser('${id}')">אשר</button>
            <button class="btn btn-danger btn-lg ms-3" onclick="rejectUser('${id}')">דחה</button>
        `;
    }
    modal.style.display = "flex";
}
function approveUser(id) {
    fetch(`/users/manager/approve_user/${id}`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            showAlert("הצלחה", "המשתמש נוסף בהצלחה", {
                onSuccess: () => {
                    closeModal();
                    location.reload();
                }
            });
        })
        .catch(error => console.error('Error:', error));
}

function rejectUser(id) {
    fetch(`/users/manager/reject_user/${id}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            showAlert("הצלחה", "המשתמש הוסר בהצלחה", {
                onSuccess: () => {
                    closeModal();
                    location.reload();
                }
            });
        })
        .catch(error => console.error('Error:', error));
}


function closeOnOutsideClick(event) {
    const taskModal = document.getElementById("taskModal");
    const taskModalContent = document.getElementById("taskModalContent");

    if (taskModal.style.display === "flex" &&
        !taskModalContent.contains(event.target)) {
        closeTaskModal();
    }
}
function deleteEmployee(employeeId) {
    showCustomConfirm("האם אתה בטוח שברצונך למחוק את העובד?", () => {
        fetch(`/users/manager/deleteuser/${employeeId}`, {
            method: 'DELETE'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error("לא ניתן למחוק את המשתמש.");
                }
                return response.json();
            })
            .then(data => {
                showAlert("הצלחה", data.message, {
                    onSuccess: () => {
                        location.reload();
                    }
                });
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert("שגיאה", "לא ניתן למחוק את המשתמש.", {
                    onSuccess: () => {
                        closeModal();
                    }
                });
            });
    });
}

function showCustomConfirm(message, onConfirm) {
    const confirmBox = document.getElementById("customConfirm");
    const messageBox = confirmBox.querySelector(".alert-message");
    const yesButton = document.getElementById("confirmYes");
    const noButton = document.getElementById("confirmNo");

    messageBox.textContent = message;
    confirmBox.style.display = "block";

    yesButton.onclick = function () {
        confirmBox.style.display = "none";
        if (typeof onConfirm === "function") { // בדיקה שהפרמטר הוא פונקציה
            onConfirm();
        }
    };
    noButton.onclick = function () {
        confirmBox.style.display = "none";
    };
}

// task form in my team
function openTaskModal(employeeEmail, employeeName) {
    currentEmployeeEmail = employeeEmail;
    const modal = document.getElementById("taskModal");
    modal.style.display = "flex";
    document.getElementById("taskName").value = "";
    document.getElementById("taskContent").value = "";
    document.getElementById("dueDate").value = "";
    document.addEventListener("mousedown", closeOnOutsideClick);
}
function closeTaskModal() {
    const modal = document.getElementById("taskModal");
    modal.style.display = "none";
    document.removeEventListener("mousedown", closeOnOutsideClick);
}

// שמירת משימה
function saveTask() {
    const taskName = document.getElementById("taskName").value;
    const taskContent = document.getElementById("taskContent").value;
    const dueDate = document.getElementById("dueDate").value;

    if (!taskName || !taskContent || !dueDate) {
        // Save current form data to restore later
        const restoreData = {
            formId: "taskForm",
            lastData: {
                taskName,
                taskContent,
                dueDate
            }
        };

        showAlert("שגיאה", "יש למלא את כל השדות.", {
            restoreModal: "taskModal",
            restoreData
        });
        return;
    }

    const taskData = {
        giver_email: "{{ session['email'] }}",
        employee_email: currentEmployeeEmail,
        task_name: taskName,
        task_content: taskContent,
        due_date: dueDate,
        status: "in_progress"
    };

    fetch("/task/tasks", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(taskData)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error("שגיאה בשמירת המשימה.");
            }
            return response.json();
        })
        .then(data => {
            showAlert("הצלחה", data.message, {
                onSuccess: () => {
                    closeTaskModal();
                    location.reload();
                }
            });
        })
        .catch(error => {
            console.error("Error:", error);
            showAlert("שגיאה", "שגיאה בשמירת המשימה.");
        });
}


//social_feed
$(document).ready(function () {
    function fetchPosts() {

        const loggedInUserEmail = $("#postsContainer").data("user-email"); // קבלת המייל של המשתמש המחובר

        $.get("/posts/", function (data) {
            $("#postsContainer").empty();
            data.forEach(post => {
                let isUserPost = post.publisher_email === loggedInUserEmail;

                let sortedComments = post.comments
                    .slice()
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

                let commentsHtml = sortedComments.slice(0, 2)
                    .map(comment => {
                        let isUserComment = comment.commenter_email === loggedInUserEmail;
                        return `
                        <div class="comment" data-comment-id="${comment.id}" data-post-id="${post.id}">
                            ${isUserComment ? '<button class="delete-comment-btn" data-comment-id="' + comment.id + '" data-post-id="' + post.id + '">X</button>' : ""}
                            <span class="comment-date">${comment.created_at}</span>
                            <strong class="commenter-name user-info" data-email="${comment.commenter_email}" style="cursor:pointer;">
                                ${comment.commenter_name}
                            </strong>
                            <p class="comment-content">${comment.content}</p>
                        </div>
                    `;
                    }).join("");

                let hiddenCommentsHtml = sortedComments.slice(2).map(comment => {
                    let isUserComment = comment.commenter_email === loggedInUserEmail;
                    return `
                    <div class="comment" data-comment-id="${comment.id}" data-post-id="${post.id}">
                        ${isUserComment ? '<button class="delete-comment-btn" data-comment-id="' + comment.id + '" data-post-id="' + post.id + '">X</button>' : ""}
                        <span class="comment-date">${comment.created_at}</span>
                        <strong class="commenter-name user-info" data-email="${comment.commenter_email}" style="cursor:pointer;">
                            ${comment.commenter_name}
                        </strong>
                        <p class="comment-content">${comment.content}</p>
                    </div>
                `;
                }).join("");

                let postElement = `
                <div class="post-card" data-post-id="${post.id}">
                    ${isUserPost ? '<button class="delete-post-btn">X</button>' : ""}
                    <div class="post-header">
                        <h5 class="post-author user-info" data-email="${post.publisher_email}" style="cursor:pointer;">
                            ${post.publisher_name}
                        </h5>
                        <span class="post-date">${post.created_at}</span>
                    </div>
                    <p class="post-content">${post.content}</p>
                    <button class="btn btn-link toggle-comment">תגובה</button>
                    <div class="comment-box">
                        <input type="text" class="form-control comment-input" placeholder="כתוב תגובה...">
                        <button class="btn btn-primary mt-2 submit-comment">שלח</button>
                    </div>
    
                    <div class="comments-list">
                        ${commentsHtml}
                        <div class="hidden-comments" style="display: none;">
                            ${hiddenCommentsHtml}
                        </div>
                        ${post.comments.length > 2 ? `<button class="btn btn-link show-more-comments">ראה עוד</button>` : ""}
                    </div>
                </div>`;

                $("#postsContainer").append(postElement);
            });
        });
    }
    fetchPosts();

    $(document).on("click", ".commenter-name", function () {
        let userEmail = $(this).attr("data-email");
        if (!userEmail || userEmail === "undefined") {
            return;
        }

        $.get(`/users/info/${userEmail}`, function (user) {
            let roleText = user.role === "manager" || user.role === "co_manager" ? "בעל משק חקלאי" :
                user.role === "job_seeker" ? "מתנדב/מחפש עבודה" : "משתמש רגיל";

            let locationText = user.role === "manager" || user.role === "co_manager" ? `<p><strong>מקום המשק:</strong> ${user.location}</p>` : "";

            let userInfoHtml = `
                <div class="user-popup">
                    <h4>${user.first_name} ${user.last_name}</h4>
                    <p><strong>תפקיד:</strong> ${roleText}</p>
                    ${locationText}
                </div>
            `;

            $("#userInfoModal .modal-body").html(userInfoHtml);
            $("#userInfoModal").modal("show");
        }).fail(function () {
            console.error("⚠️ שגיאה בשליפת פרטי המשתמש.");
        });
    });

    $(document).on("click", ".user-info", function () {
        let userEmail = $(this).data("email");

        $.get(`/users/info/${userEmail}`, function (user) {
            let roleText = "משתמש רגיל";
            if (user.role === "manager" || user.role === "co_manager") {
                roleText = "בעל משק חקלאי";
            } else if (user.role === "job_seeker") {
                roleText = "מתנדב/מחפש עבודה";
            }

            let locationText = user.role === "manager" || user.role === "co_manager" ? `<p><strong>מקום המשק:</strong> ${user.location}</p>` : "";

            let userInfoHtml = `
            <div class="user-popup">
                <h4>${user.first_name} ${user.last_name}</h4>
                <hr class="section-divider">

                <p><strong>תפקיד:</strong> ${roleText}</p>
                ${locationText}
            </div>
        `;

            $("#userInfoModal .modal-body").html(userInfoHtml);
            $("#userInfoModal").modal("show");
        });
    });

    $(document).on("click", ".delete-comment-btn", function () {
        let commentId = $(this).data("comment-id");
        let postId = $(this).data("post-id");

        if (!commentId || !postId) {
            console.error("⚠️ חסר ID של התגובה או הפוסט.");
            return;
        }

        $("#alertTitle").text("אישור מחיקה");
        $("#alertMessage").text("אתה בטוח שברצונך למחוק את התגובה?");
        $("#customAlert").fadeIn();

        $(".alert-close").off("click").on("click", function () {
            $("#customAlert").fadeOut();
        });

        $("#alertConfirm").off("click").on("click", function () {
            $.ajax({
                url: `/posts/${postId}/comments/${commentId}`,
                type: "DELETE",
                success: function () {
                    fetchPosts();
                    $("#customAlert").fadeOut();
                },
                error: function () {
                    $("#alertTitle").text("שגיאה");
                    $("#alertMessage").text("אירעה שגיאה בעת מחיקת התגובה.");
                }
            });
        });
    });


    $(document).on("click", ".delete-post-btn", function () {
        let postElement = $(this).closest(".post-card");
        let postId = postElement.attr("data-post-id");

        $("#alertTitle").text("אישור מחיקה");
        $("#alertMessage").text("אתה בטוח שברצונך למחוק את הפוסט?");
        $("#customAlert").fadeIn();

        $(".alert-close").off("click").on("click", function () {
            $("#customAlert").fadeOut();
        });

        $("#alertConfirm").off("click").on("click", function () {
            $.ajax({
                url: `/posts/${postId}`,
                type: "DELETE",
                success: function () {
                    fetchPosts();
                    $("#customAlert").fadeOut();
                },
                error: function () {
                    $("#alertTitle").text("שגיאה");
                    $("#alertMessage").text("אירעה שגיאה בעת מחיקת הפוסט.");
                }
            });
        });
    });


    // פרסום פוסט
    $("#newPostForm").submit(function (event) {
        event.preventDefault();
        let content = $("#newPostContent").val().trim();
        if (!content) {
            showAlert("לא ניתן לפרסם פוסט ריק!");
            return;
        }

        $.ajax({
            url: "/posts/",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ "content": content }),
            success: function () {
                $("#newPostContent").val("");
                fetchPosts();
            },
            error: function () {
                showAlert("שגיאה בשליחת הפוסט.");
            }
        });
    });

    // פתיחה וסגירה של תיבת תגובות
    $(document).on("click", ".toggle-comment", function () {
        $(this).siblings(".comment-box").toggle();
    });

    // פרסום תגובה
    $(document).on("click", ".submit-comment", function () {
        let postElement = $(this).closest(".post-card");
        let postId = postElement.attr("data-post-id");
        let commentContent = postElement.find(".comment-input").val().trim();

        if (!commentContent) {
            showAlert("לא ניתן לשלוח תגובה ריקה!");
            return;
        }

        $.ajax({
            url: "/posts/comments",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                "post_id": postId,
                "content": commentContent
            }),
            success: function () {
                postElement.find(".comment-input").val("");
                fetchPosts();
            },
            error: function () {
                showAlert("שגיאה בשליחת התגובה.");
            }
        });
    });

    $(document).on("click", ".show-more-comments", function () {
        let postElement = $(this).closest(".post-card");
        let hiddenComments = postElement.find(".hidden-comments");

        hiddenComments.slideDown();
        $(this).remove();
    });

});
$(document).on("click", ".delete-comment-btn", function () {
    let commentId = $(this).data("comment-id");
    let postId = $(this).data("post-id");

    if (!commentId || !postId) {
        console.error("חסר ID של התגובה או הפוסט.");
        return;
    }

    $("#alertTitle").text("אישור מחיקה");
    $("#alertMessage").text("אתה בטוח שברצונך למחוק את התגובה?");
    $("#customAlert").fadeIn();

    $(".alert-close").off("click").on("click", function () {
        $("#customAlert").fadeOut();
    });

    $("#alertConfirm").off("click").on("click", function () {
        $.ajax({
            url: `/posts/${postId}/comments/${commentId}`,
            type: "DELETE",
            success: function () {
                fetchPosts();
                $("#customAlert").fadeOut();
            },
            error: function () {
                $("#alertTitle").text("שגיאה");
                $("#alertMessage").text("אירעה שגיאה בעת מחיקת התגובה.");
            }
        });
    });
});


document.addEventListener("click", function (event) {
    let navbarCollapse = document.getElementById("navbarCollapse");
    let menuButton = document.querySelector(".navbar-toggler");

    if (!navbarCollapse.contains(event.target) && !menuButton.contains(event.target)) {
        let isExpanded = menuButton.getAttribute("aria-expanded");

        if (isExpanded === "true") {
            menuButton.click();
        }
    }
});


// attendance

// attendance to worker
function loadAttendanceRecords() {
    fetch('/attendance/user_records')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById("attendanceTableBody");
            tableBody.innerHTML = ""; // איפוס הטבלה לפני מילוי מחדש

            let hasOpenCheckIn = false;

            if (data.attendance_records.length === 0) {
                tableBody.innerHTML = "<tr><td colspan='5'>אין נתונים זמינים</td></tr>";
                return;
            }

            data.attendance_records.forEach(record => {
                const checkInTime = record.check_in ? new Date(record.check_in) : null;
                const checkOutTime = record.check_out ? new Date(record.check_out) : null;

                let totalHours = "-";

                if (checkInTime && checkOutTime) {
                    totalHours = ((checkOutTime - checkInTime) / (1000 * 60 * 60)).toFixed(2);
                }

                if (checkInTime && !checkOutTime) {
                    hasOpenCheckIn = true;
                }

                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${record.first_name || '-'}</td>
                    <td>${record.last_name || '-'}</td>
                    <td>${checkInTime ? checkInTime.toLocaleString('he-IL') : '-'}</td>
                    <td>${checkOutTime ? checkOutTime.toLocaleString('he-IL') : '-'}</td>
                    <td>${totalHours}</td>
                `;
                tableBody.appendChild(row);
            });

            updateAttendanceButtons(hasOpenCheckIn);
        })
        .catch(error => {
            console.error("Error fetching attendance records:", error);
        });
}

function updateAttendanceButtons(hasOpenCheckIn) {
    const checkInButton = document.querySelector(".btn-check-in");
    const checkOutButton = document.querySelector(".btn-check-out");

    if (hasOpenCheckIn) {
        checkInButton.style.display = "none";
        checkOutButton.style.display = "inline-block";
    } else {
        checkInButton.style.display = "inline-block";
        checkOutButton.style.display = "none";
    }
}

function loadManagerAttendanceRecords() {
    fetch('/attendance/manager_records')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById("attendanceManagerTableBody");
            tableBody.innerHTML = ""; // איפוס הטבלה לפני מילוי מחדש

            if (data.attendance_records.length === 0) {
                tableBody.innerHTML = "<tr><td colspan='7'>אין נתונים זמינים</td></tr>";
                return;
            }
            data.attendance_records.forEach(record => {
                const checkInTime = record.check_in ? new Date(record.check_in).toISOString().slice(0, 16) : "";
                const checkOutTime = record.check_out ? new Date(record.check_out).toISOString().slice(0, 16) : "";

                let row = `
                    <tr>
                        <td>${record.first_name || '-'}</td>
                        <td>${record.last_name || '-'}</td>
                        <td>${record.email || '-'}</td>
                        <td>${record.check_in || '-'}</td>
                        <td>${record.check_out || '-'}</td>
                        <td>${record.total_hours || '-'}</td>
                        <td style="text-align: left;">
                            <button class="btn btn-warning edit-btn"
                                onclick="openEditModal('${record._id}' , '${checkInTime}', '${checkOutTime}')">
                                <i class="bi bi-pencil-square"></i> ערוך
                            </button>
                        </td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => console.error("Error fetching manager attendance records:", error));
}


function openAttendanceModal() {
    document.getElementById("attendanceModal").style.display = "block";
    fetchEmployeesList(); // טעינת רשימת העובדים למנהל
}

function closeAttendanceModal() {
    document.getElementById("attendanceModal").style.display = "none";
}

function fetchEmployeesList() {
    fetch('/attendance/employees_list')
        .then(response => response.json())
        .then(data => {
            const employeeSelect = document.getElementById("employeeSelect");
            employeeSelect.innerHTML = "";

            data.employees.forEach(emp => {
                const option = document.createElement("option");
                option.value = emp.email;
                option.textContent = `${emp.first_name} ${emp.last_name}`;
                employeeSelect.appendChild(option);
            });
        })
        .catch(error => console.error("Error fetching employees list:", error));
}

function submitManualAttendance() {
    const employeeEmail = document.getElementById("employeeSelect").value;
    const checkInTime = document.getElementById("manualCheckIn").value;
    const checkOutTime = document.getElementById("manualCheckOut").value;


    if (!employeeEmail || !checkInTime || !checkOutTime) {
        showAlert("שגיאה", "נא למלא את כל השדות.", {
            restoreForm: true,
            formId: "attendanceForm",
            modalId: "attendanceModal"
        });
        return;
    }

    fetch('/attendance/manual_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: employeeEmail,
            check_in: checkInTime,
            check_out: checkOutTime
        })
    })
        .then(response => response.json())
        .then(data => {
            showAlert("הצלחה", data.message, {
                isSuccess: true,
                closeModal: closeAttendanceModal,
                refreshPage: true
            });
            loadManagerAttendanceRecords();
        })
        .catch(error => {
            console.error("Error submitting manual attendance:", error);
            showAlert("שגיאה", "שגיאה בלתי צפויה בעת שליחת הדיווח.", {
                restoreForm: true,
                formId: "attendanceForm",
                modalId: "attendanceModal"
            });
        });
}

//חדש

function openEditModal(id) {
    fetch(`/attendance/get_record/${id}`)  // קריאה לשרת לפי ה-ID
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert("שגיאה", data.error, { restoreForm: false });
                return;
            }

            // הכנסת הנתונים מהשרת ישירות לחלונית
            document.getElementById('editAttendanceId').value = id;
            document.getElementById('editCheckIn').value = data.check_in.slice(0, 16);
            document.getElementById('editCheckOut').value = data.check_out.slice(0, 16);
            document.getElementById('editAttendanceModal').style.display = "block";
        })
        .catch(error => {
            console.error("Error fetching attendance record:", error);
            showAlert("שגיאה", "שגיאה בלתי צפויה בטעינת נתוני הנוכחות.", { restoreForm: false });
        });
}



function closeEditModal() {
    document.getElementById('editAttendanceModal').style.display = "none";
}

function saveAttendanceChanges() {
    let id = document.getElementById('editAttendanceId').value;
    let checkIn = document.getElementById('editCheckIn').value;
    let checkOut = document.getElementById('editCheckOut').value;

    if (!id) {
        showAlert("שגיאה", "ה-ID לא זוהה.", { restoreForm: false });
        return;
    }

    fetch('/attendance/update_attendance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, check_in: checkIn, check_out: checkOut })
    })
        .then(response => response.json())
        .then(data => {
            showAlert("הצלחה", data.message, {
                isSuccess: true,
                closeModal: closeEditModal,
                refreshPage: true
            });
        })
        .catch(error => {
            console.error("Error updating attendance:", error);
            showAlert("שגיאה", "שגיאה בלתי צפויה בעת עדכון הנתונים.", {
                restoreForm: true,
                formId: "editAttendanceForm",
                modalId: "editAttendanceModal"
            });
        });
}

//חדש
//filter Attendance employee
function filterAttendanceRecords() {
    const input = document.getElementById("searchEmployee").value.toLowerCase();
    const tableBody = document.getElementById("attendanceManagerTableBody");
    const rows = tableBody.getElementsByTagName("tr");

    for (let i = 0; i < rows.length; i++) {
        const firstName = rows[i].getElementsByTagName("td")[0]?.textContent.toLowerCase() || "";
        const lastName = rows[i].getElementsByTagName("td")[1]?.textContent.toLowerCase() || "";

        if (firstName.includes(input) || lastName.includes(input)) {
            rows[i].style.display = "";
        } else {
            rows[i].style.display = "none";
        }
    }
}

function goBack() {
    if (document.referrer) {
        window.history.back();
    } else {
        window.location.href = "{{ url_for('home') }}";
    }
}


async function loadCropsForUpdate(category, selectedCrop = null) {
    const cropSelect = document.getElementById("crop");
    const cropDiv = document.getElementById("cropDiv");

    if (!category || category === "none") {
        cropDiv.style.display = "none";
        cropSelect.innerHTML = '<option value="none">ללא</option>';
        return;
    }

    try {
        const response = await fetch("/supply/available_crops");
        if (!response.ok) throw new Error("שגיאה בטעינת הגידולים");

        const crops = await response.json();

        cropSelect.innerHTML = '<option value="none">ללא</option>';
        crops.forEach(crop => {
            let option = document.createElement("option");
            option.value = crop.name;
            option.textContent = `${crop.name} (זמין: ${crop.quantity} ק"ג)`;
            option.dataset.quantity = crop.quantity;
            cropSelect.appendChild(option);
        });

        cropDiv.style.display = crops.length > 0 ? "block" : "none";

        if (selectedCrop) {
            cropSelect.value = selectedCrop;
        }
    } catch (error) {
        console.error(" שגיאה בטעינת הגידולים:", error);
    }
}

async function updateCropCategory() {
    let cropSelect = document.getElementById('crop');
    let cropCategoryField = document.getElementById('cropCategory');

    if (!cropSelect || !cropCategoryField) {
        console.error(" שגיאה: אחד השדות לא נמצא ב-DOM");
        return;
    }

    let selectedCrop = cropSelect.value;
    if (selectedCrop === "none") {
        cropCategoryField.value = "none";
        cropCategoryField.setAttribute("data-category", "none");
        return;
    }

    try {
        const response = await fetch("/static/data/crops_data.json");
        if (!response.ok) throw new Error(" שגיאה בטעינת הקובץ crop_data.json");

        const data = await response.json();
        let foundCategory = "none";
        data.forEach(entry => {
            if (entry.values.includes(selectedCrop)) {
                foundCategory = entry.category;
            }
        });
        if (cropCategoryField) {
            cropCategoryField.value = foundCategory;
            cropCategoryField.setAttribute("data-category", foundCategory);
        } else {
            console.error(" שגיאה: cropCategoryField עדיין לא נמצא ב-DOM.");
        }

    } catch (error) {
        console.error(" שגיאה בטעינת קטגוריית הגידול:", error);
    }
}



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
        productName = document.getElementById("productName").value;
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
            <select id="productName" required>
                <option value="">בחר גידול</option>
            </select>
        `;

        const productNameSelect = document.getElementById("productName");

        try {
            const response = await fetch("/static/data/crops_data.json");
            const data = await response.json();

            // מעבר על כל הקטגוריות והוספתן לרשימה
            data.forEach(cat => {
                const optgroup = document.createElement("optgroup");
                optgroup.label = cat.category; // שם הקטגוריה (פירות, ירקות, גידולי שדה וכו')

                cat.values.forEach(crop => {
                    const option = document.createElement("option");
                    option.value = crop;
                    option.textContent = crop;
                    optgroup.appendChild(option);
                });

                productNameSelect.appendChild(optgroup);
            });

        } catch (error) {
            console.error("שגיאה בטעינת רשימת הגידולים:", error);
            productNameSelect.innerHTML = '<option value="">שגיאה בטעינה</option>';
        }
    } else {
        // אם מדובר ב"מוצר כללי" או "הדברה", נציג תיבת טקסט
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

// הכנסת מחיר לקו״ב
function openWaterPriceModal() {
    document.getElementById("waterPriceModal").style.display = "flex";
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

    try {
        const response = await fetch("/expenses/water/add", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                price: parseFloat(waterPrice),
                date: waterDate,
            }),
        });

        const result = await response.json();
        if (response.ok) {
            showAlert("הצלחה", " התעריף נשמר בהצלחה!", false);
            closeWaterPriceModal();
        } else {
            showAlert("שגיאה", result.error, false);
        }
    } catch (error) {
        showAlert("שגיאה", "שגיאה בשליחת הנתונים לשרת.", false);
    }
}

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

// שמירת המחיר בבסיס הנתונים
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

/* Vehicles */
$(document).ready(function () {
    $("#openVehicleModal").click(function () {
        $("#addVehicleForm")[0].reset();
        $("#addVehicleModal").modal("show");
    });

    function formatDate(dateString) {
        if (!dateString) return "";
        let date = new Date(dateString);
        let day = String(date.getDate()).padStart(2, '0');
        let month = String(date.getMonth() + 1).padStart(2, '0');
        let year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }

    function formatDateForInput(dateString) {
        if (!dateString) return "";
        let date = new Date(dateString);
        let day = String(date.getDate()).padStart(2, '0');
        let month = String(date.getMonth() + 1).padStart(2, '0');
        let year = date.getFullYear();
        return `${year}-${month}-${day}`;
    }

    function loadVehicles(searchQuery = "") {
        $.get("/vehicles/get", function (data) {
            $("#vehicleTable").empty();
            data.forEach(vehicle => {
                const vehicleNumber = String(vehicle.vehicle_number);
                const vehicleType = String(vehicle.vehicle_type);

                if (searchQuery === "" || vehicleNumber.includes(searchQuery) || vehicleType.includes(searchQuery)) {
                    $("#vehicleTable").append(`
                        <tr id="row-${vehicle._id}">
                            <td>${vehicle.vehicle_number}</td>
                            <td>${vehicle.vehicle_type}</td>
                            <td>${formatDate(vehicle.test_date)}</td>
                            <td>${vehicle.test_cost}</td>
                            <td>${formatDate(vehicle.insurance_date) || ''}</td>
                            <td>${vehicle.insurance_cost || ''}</td>
                            <td>${formatDate(vehicle.last_service_date)}</td>
                            <td>${vehicle.service_cost}</td>
                            <td>${vehicle.authorized_drivers}</td>
                            <td class="action-buttons">
                                <button class="btn btn-warning btn-sm edit-btn action-btn" data-id="${vehicle._id}">ערוך</button>
                                <button class="btn btn-danger btn-sm delete-btn action-btn" data-id="${vehicle._id}">מחק</button>
                            </td>
                        </tr>
                    `);
                }
            });


            $(".delete-btn").click(function () {
                let vehicle_id = $(this).data("id");
                deleteVehicle(vehicle_id);
            });


            $(".edit-btn").click(function () {
                let vehicle_id = $(this).data("id");
                editVehicle(vehicle_id);
            });
        });
    }

    loadVehicles();

    $("#searchInput").on("input", function () {
        let searchQuery = $(this).val().trim();
        loadVehicles(searchQuery);
    });

    $("#addVehicleForm").submit(function (event) {
        event.preventDefault();

        const newVehicle = {
            vehicle_number: $("#addVehicleNumber").val(),
            vehicle_type: $("#addVehicleType").val(),
            test_date: $("#addTestDate").val(),
            test_cost: $("#addTestCost").val(),
            insurance_date: $("#addInsuranceDate").val(),
            insurance_cost: $("#addInsuranceCost").val(),
            last_service_date: $("#addLastServiceDate").val(),
            service_cost: $("#addServiceCost").val(),
            authorized_drivers: $("#addAuthorizedDrivers").val()
        };

        $.ajax({
            url: "/vehicles/add",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(newVehicle),
            success: function () {
                loadVehicles();
                $("#addVehicleModal").modal("hide");
                $("#addVehicleForm")[0].reset();
            },
            error: function (xhr) {
                console.error(" Error:", xhr.responseText);
            }
        });
    });

    function deleteVehicle(vehicle_id) {
        $.ajax({
            url: `/vehicles/delete/${vehicle_id}`,
            type: "DELETE",
            success: function () {
                $(`#row-${vehicle_id}`).remove();
            }
        });
    }

    function editVehicle(vehicle_id) {
        $.get(`/vehicles/get`, function (data) {
            let vehicle = data.find(v => v._id === vehicle_id);
            if (!vehicle) return;

            $("#editVehicleNumber").val(vehicle.vehicle_number).prop("readonly", true);
            $("#editVehicleType").val(vehicle.vehicle_type);
            $("#editTestDate").val(formatDateForInput(vehicle.test_date));
            $("#editTestCost").val(vehicle.test_cost);
            $("#editInsuranceDate").val(formatDateForInput(vehicle.insurance_date));
            $("#editInsuranceCost").val(vehicle.insurance_cost);
            $("#editLastServiceDate").val(formatDateForInput(vehicle.last_service_date));
            $("#editServiceCost").val(vehicle.service_cost);
            $("#editAuthorizedDrivers").val(vehicle.authorized_drivers);

            $("#editVehicleModal").modal("show");

            $("#editVehicleForm").off("submit").on("submit", function (event) {
                event.preventDefault();
                $.ajax({
                    url: `/vehicles/update/${vehicle_id}`,
                    type: "PUT",
                    contentType: "application/json",
                    data: JSON.stringify({
                        vehicle_type: $("#editVehicleType").val(),
                        test_date: $("#editTestDate").val(),
                        test_cost: $("#editTestCost").val(),
                        insurance_date: $("#editInsuranceDate").val(),
                        insurance_cost: $("#editInsuranceCost").val(),
                        last_service_date: $("#editLastServiceDate").val(),
                        service_cost: $("#editServiceCost").val(),
                        authorized_drivers: $("#editAuthorizedDrivers").val()
                    }),
                    success: function () {
                        loadVehicles();
                        $("#editVehicleModal").modal("hide");
                    }
                });
            });
        });
    }
});

/* recommendation irrgration*/
document.getElementById("getIrrigationButton").addEventListener("click", async function () {
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
            body: JSON.stringify({
                crop_type: cropType
            })
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

function closeIrrigationModal() {
    document.getElementById("irrigationRecommendationModal").style.display = "none";
}