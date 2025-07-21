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

// save task
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

function closeOnOutsideClick(event) {
    const taskModal = document.getElementById("taskModal");
    const taskModalContent = document.getElementById("taskModalContent");

    if (taskModal.style.display === "flex" &&
        !taskModalContent.contains(event.target)) {
        closeTaskModal();
    }
}

fetch('/task/alltasks')
    .then(response => response.json())
    .then(data => {
        const taskTableBody = document.getElementById('taskTableBody');
        const actionHeader = document.querySelector('.action-header');
        let hasApproveButtons = false;
        taskTableBody.innerHTML = '';

        data.forEach(task => {
            const row = document.createElement('tr');
            const isDone = task.status === 'done';

            const statusOptions = `
                <select ${isDone ? 'disabled' : ''} data-id="${task._id}" class="form-select status-select">
                    <option value="in_progress" ${task.status === 'in_progress' ? 'selected' : ''}>בתהליך</option>
                    <option value="done" ${task.status === 'done' ? 'selected' : ''}>בוצע</option>
                </select>
            `;

            const approveButton = isDone ? '' : `<button class="btn btn-success btn-sm approve-btn" data-id="${task._id}">אישור</button>`;
            if (!isDone) hasApproveButtons = true;

            row.innerHTML = `
                <td data-label="שם העובד:">${task.employee_name}</td>
                <td data-label="שם המשימה:">${task.task_name}</td>
                <td data-label="המשימה:">${task.task_content}</td>
                <td data-label="תאריך אחרון למשימה:">${task.due_date}</td>
                <td data-label="סטטוס:">${statusOptions}</td>
                ${approveButton ? `<td data-label="פעולה:">${approveButton}</td>` : ""}
                `;
            taskTableBody.appendChild(row);
        });

        if (hasApproveButtons) {
            actionHeader.style.display = 'table-cell';
        } else {
            actionHeader.style.display = 'none';
        }

        document.querySelectorAll('.approve-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const taskId = this.getAttribute('data-id');
                fetch('/task/update_status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ id: taskId, status: 'done' })
                })
                    .then(res => res.json())
                    .then(res => {
                        if (res.success) {
                            showAlert("הצלחה", "המשימה עודכנה בהצלחה", {
                                onSuccess: () => location.reload()
                            });
                        }

                    });
            });
        });
    });
let selectedTask = null;
let calendar = null;

document.addEventListener("DOMContentLoaded", async function () {
    const calendarEl = document.getElementById('calendar');
    const response = await fetch("/task/alltasks");
    const tasks = await response.json();

    const events = tasks.map(task => ({
        id: task._id,
        title: task.task_name + " - " + task.employee_name,
        start: task.due_date,
        extendedProps: {
            content: task.task_content,
            status: task.status
        },
        allDay: true,
        backgroundColor: task.status === "done" ? "#6c757d" : "#28a745",
    }));


    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'he',
        direction: 'rtl',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
        },
        events: events,
        eventClick: function (info) {
            const task = info.event;
            selectedTask = task;

            document.getElementById("taskModalTitle").innerText = task.title;
            document.getElementById("taskModalContent").innerText = task.extendedProps.content;

            const select = document.getElementById("statusSelectModal");
            const updateBtn = document.getElementById("updateStatusBtn");

            select.value = task.extendedProps.status;

            if (task.extendedProps.status === "done") {
                select.disabled = true;
                updateBtn.style.display = "none";
            } else {
                select.disabled = false;
                updateBtn.style.display = "inline-block";
            }

            document.getElementById("taskDetailModal").style.display = "block";
        }
    });

    calendar.render();
});


function applyTaskFilter() {
    const month = document.getElementById("monthSelect").value;
    const year = document.getElementById("yearSelect").value;

    // עדכון תצוגת הטבלה (כמו קודם)
    const rows = document.querySelectorAll("#taskTableBody tr");

    rows.forEach(row => {
        const dateCell = row.children[3];
        const dateText = dateCell ? dateCell.textContent.trim() : "";
        let show = true;

        if (month && !dateText.includes(`-${month}-`)) {
            show = false;
        }

        if (year && !dateText.includes(year)) {
            show = false;
        }

        row.style.display = show ? "" : "none";
    });

    // העברת לוח השנה לחודש/שנה שנבחרו
    if (month && year && calendar) {
        const formattedMonth = month.padStart(2, '0');
        const gotoDate = `${year}-${formattedMonth}-01`;
        calendar.gotoDate(gotoDate);
    }
}

document.getElementById("updateStatusBtn").addEventListener("click", function () {
    const newStatus = document.getElementById("statusSelectModal").value;

    if (!selectedTask) {
        alert("שגיאה: לא נמצאה משימה נבחרת.");
        return;
    }

    if (newStatus === selectedTask.extendedProps.status) {
        closeTaskDetailModal();
        return;
    }

    fetch("/task/update_status", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id: selectedTask.id,
            status: newStatus
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                selectedTask.extendedProps.status = newStatus;
                selectedTask.setProp("backgroundColor", newStatus === "done" ? "#6c757d" : "#28a745");
                closeTaskDetailModal();
                location.reload();
            } else {
                alert("שגיאה בעדכון הסטטוס: " + (data.error || ""));
            }
        })
        .catch(err => {
            alert("שגיאה בבקשה לשרת");
            console.error(err);
        });
});

function closeTaskDetailModal() {
    document.getElementById("taskDetailModal").style.display = "none";
    selectedTask = null;

    document.getElementById("statusSelectModal").disabled = false;
    document.getElementById("updateStatusBtn").style.display = "inline-block";
}

