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

        // הצגת עמודת פעולה רק אם צריך
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

function applyTaskFilter() {
    const month = document.getElementById("monthSelect").value;
    const year = document.getElementById("yearSelect").value;
    const rows = document.querySelectorAll("#taskTableBody tr");

    rows.forEach(row => {
        const dateCell = row.children[3]; // תא של תאריך אחרון למשימה
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
}
