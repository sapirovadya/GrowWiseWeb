//Plot task 
function openPlotTasksModal(plotId) {
    const modal = document.getElementById("plotTasksModal");
    modal.style.display = "flex";
    loadPlotTasks(plotId);
    modal.setAttribute("data-plot-id", plotId);
}

function closePlotTasksModal() {
    document.getElementById("plotTasksModal").style.display = "none";
}

async function loadPlotTasks(plotId) {
    const response = await fetch(`/Plots/plot_tasks/${plotId}`);
    const data = await response.json();
    const container = document.getElementById("plotTasksContainer");
    container.innerHTML = "";

    data.tasks.forEach(task => {
        const isCompleted = task.status === "done";
        const assignedTo = task.employee_email || "";

        const taskElement = document.createElement("div");
        taskElement.classList.add("task-row");

        const html = `
            <div class="task-header">
                <input type="checkbox" ${isCompleted ? "checked disabled" : ""} data-task-id="${task._id}" class="task-done">
                <span class="task-name" onclick="toggleTaskDescription('${task._id}')">${task.task_name}</span>
                ${data.is_manager ? `<select class="task-employee" data-task-id="${task._id}" ${isCompleted ? "disabled" : ""}>
                    ${data.employees.map(e => `<option value="${e.email}" ${e.email === assignedTo ? "selected" : ""}>${e.name}</option>`).join("")}
                </select>` : ""}
            </div>
            <div class="task-description" id="desc-${task._id}" style="display: none;">${task.task_content}</div>
        `;
        taskElement.innerHTML = html;
        container.appendChild(taskElement);
    });

    if (data.is_manager) {
        document.getElementById("addTaskArea").style.display = "block";
        const employeeSelect = document.getElementById("newTaskEmployee");
        employeeSelect.innerHTML = "";
        data.employees.forEach(e => {
            const option = document.createElement("option");
            option.value = e.email;
            option.textContent = e.name;
            employeeSelect.appendChild(option);
        });
    }
}

function toggleTaskDescription(taskId) {
    const desc = document.getElementById(`desc-${taskId}`);
    desc.style.display = desc.style.display === "none" ? "block" : "none";
}



function openNewTaskModal() {
    const plotId = document.getElementById("plotTasksModal").getAttribute("data-plot-id");

    const newModal = document.getElementById("newTaskModal");
    newModal.setAttribute("data-plot-id", plotId);
    document.getElementById("newTaskName").value = "";
    document.getElementById("newTaskContentFull").value = "";
    document.getElementById("newTaskDueDate").value = "";
    document.getElementById("newTaskEmployeeSelect").innerHTML = "";

    closePlotTasksModal();

    fetch(`/Plots/plot_tasks/${plotId}`)
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById("newTaskEmployeeSelect");
            select.innerHTML = "";
            data.employees.forEach(e => {
                const option = document.createElement("option");
                option.value = e.email;
                option.textContent = e.name;
                select.appendChild(option);
            });

            newModal.style.display = "flex";
        });
}
async function submitNewTask() {
    const modal = document.getElementById("newTaskModal");
    const plotId = modal.getAttribute("data-plot-id");

    const taskName = document.getElementById("newTaskName").value.trim();
    const taskContent = document.getElementById("newTaskContentFull").value.trim();
    const dueDate = document.getElementById("newTaskDueDate").value;
    const employeeEmail = document.getElementById("newTaskEmployeeSelect").value;
    if (!taskName || !taskContent || !dueDate || !employeeEmail) {
        showAlert("שגיאה", "נא למלא את כל השדות החובה: כותרת, תוכן, תאריך ולקשר עובד.", {
            isSuccess: false,
            restoreForm: false,
            modalId: "newTaskModal"
        });
        return;
    }
    window.lastFormData = {
        newTaskName: taskName,
        newTaskContentFull: taskContent,
        newTaskDueDate: dueDate,
        newTaskEmployeeSelect: employeeEmail
    };

    const response = await fetch("/Plots/plot_tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            plot_id: plotId,
            task_name: taskName,
            task_content: taskContent,
            due_date: dueDate,
            employee_email: employeeEmail
        })
    });

    const data = await response.json();

    if (data.success) {
        closeNewTaskModal();

        showAlert("הצלחה", "המשימה נוספה בהצלחה!", {
            isSuccess: true,
            modalId: "plotTasksModal"
        });
    } else {
        showAlert("שגיאה", "אירעה שגיאה בהוספת המשימה. נסה שוב.", {
            isSuccess: false,
            restoreForm: true,
            formId: "newTaskForm",
            modalId: "newTaskModal"
        });
    }
}

function closeNewTaskModal() {
    const modal = document.getElementById("newTaskModal");
    modal.style.display = "none";
}

async function savePlotTasks() {
    const selects = document.querySelectorAll(".task-employee");
    const checkboxes = document.querySelectorAll(".task-done:checked");

    const updates = [];
    selects.forEach(select => {
        const taskId = select.getAttribute("data-task-id");
        const selectedEmail = select.value;
        updates.push({ task_id: taskId, employee_email: selectedEmail });
    });

    const completedTaskIds = Array.from(checkboxes).map(cb => cb.getAttribute("data-task-id"));

    try {
        const response = await fetch("/Plots/update_task_employees", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ updates, completed_tasks: completedTaskIds })
        });

        const data = await response.json();
        if (data.success) {
            showAlert("הצלחה", "המשימות והעובדים עודכנו בהצלחה", {
                isSuccess: true,
                modalId: "plotTasksModal"
            });
        } else {
            showAlert("שגיאה", data.error || "אירעה שגיאה בעדכון", {
                isSuccess: false,
                modalId: "plotTasksModal"
            });
        }
    } catch (error) {
        console.error("שגיאה:", error);
        showAlert("שגיאה", "בעיה בשרת. נסה שוב.", { isSuccess: false });
    }
}