(() => {
    const timeInput = document.querySelector("#id_start_time");
    if (!timeInput) return;

    document.querySelectorAll("[data-start-time]").forEach((button) => {
        button.addEventListener("click", () => {
            timeInput.value = button.dataset.startTime;
            timeInput.dispatchEvent(new Event("input", { bubbles: true }));
            timeInput.dispatchEvent(new Event("change", { bubbles: true }));
            timeInput.focus();
        });
    });
})();
