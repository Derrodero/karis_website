(() => {
    const serviceSelect = document.querySelector("#id_service");
    const slotSelect = document.querySelector("#id_slot");
    if (!serviceSelect || !slotSelect) return;

    function filterSlots() {
        for (const option of slotSelect.options) {
            if (option.value) {
                option.hidden = option.dataset.service !== serviceSelect.value;
            }
        }
        const selected = slotSelect.selectedOptions[0];
        if (selected?.dataset.service !== serviceSelect.value) slotSelect.value = "";
    }

    serviceSelect.addEventListener("change", filterSlots);
    filterSlots();

    for (const trigger of document.querySelectorAll("[data-select-service]")) {
        trigger.addEventListener("click", () => {
            const serviceId = trigger.getAttribute("data-select-service");
            if (serviceId) {
                serviceSelect.value = serviceId;
                filterSlots();
                slotSelect.focus({ preventScroll: true });
            }
        });
    }
})();
