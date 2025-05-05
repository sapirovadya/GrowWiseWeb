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
                            <td>
                            ${vehicle.Km_WorkHours ? `${vehicle.Km_WorkHours} (עודכן ב־${vehicle.Km_WorkHours_update_date || ''})` : ''}
                            </td>
                            <td class="action-buttons">
                            <button class="action-btn btn-test edit-test-btn" data-id="${vehicle._id}">ערוך טסט</button>
                            <button class="action-btn btn-service edit-service-btn" data-id="${vehicle._id}">ערוך טיפול</button>
                            <button class="action-btn btn-insurance edit-insurance-btn"  data-id="${vehicle._id}">ערוך ביטוח</button>
                            <button class="action-btn btn-km edit-km-btn" data-id="${vehicle._id}">ק"מ/שעות</button>
                            </td>
                            <td><button class="action-btn btn-delete-vehicle delete-btn"  data-id="${vehicle._id}">הסר</button></td>

                        </tr>
                    `);
                }
            });

            // delete vehicle
            $(".delete-btn").click(function () {
                let vehicle_id = $(this).data("id");
                deleteVehicle(vehicle_id);
            });

            $(".edit-test-btn").click(function () {
                let vehicle_id = $(this).data("id");
                openEditTestModal(vehicle_id);
            });

            $(".edit-service-btn").click(function () {
                let vehicle_id = $(this).data("id");
                openEditServiceModal(vehicle_id);
            });

            $(".edit-insurance-btn").click(function () {
                let vehicle_id = $(this).data("id");
                openEditInsuranceModal(vehicle_id);
            });

            $(".edit-km-btn").click(function () {
                let vehicle_id = $(this).data("id");
                openEditKmModal(vehicle_id);
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
            Km_WorkHours: $("#addKmWorkHours").val() || "0",
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

    $("#editTestForm").submit(function (event) {
        event.preventDefault();
        let vehicleId = $("#editTestVehicleId").val();
        $.ajax({
            url: `/vehicles/update_test/${vehicleId}`,
            type: "PUT",
            contentType: "application/json",
            data: JSON.stringify({
                test_date: $("#editTestDate").val(),
                test_cost: $("#editTestCost").val()
            }),
            success: function () {
                loadVehicles();
                $("#editTestModal").modal("hide");
            }
        });
    });

    $("#editServiceForm").submit(function (event) {
        event.preventDefault();
        let vehicleId = $("#editServiceVehicleId").val();

        let vehicleNumber = $("#row-" + vehicleId).find("td:first").text().trim();

        $.ajax({
            url: `/vehicles/update_service/${vehicleId}`,
            type: "PUT",
            contentType: "application/json",
            data: JSON.stringify({
                vehicle_number: vehicleNumber,
                service_date: $("#editServiceDate").val(),
                service_cost: $("#editServiceCost").val(),
                service_notes: $("#editServiceNotes").val()
            }),
            success: function () {
                loadVehicles();
                $("#editServiceModal").modal("hide");
            }
        });
    });


    $("#editInsuranceForm").submit(function (event) {
        event.preventDefault();
        let vehicleId = $("#editInsuranceVehicleId").val();
        $.ajax({
            url: `/vehicles/update_insurance/${vehicleId}`,
            type: "PUT",
            contentType: "application/json",
            data: JSON.stringify({
                insurance_date: $("#editInsuranceDate").val(),
                insurance_cost: $("#editInsuranceCost").val()
            }),
            success: function () {
                loadVehicles();
                $("#editInsuranceModal").modal("hide");
            }
        });
    });

    $("#editKmForm").submit(function (event) {
        event.preventDefault();
        let vehicleId = $("#editKmVehicleId").val();
        let newKmWorkHours = $("#editKmWorkHours").val();
        $.ajax({
            url: `/vehicles/update_km/${vehicleId}`,
            type: "PUT",
            contentType: "application/json",
            data: JSON.stringify({
                Km_WorkHours: newKmWorkHours
            }),
            success: function () {
                loadVehicles();
                $("#editKmModal").modal("hide");
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

    function openEditTestModal(vehicleId) {
        $("#editTestVehicleId").val(vehicleId);
        $("#editTestModal").modal("show");
    }

    function openEditServiceModal(vehicleId) {
        $("#editServiceVehicleId").val(vehicleId);
        $("#editServiceModal").modal("show");
    }

    function openEditInsuranceModal(vehicleId) {
        $("#editInsuranceVehicleId").val(vehicleId);
        $("#editInsuranceModal").modal("show");
    }

    function openEditKmModal(vehicleId) {
        $("#editKmVehicleId").val(vehicleId);
        $("#editKmModal").modal("show");
    }
    
});

    function clearKmField() {
        $("#editKmWorkHours").val('');
        $("#editKmForm").submit();
    }