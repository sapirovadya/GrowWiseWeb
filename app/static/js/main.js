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
        badge.style.display = "flex"; // הצגת העיגול האדום
        badge.textContent = newNotificationsCount; // הצגת מספר ההתראות
    } else {
        badge.style.display = "none"; // הסתרת העיגול האדום
    }
}


function toggleNotifications() {
    const modal = document.getElementById("notificationModal");
    const badge = document.getElementById("notificationBadge");

    if (modal.style.display === "none" || modal.style.display === "") {
        modal.style.display = "block";

        // הסתרת האייקון האדום (בזמן פתיחת ההתראות)
        badge.style.display = "none";

        // סימון התראות כנצפות בשרת
        fetch("/users/mark_notifications_seen", { method: "POST" })
            .catch(error => console.error("Error marking notifications as seen:", error));

        // טעינת התראות
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

    // הסרת המאזין
    document.removeEventListener("click", closeOnOutsideClick);
}

function closeOnOutsideClick(event) {
    const modal = document.getElementById("notificationModal");
    const notificationIcon = document.getElementById("notificationIcon");

    // בדיקה אם הלחיצה התבצעה מחוץ לחלון ומחוץ לאייקון
    if (!modal.contains(event.target) && event.target !== notificationIcon) {
        closeNotifications();
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    // טעינת התראות
    try {
        const notificationsResponse = await fetch("/users/get_notifications");
        const notificationsData = await notificationsResponse.json();

        showNotificationBadge(notificationsData.new_notifications_count); // עדכון העיגול האדום עם מספר ההתראות החדשות
    } catch (error) {
        console.error("Error fetching notifications:", error);
    }
});


/* Logout */

function logout() {
    fetch('/users/logout', {
        method: 'POST',
        credentials: 'same-origin'  // שולח את ה-cookies של ה-session
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;  // מפנה לדף הבית
        } else {
            showAlert('שגיאה במהלך הניתוק.');
        }
    }).catch(error => {
        console.error('שגיאה בלתי צפויה:', error);
    });
}

// catagory of crop
async function loadCategories() {
    const categorySelect = document.getElementById('cropCategory');
    categorySelect.innerHTML = '<option value="none">ללא</option>'; // איפוס הרשימה

    try {
        // שליפת הקטגוריות מהשרת
        const response = await fetch('/Plots/get_crop_categories');
        if (!response.ok) {
            throw new Error(`שגיאה בטעינת קטגוריות: ${response.status}`);
        }

        const data = await response.json();

        // הוספת קטגוריות לשדה הבחירה
        data.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categorySelect.appendChild(option);
        });

        // הוספת אירוע שינוי קטגוריה
        categorySelect.addEventListener('change', () => {
            const selectedCategory = categorySelect.value;
            loadCrops(selectedCategory); // טעינת הגידולים לפי הקטגוריה שנבחרה
        });

    } catch (error) {
        console.error('שגיאה בטעינת קטגוריות:', error);
        showAlert('שגיאה', 'שגיאה בעת טעינת הקטגוריות.', { restoreForm: false }); // הצגת הודעה למשתמש
    }
}
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

    // בדיקת תקינות הקלט
    if (!irrigationAmount || isNaN(irrigationAmount) || irrigationAmount <= 0) {
        showAlert('שגיאה', 'נא להזין כמות השקיה תקינה.', {
            restoreForm: true,
            formId: 'irrigationForm', // וודא שזה ה-ID של הטופס
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
                closeModal: closeIrrigationModal,
                refreshPage: true
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

async function openUpdateModal(plotId) {
    document.getElementById('updateModal').setAttribute('data-plot-id', plotId);
    document.getElementById('updateModal').style.display = 'flex';

    // טען את רשימת הקטגוריות
    await loadCategories();
}

function resetCropField() {
    const cropSelect = document.getElementById('crop');
    const cropDiv = document.getElementById('cropDiv');
    cropDiv.style.display = 'none';
    cropSelect.innerHTML = '<option value="none">ללא</option>'; // איפוס
}

async function submitUpdate() {
    const cropCategory = document.getElementById('cropCategory').value;
    const crop = document.getElementById('crop').value;
    const sowDate = document.getElementById('sowDate').value;
    const quantity_Planted = document.getElementById('quantityPlanted').value;
    const plotId = document.getElementById('updateModal').getAttribute('data-plot-id');

    // בדיקת תקינות הקלט
    if (!quantity_Planted || !sowDate || crop === "none" || cropCategory === "none") {
        const errorMessage =
            !cropCategory || cropCategory === "none" ? 'נא בחר סוג גידול.' :
                !crop || crop === "none" ? 'נא בחר גידול.' :
                    !sowDate ? 'נא בחר את תאריך הזריעה.' :
                        !quantity_Planted ? 'נא בחר את הכמות שזרעת.' :
                            'נא למלא את כל השדות.';

        showAlert('שגיאה', errorMessage, {
            restoreForm: true,
            formId: 'updatePlotForm',
            modalId: 'updateModal'
        });
        return;
    }

    const payload = {
        crop_category: cropCategory,
        crop: crop,
        sow_date: sowDate,
        quantity_planted: quantity_Planted
    };

    try {
        const response = await fetch(`/Plots/update_plot/${plotId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showAlert('הצלחה', 'פרטי החלקה עודכנו בהצלחה!', {
                isSuccess: true,
                closeModal: closeUpdateModal,
                refreshPage: true
            });
        } else {
            const error = await response.json();
            showAlert('שגיאה', `שגיאה: ${error.error}`, {
                restoreForm: true,
                formId: 'updatePlotForm',
                modalId: 'updateModal'
            });
        }
    } catch (error) {
        console.error('שגיאה בעת עדכון:', error);
        showAlert('שגיאה', 'שגיאה בעת שליחת הבקשה לשרת.', {
            restoreForm: true,
            formId: 'updatePlotForm',
            modalId: 'updateModal'
        });
    }
}


function closeUpdateModal() {
    const modal = document.getElementById('updateModal');
    modal.style.display = 'none';
    document.getElementById('updatePlotForm').reset();
}

// תחזית גדילה
function closeGrowthForecastModal() {
    const modal = document.getElementById("growthForecastModal");
    modal.style.display = "none";
}

// archive model
function openArchiveModal(plotId) {
    selectedPlotId = plotId; // שמירת ה-ID של החלקה שנבחרה
    const modal = document.getElementById('archiveModal');
    modal.style.display = 'flex';
}


function closeArchiveModal() {
    const modal = document.getElementById('archiveModal');
    modal.style.display = 'none';
    document.getElementById('cropYield').value = ''; // איפוס תיבת הטקסט
}

async function finalizePlot() {
    const cropYield = document.getElementById('cropYield').value;

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
                harvest_date: new Date().toISOString().split('T')[0], // תאריך של היום
                crop_yield: parseFloat(cropYield)
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
function openPlotForm(type) {
    const plotTypeInput = document.getElementById('plotType');
    const selectTypeModal = document.getElementById('selectTypeModal');
    const plotFormModal = document.getElementById('plotFormModal');

    plotTypeInput.value = type;
    selectTypeModal.style.display = 'none';
    plotFormModal.style.display = 'flex';
    loadCategories();
}


async function savePlot() {
    const plotName = document.getElementById('plotName').value.trim();
    const length = document.getElementById('length').value.trim();
    const width = document.getElementById('width').value.trim();
    const cropCategory = document.getElementById('cropCategory').value;
    const crop = document.getElementById('crop').value;
    const sowDate = document.getElementById('sowDate').value;
    const quantityPlanted = document.getElementById('quantityPlanted').value.trim();

    if (!plotName || !length || !width) {
        showAlert("שגיאה", 'יש למלא את השדות: שם החלקה, אורך ורוחב.', {
            restoreForm: true,
            formId: "plotForm",
            modalId: "plotFormModal"
        });
        return;
    }
    if (length <= 0 || width <= 0) {
        showAlert("שגיאה", 'אורך ורוחב חייבים להיות גדולים מ-0.', {
            restoreForm: true,
            formId: "plotForm",
            modalId: "plotFormModal"
        });
        return;
    }

    if (cropCategory !== 'none' && (!crop || !sowDate)) {
        showAlert("שגיאה", 'נא למלא את השדות גידול ותאריך זריעה.', {
            restoreForm: true,
            formId: "plotForm",
            modalId: "plotFormModal"
        });
        return;
    }
    if (cropCategory !== 'none' && crop !== 'none' && sowDate) {
        if (!quantityPlanted || quantityPlanted <= 0) {
            showAlert("שגיאה", 'נא למלא כמות זרעית גדולה מ-0.', {
                restoreForm: true,
                formId: "plotForm",
                modalId: "plotFormModal"
            });
            return;
        }
    }

    const formData = new FormData(document.getElementById('plotForm'));
    const response = await fetch('/Plots/save_plot', {
        method: 'POST',
        body: formData
    });

    if (response.ok) {
        showAlert("הצלחה", 'החלקה נשמרה בהצלחה!', {
            isSuccess: true,
            redirectUrl: "/Plots/track_greenhouse" // הפניה לדף הרצוי (ניתן לשנות)
        });
    } else {
        const errorData = await response.json();
        showAlert("שגיאה", errorData.error, {
            restoreForm: true,
            formId: "plotForm",
            modalId: "plotFormModal"
        });
    }
}

// plots view
const plots = []; // מערך של החלקות שנטען מבסיס הנתונים

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
        showAlert(error.message); // הצגת השגיאה למשתמש
    }
}

let currentPlotIndex = 0;


function renderMultipleView() {
    const container = document.getElementById("plotsContainer");
    container.innerHTML = ""; // איפוס
    if (plots.length === 0) {
        container.innerHTML = "<p style='text-align:center;'>אין חלקות פעילות להצגה.</p>";
        return;
    }

    plots.forEach(plot => {
        const plotContainer = document.createElement("div");
        plotContainer.classList.add("plot-container");
        plotContainer.style.cursor = "pointer"; // הפיכת האלמנט ללחיץ

        // הוספת אירוע לחיצה
        plotContainer.onclick = () => {
            window.location.href = `/Plots/plot_details?id=${plot._id}`; // העברה לדף חדש עם ה-ID
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

// דפדוף בין החלקות בפריסה בודדת

function updateSingleView() {
    const singleView = document.getElementById("singleView");

    if (plots.length === 0) {
        singleView.innerHTML = "<p style='text-align:center;'>אין חלקות פעילות להצגה.</p>";
        return;
    }
    const plot = plots[currentPlotIndex];

    // עדכון שם החלקה
    document.getElementById("plotTitle").textContent = plot.plot_name;

    // עדכון תמונת החלקה לפי סוג
    document.getElementById("plotImage").src =
        plot.plot_type === "חלקה" ? "/static/img/land.png" : "/static/img/green_house.png";

    // עדכון קישור התמונה
    const plotDetailsLink = document.getElementById("plotDetailsLink");
    plotDetailsLink.href = `/Plots/plot_details?id=${plot._id}`;


    // עדכון השדות לפי הערכים מהבסיס נתונים
    document.getElementById("plottype").textContent = plot.plot_type || "לא זמין";

    document.getElementById("plotLength").textContent = plot.length || "לא זמין";
    document.getElementById("plotWidth").textContent = plot.width || "לא זמין";

    // בדיקה עבור plotCrop
    document.getElementById("plotCrop").textContent =
        plot.crop === "none" ? " טרם נבחר גידול" : (plot.crop || "לא זמין");

    // בדיקה עבור sowdate
    document.getElementById("sowdate").textContent =
        plot.sow_date === "" ? "טרם בוצעה זריעה" : (plot.sow_date || "לא זמין");

    // בדיקה עבור lastIrrigationDate
    document.getElementById("lastIrrigationDate").textContent =
        plot.last_irrigation_date == null ? "טרם בוצעה השקייה" : plot.last_irrigation_date;

    // בדיקה עבור totalIrrigationAmount
    document.getElementById("totalIrrigationAmount").textContent =
        plot.total_irrigation_amount == null ? "0" : plot.total_irrigation_amount;
}

function closePlotForm() {
    // הסתרת החלון
    const plotFormModal = document.getElementById('plotFormModal');
    plotFormModal.style.display = 'none';

    // איפוס כל השדות
    const form = document.getElementById('plotForm');
    form.reset();

    // איפוס שדות נוספים אם מוסתרים
    document.getElementById('cropDiv').style.display = 'none';
    document.getElementById('sowDateDiv').style.display = 'none';
    document.getElementById('quantityPlantedDiv').style.display = 'none';
}


// profile 
function saveChanges() {
    const firstName = document.getElementById("firstName").value.trim();
    const lastName = document.getElementById("lastName").value.trim();
    const email = document.getElementById("email").value.trim();

    // בדיקות שדה שם פרטי
    if (!firstName) {
        showAlert("שגיאה", "נא להזין שם פרטי.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    if (/[^a-zA-Zא-ת\s]/.test(firstName)) {
        showAlert("שגיאה", "שם פרטי יכול להכיל רק אותיות בעברית או באנגלית.", { restoreForm: true, formId: "profileForm" });
        return;
    }

    // בדיקות שדה שם משפחה
    if (!lastName) {
        showAlert("שגיאה", "נא להזין שם משפחה.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    if (/[^a-zA-Zא-ת\s]/.test(lastName)) {
        showAlert("שגיאה", "שם משפחה יכול להכיל רק אותיות בעברית או באנגלית.", { restoreForm: true, formId: "profileForm" });
        return;
    }

    // בדיקות אימייל
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!email) {
        showAlert("שגיאה", "נא להזין כתובת אימייל.", { restoreForm: true, formId: "profileForm" });
        return;
    }
    if (!emailPattern.test(email)) {
        showAlert("שגיאה", "כתובת האימייל אינה תקינה. יש להזין כתובת חוקית.", { restoreForm: true, formId: "profileForm" });
        return;
    }

    // אם הכל תקין - שליחת הטופס לשרת
    const formData = new FormData(document.getElementById("profileForm"));

    fetch('/users/save_profile', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert("הצלחה", data.message, { refreshPage: true }); // הצלחה - עדכון הדף
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
let currentEmployeeEmail = ""; // משתנה גלובלי לשמירת האימייל של העובד הנבחר
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
    // ניקוי כפתורים
    actions.innerHTML = "";
    // הוספת כפתורי אישור ודחייה אם המשתמש לא מאושר
    if (isApproved == 0) {
        actions.innerHTML = `
            <button class="btn btn-success btn-lg" onclick="approveUser('${id}')">אשר</button>
            <button class="btn btn-danger btn-lg ms-3" onclick="rejectUser('${id}')">דחה</button>
        `;
    }
    // הצגת המודל
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

    // בדיקה אם הלחיצה התבצעה מחוץ למודל של משימה
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

    // טיפול בכפתור אישור
    yesButton.onclick = function () {
        confirmBox.style.display = "none";
        if (typeof onConfirm === "function") { // בדיקה שהפרמטר הוא פונקציה
            onConfirm();
        }
    };

    // טיפול בכפתור ביטול
    noButton.onclick = function () {
        confirmBox.style.display = "none";
    };
}

// task form in my team

// פותח את חלון המשימות
function openTaskModal(employeeEmail, employeeName) {
    currentEmployeeEmail = employeeEmail; // שמירת האימייל של העובד הנבחר
    const modal = document.getElementById("taskModal");
    modal.style.display = "flex"; // הצגת החלון
    // איפוס שדות הטופס
    document.getElementById("taskName").value = "";
    document.getElementById("taskContent").value = "";
    document.getElementById("dueDate").value = "";
    // מאזין ללחיצה מחוץ לחלון
    document.addEventListener("mousedown", closeOnOutsideClick);
}
// סוגר את חלון המשימות
function closeTaskModal() {
    const modal = document.getElementById("taskModal");
    modal.style.display = "none"; // הסתרת החלון
    // הסרת המאזין ללחיצה מחוץ לחלון
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

