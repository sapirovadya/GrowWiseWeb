// my team
let currentEmployeeEmail = "";
function openEmployeeModal(id, firstName, lastName, email, role, isApproved) {
    const modal = document.getElementById("detailsModal");
    const firstNameField = document.getElementById("detail-first-name");
    const lastNameField = document.getElementById("detail-last-name");
    const emailField = document.getElementById("detail-email");
    const roleField = document.getElementById("detail-role");
    const actions = document.getElementById("modal-actions");
    const roleText = role === "employee" ? "עובד" : role === "co_manager" ? "שותף" : "לא ידוע";
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
        if (typeof onConfirm === "function") {
            onConfirm();
        }
    };
    noButton.onclick = function () {
        confirmBox.style.display = "none";
    };
}