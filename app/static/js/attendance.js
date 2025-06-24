document.addEventListener("DOMContentLoaded", async function () {
    if (document.getElementById("attendanceTableBody")) {
        loadAttendanceRecords();
    }

    if (document.getElementById("attendanceManagerTableBody")) {
        loadManagerAttendanceRecords();
    }

});

function loadAttendanceRecords() {
    fetch('/attendance/user_records')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById("attendanceTableBody");
            tableBody.innerHTML = "";

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
            tableBody.innerHTML = "";

            if (data.attendance_records.length === 0) {
                tableBody.innerHTML = "<tr><td colspan='7'>אין נתונים זמינים</td></tr>";
                return;
            }

            data.attendance_records.sort((a, b) => {
                const dateA = parseHebrewDate(a.check_in);
                const dateB = parseHebrewDate(b.check_in);
                return dateA - dateB;
            });

            data.attendance_records.forEach(record => {
                const checkInTime = (record.check_in && !isNaN(new Date(record.check_in).getTime()))
                    ? new Date(record.check_in).toISOString().slice(0, 16)
                    : "";
                const checkOutTime = (record.check_out && !isNaN(new Date(record.check_out).getTime()))
                    ? new Date(record.check_out).toISOString().slice(0, 16)
                    : "";

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
    fetchEmployeesList();
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
    const inTime = new Date(checkInTime);
    const outTime = new Date(checkOutTime);

    if (outTime <= inTime) {
        showAlert("שגיאה", "שעת היציאה חייבת להיות לאחר שעת הכניסה.", {
            restoreForm: true,
            formId: "attendanceForm",
            modalId: "attendanceModal"
        });
        return;
    }


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

function openEditModal(id) {
    fetch(`/attendance/get_record/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert("שגיאה", data.error, { restoreForm: false });
                return;
            }

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
    const inTime = new Date(checkIn);
    const outTime = new Date(checkOut);

    if (outTime <= inTime) {
        showAlert("שגיאה", "שעת היציאה חייבת להיות לאחר שעת הכניסה.", {
            restoreForm: true,
            formId: "editAttendanceForm",
            modalId: "editAttendanceModal"
        });
        return;
    }

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


function parseHebrewDate(dateStr) {
    const [datePart, timePart] = dateStr.split(" ");
    const [day, month, year] = datePart.split("/").map(Number);
    const [hour, minute] = timePart.split(":").map(Number);
    return new Date(year, month - 1, day, hour, minute); // חודש ב-JS מתחיל מ-0
}
