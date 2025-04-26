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

    (function () {
        const script = document.createElement("script");
        script.src = "https://cdn.enable.co.il/licenses/enable-L407982omp8qahbj-0425-69879/init.js";
        script.async = true;
        document.head.appendChild(script);
    })();


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
    if (!badge) return;

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
    const notificationsList = document.getElementById("notifications-list");

    if (!modal || !badge || !notificationsList) return;

    if (modal.style.display === "none" || modal.style.display === "") {
        modal.style.display = "block";
        badge.style.display = "none";

        fetch("/users/mark_notifications_seen", { method: "POST" })
            .catch(error => console.error("Error marking notifications as seen:", error));

        fetch("/users/get_notifications")
            .then(response => response.json())
            .then(data => {
                if (data.notifications.length > 0) {
                    notificationsList.innerHTML = data.notifications
                        .map(notification => `
                            <div class="notification-item">
                                <p><strong>תוכן:</strong> ${notification.content}</p>
                                ${notification.employee_email ? `<p><strong>מייל:</strong> ${notification.employee_email}</p>` : ""}
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
    if (modal) {
        modal.style.display = "none";
        document.removeEventListener("click", closeOnOutsideClick);
    }
}

function closeOnOutsideClick(event) {
    const modal = document.getElementById("notificationModal");
    const notificationIcon = document.getElementById("notificationIcon");
    if (modal && notificationIcon && !modal.contains(event.target) && event.target !== notificationIcon) {
        closeNotifications();
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    // --- התראות ---
    const badge = document.getElementById("notificationBadge");
    if (badge) {
        try {
            const notificationsResponse = await fetch("/users/get_notifications");
            const notificationsData = await notificationsResponse.json();
            showNotificationBadge(notificationsData.new_notifications_count);
        } catch (error) {
            console.error("Error fetching notifications:", error);
        }
    }


    const kosherCheckbox = document.getElementById("kosherRequiredUpdate");
    if (kosherCheckbox) {
        kosherCheckbox.addEventListener("change", function () {
            const fileDiv = document.getElementById("kosherFileDivUpdate");
            fileDiv.style.display = this.checked ? "block" : "none";
        });
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

//update irrigation
let selectedWaterTypeForIrrigation = null;

async function checkAndOpenIrrigationModal(plotId) {
    try {
        const response = await fetch(`/Plots/get_plot_info/${plotId}`);
        if (!response.ok) {
            throw new Error('שגיאה בשליפת פרטי חלקה.');
        }
        const data = await response.json();
        const irrigationType = data.irrigation_water_type || "none";

        if (irrigationType === "משולב") {
            const modal = document.getElementById('chooseWaterTypeModal');
            modal.setAttribute('data-plot-id', plotId);
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        } else {
            selectedWaterTypeForIrrigation = irrigationType;
            const modal = document.getElementById('irrigationModal');
            modal.setAttribute('data-plot-id', plotId);
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    } catch (error) {
        console.error('שגיאה בשליפת מידע:', error);
    }
}

function closeChooseWaterTypeModal() {
    const modal = document.getElementById('chooseWaterTypeModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

function selectWaterType(type) {
    selectedWaterTypeForIrrigation = type;
    closeChooseWaterTypeModal();

    const plotId = document.getElementById('chooseWaterTypeModal').getAttribute('data-plot-id');
    const modal = document.getElementById('irrigationModal');
    modal.setAttribute('data-plot-id', plotId);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}


function closeIrrigationModal() {
    const modal = document.getElementById('irrigationModal');

    if (modal) {
        modal.style.display = 'none';
        document.getElementById('irrigationAmount').value = '';
    } else {
        console.warn("❌ לא נמצא אלמנט עם id irrigationModal");
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
            body: JSON.stringify({
                irrigation_amount: parseFloat(irrigationAmount),
                irrigation_water_type: selectedWaterTypeForIrrigation || "none"
            })
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
    cropSelect.innerHTML = '<option value="none">ללא</option>'; // reset
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
    const irrigationWaterTypeField = document.getElementById("irrigationWaterTypeUpdate");
    const sowDateField = document.getElementById("sowDate");
    const quantityPlantedField = document.getElementById("quantityPlanted");
    const kosherCheckbox = document.getElementById("kosherRequiredUpdate");
    const kosherFileInput = document.getElementById("kosherCertificateUpdate");

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
    const formData = new FormData();
    formData.append("crop_category", cropCategory);
    formData.append("crop", crop);
    formData.append("sow_date", sowDate);
    formData.append("quantity_planted", quantityPlanted);
    formData.append("irrigation_water_type", irrigationWaterTypeField.value || "none");

    if (kosherCheckbox.checked) {
        formData.append("kosher_required", "on");
        if (kosherFileInput.files.length > 0) {
            formData.append("kosher_certificate", kosherFileInput.files[0]);
        }
    }

    try {
        const response = await fetch(`/Plots/update_plot/${plotId}`, {
            method: 'POST',
            body: formData
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
            showAlert('החלקה הועברה לארכיון בהצלחה!', '', {
                isSuccess: true,
                redirectUrl: '/Plots/track_greenhouse'
            });
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
    //reset
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

        cropDiv.style.display = crops.length >= 1 ? "block" : "none";


    } catch (error) {
        console.error("שגיאה בטעינת רשימת הגידולים:", error);
    }
    document.getElementById('crop').addEventListener('change', function () {
        updateCropCategory();
        const selectedCrop = this.value;
        const sowDateDiv = document.getElementById('sowDateDiv');
        const quantityPlantedDiv = document.getElementById('quantityPlantedDiv');
        const cropCategoryField = document.getElementById('cropCategory');
        const irrigationWaterTypeDiv = document.getElementById('irrigationWaterTypeDiv'); // חדש

        if (selectedCrop === "none") {
            sowDateDiv.style.display = 'none';
            quantityPlantedDiv.style.display = 'none';
            cropCategoryField.value = "none";
            irrigationWaterTypeDiv.style.display = 'none';

        } else {
            sowDateDiv.style.display = 'block';
            quantityPlantedDiv.style.display = 'block';
            irrigationWaterTypeDiv.style.display = 'block';

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
    const form = document.getElementById("plotForm");

    const plotTypeInput = document.getElementById("plotType");
    const plotNameField = document.getElementById("plotName");
    const metersField = document.getElementById("squareMeters");
    const cropField = document.getElementById("crop");
    const cropCategoryField = document.getElementById("cropCategory");
    const sowDateField = document.getElementById("sowDate");
    const quantityPlantedField = document.getElementById("quantityPlanted");
    const irrigationWaterTypeField = document.getElementById("irrigationWaterType");

    const kosherCheckbox = document.getElementById("kosherRequired");
    const kosherFileInput = document.getElementById("kosherCertificate");

    if (!plotTypeInput.value.trim()) {
        showAlert("שגיאה", "סוג החלקה הוא שדה חובה.");
        return;
    }

    if (!plotNameField.value.trim()) {
        showAlert("שגיאה", "שם החלקה הוא שדה חובה.");
        return;
    }

    if (!metersField.value.trim() || parseFloat(metersField.value) <= 0) {
        showAlert("שגיאה", "יש להזין גודל חלקה חיובי (גדול מ-0).");
        return;
    }

    const crop = cropField.value !== "none" ? cropField.value : "none";
    const cropCategory = crop !== "none" ? cropCategoryField.value : "none";
    const sowDate = sowDateField && sowDateField.value ? sowDateField.value : "";
    const quantityPlanted = quantityPlantedField && quantityPlantedField.value ? parseFloat(quantityPlantedField.value) : "";

    const today = new Date().toISOString().split("T")[0];
    if (sowDate && sowDate > today) {
        showAlert("שגיאה", "לא ניתן להזין תאריך עתידי לזריעה.");
        return;
    }

    // הכנת הנתונים לשליחה
    const formData = new FormData();
    formData.append("plot_type", plotTypeInput.value.trim());
    formData.append("plot_name", plotNameField.value.trim());
    formData.append("square_meters", metersField.value);
    formData.append("crop_category", cropCategory);
    formData.append("crop", crop);
    formData.append("sow_date", sowDate);
    formData.append("quantity_planted", quantityPlanted);
    formData.append("irrigation_water_type", irrigationWaterTypeField.value || "none");

    if (kosherCheckbox.checked) {
        formData.append("kosher_required", "on");
        if (kosherFileInput.files.length > 0) {
            formData.append("kosher_certificate", kosherFileInput.files[0]);
        }
    }

    try {
        const response = await fetch("/Plots/save_plot", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            showAlert("הצלחה", "החלקה נשמרה בהצלחה!", {
                isSuccess: true,
                redirectUrl: "/Plots/track_greenhouse"
            });
        } else {
            const errorData = await response.json();
            showAlert("שגיאה", errorData.error || "שגיאה בלתי צפויה בשמירה.");
        }
    } catch (error) {
        console.error("שגיאה:", error);
        showAlert("שגיאה", "שגיאה בלתי צפויה בשמירה.");
    }
}
const cropElement = document.getElementById("crop");
if (cropElement) {
    cropElement.addEventListener("change", () => {
        const cropValue = cropElement.value;
        const kosherDiv = document.getElementById("kosherDiv");
        if (cropValue !== "none") {
            kosherDiv.style.display = "block";
        } else {
            kosherDiv.style.display = "none";
            const kosherRequiredCheckbox = document.getElementById("kosherRequired");
            if (kosherRequiredCheckbox) {
                kosherRequiredCheckbox.checked = false;
            }
            const kosherFileDiv = document.getElementById("kosherFileDiv");
            if (kosherFileDiv) {
                kosherFileDiv.style.display = "none";
            }
        }
    });
}

const kosherRequiredCheckbox = document.getElementById("kosherRequired");
if (kosherRequiredCheckbox) {
    kosherRequiredCheckbox.addEventListener("change", function () {
        const fileDiv = document.getElementById("kosherFileDiv");
        if (fileDiv) {
            fileDiv.style.display = this.checked ? "block" : "none";
        }
    });
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
