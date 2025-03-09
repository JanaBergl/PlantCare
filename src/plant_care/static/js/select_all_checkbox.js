document.addEventListener("DOMContentLoaded", function () {
    const selectAllCheckbox = document.getElementById("select_all");
    const plantCheckboxes = document.querySelectorAll("input[name='plants']");

    selectAllCheckbox.addEventListener("change", function () {
        plantCheckboxes.forEach(function (checkbox) {
            checkbox.checked = selectAllCheckbox.checked;
        });
    });

    plantCheckboxes.forEach(function (checkbox) {
        checkbox.addEventListener("change", function () {
            if (Array.from(plantCheckboxes).every(cb => cb.checked)) {
                selectAllCheckbox.checked = true;
            } else {
                selectAllCheckbox.checked = false;
            }
        });
    });
});