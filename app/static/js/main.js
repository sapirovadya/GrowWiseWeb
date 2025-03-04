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
async function loadCategories() {
    const categorySelect = document.getElementById('cropCategory');
    categorySelect.innerHTML = '<option value="none">ללא</option>';

    try {
        const response = await fetch('/Plots/get_crop_categories');
        if (!response.ok) {
            throw new Error(`שגיאה בטעינת קטגוריות: ${response.status}`);
        }

        const data = await response.json();

        data.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categorySelect.appendChild(option);
        });
        categorySelect.addEventListener('change', () => {
            const selectedCategory = categorySelect.value;
            loadCrops(selectedCategory);
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
            redirectUrl: "/Plots/track_greenhouse"
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
        let loggedInUserEmail = $("#postsContainer").data("user-email"); // קבלת המייל של המשתמש המחובר

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
document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("attendanceTableBody")) {
        loadAttendanceRecords();
    }

    if (document.getElementById("attendanceManagerTableBody")) {
        loadManagerAttendanceRecords();
    }
});

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


// attendance to manager
function loadManagerAttendanceRecords() {
    fetch('/attendance/manager_records')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById("attendanceManagerTableBody");
            tableBody.innerHTML = ""; // איפוס הטבלה לפני מילוי מחדש

            if (data.attendance_records.length === 0) {
                tableBody.innerHTML = "<tr><td colspan='6'>אין נתונים זמינים</td></tr>";
                return;
            }

            data.attendance_records.forEach(record => {
                const checkInTime = record.check_in ? new Date(record.check_in) : null;
                const checkOutTime = record.check_out ? new Date(record.check_out) : null;
                let totalHours = "-";

                if (checkInTime && checkOutTime) {
                    totalHours = ((checkOutTime - checkInTime) / (1000 * 60 * 60)).toFixed(2); // חישוב הפרש שעות מדויק
                }

                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${record.first_name || '-'}</td>
                    <td>${record.last_name || '-'}</td>
                    <td>${record.email || '-'}</td>
                    <td>${checkInTime ? checkInTime.toLocaleString('he-IL') : '-'}</td>
                    <td>${checkOutTime ? checkOutTime.toLocaleString('he-IL') : '-'}</td>
                    <td>${totalHours}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error("Error fetching manager attendance records:", error);
        });
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
        alert("נא למלא את כל השדות.");
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
            alert(data.message);
            closeAttendanceModal();
            loadManagerAttendanceRecords();
        })
        .catch(error => console.error("Error submitting manual attendance:", error));
}