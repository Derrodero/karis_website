(() => {
    const serviceSelect = document.querySelector("#id_service");
    const specialtySelect = document.querySelector("#id_specialty");
    const slotSelect = document.querySelector("#id_slot");
    const dateInput = document.querySelector("#id_date");

    function filterSlots() {
        if (!serviceSelect || !slotSelect) return;
        const selectedDate = dateInput?.value || "";
        let availableCount = 0;
        for (const option of slotSelect.options) {
            if (option.value) {
                const matchesService = option.dataset.service === serviceSelect.value;
                const matchesDate = !selectedDate || option.dataset.date === selectedDate;
                option.hidden = !matchesService || !matchesDate;
                option.disabled = option.hidden;
                if (!option.hidden) availableCount += 1;
            }
        }
        const selected = slotSelect.selectedOptions[0];
        if (
            selected?.value &&
            (selected.dataset.service !== serviceSelect.value ||
                (selectedDate && selected.dataset.date !== selectedDate))
        ) {
            slotSelect.value = "";
        }
        const noTimes = document.querySelector("[data-no-times]");
        if (noTimes) noTimes.hidden = !selectedDate || availableCount > 0;
    }

    serviceSelect?.addEventListener("change", () => {
        filterSlots();
        updateReview();
    });
    specialtySelect?.addEventListener("change", updateReview);
    slotSelect?.addEventListener("change", updateReview);
    dateInput?.addEventListener("change", () => {
        filterSlots();
        updateReview();
    });

    for (const trigger of document.querySelectorAll("[data-select-service]")) {
        trigger.addEventListener("click", () => {
            const serviceId = trigger.getAttribute("data-select-service");
            if (serviceSelect && serviceId) {
                serviceSelect.value = serviceId;
                filterSlots();
                updateReview();
                slotSelect?.focus({ preventScroll: true });
            }
        });
    }

    const wizard = document.querySelector(".booking-wizard");
    if (!wizard) return;

    const panels = [...wizard.querySelectorAll("[data-wizard-panel]")];
    const indicators = [...wizard.querySelectorAll("[data-wizard-indicator]")];
    const stepStatus = wizard.querySelector(".booking-step-status");
    const branchInputs = [...wizard.querySelectorAll('input[name="branch"]')];
    let currentStep = 1;

    wizard.classList.add("booking-wizard-enhanced");

    function updateReview() {
        const checkedBranch = wizard.querySelector('input[name="branch"]:checked');
        const branchName = checkedBranch?.closest("label")?.querySelector("strong")?.textContent;
        const serviceName = serviceSelect?.selectedOptions[0]?.textContent.trim();
        const specialtyName = specialtySelect?.selectedOptions[0]?.textContent.trim();
        const selectedSlot = slotSelect?.selectedOptions[0];
        const slotName = selectedSlot?.textContent.trim();
        const timeName = slotName?.split(" at ").pop();
        const dateParts = dateInput?.value.split("-").map(Number);
        const dateName = dateParts?.length === 3
            ? new Intl.DateTimeFormat("en-UG", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
              }).format(new Date(dateParts[0], dateParts[1] - 1, dateParts[2]))
            : "Choose a date";
        wizard.querySelector("[data-review-branch]").textContent = branchName || "Choose a branch";
        wizard.querySelector("[data-review-service]").textContent =
            serviceSelect?.value ? serviceName : "Choose a service";
        wizard.querySelector("[data-review-specialty]").textContent =
            specialtySelect?.value ? specialtyName : "Not selected";
        wizard.querySelector("[data-review-date]").textContent =
            dateName;
        wizard.querySelector("[data-review-time]").textContent =
            slotSelect?.value ? timeName : "Choose a time";
    }

    function showStep(step, focusHeading = false) {
        currentStep = step;
        panels.forEach((panel) => {
            const active = Number(panel.dataset.wizardPanel) === step;
            panel.classList.toggle("is-active", active);
            panel.hidden = !active;
        });
        indicators.forEach((indicator) => {
            const indicatorStep = Number(indicator.dataset.wizardIndicator);
            indicator.classList.toggle("is-current", indicatorStep === step);
            indicator.classList.toggle("is-complete", indicatorStep < step);
            if (indicatorStep === step) {
                indicator.setAttribute("aria-current", "step");
            } else {
                indicator.removeAttribute("aria-current");
            }
        });
        const title = indicators[step - 1]?.querySelector("strong")?.textContent;
        stepStatus.textContent = `Step ${step} of ${panels.length}: ${title}`;
        updateReview();
        if (focusHeading) panels[step - 1]?.querySelector("h3")?.focus();
    }

    function firstInvalidControl(panel) {
        return [...panel.querySelectorAll("input, select, textarea")].find(
            (control) => !control.checkValidity(),
        );
    }

    wizard.addEventListener("click", (event) => {
        const next = event.target.closest("[data-wizard-next]");
        const back = event.target.closest("[data-wizard-back]");
        if (next) {
            const invalid = firstInvalidControl(panels[currentStep - 1]);
            if (invalid) {
                invalid.reportValidity();
                return;
            }
            showStep(Math.min(currentStep + 1, panels.length), true);
        } else if (back) {
            showStep(Math.max(currentStep - 1, 1), true);
        }
    });

    wizard.addEventListener("submit", (event) => {
        const invalid = [...wizard.querySelectorAll("input, select, textarea")].find(
            (control) => !control.checkValidity(),
        );
        if (invalid) {
            event.preventDefault();
            const invalidPanel = invalid.closest("[data-wizard-panel]");
            if (invalidPanel) showStep(Number(invalidPanel.dataset.wizardPanel), true);
            invalid.reportValidity();
        }
    });

    wizard.querySelectorAll(".booking-error-summary a").forEach((link) => {
        link.addEventListener("click", (event) => {
            const control = document.querySelector(link.getAttribute("href"));
            const panel = control?.closest("[data-wizard-panel]");
            if (panel) {
                event.preventDefault();
                showStep(Number(panel.dataset.wizardPanel), true);
                control.focus();
            }
        });
    });

    wizard.querySelectorAll("[data-wizard-panel] .errorlist").forEach((errors) => {
        const panel = errors.closest("[data-wizard-panel]");
        if (panel && errors.children.length) {
            showStep(Number(panel.dataset.wizardPanel));
        }
    });
    branchInputs.forEach((input) => {
        input.addEventListener("change", () => {
            branchInputs.forEach((branchInput) => {
                branchInput.closest("label")?.classList.toggle("is-selected", branchInput.checked);
            });
            updateReview();
        });
        input.closest("label")?.classList.toggle("is-selected", input.checked);
    });
    filterSlots();
    showStep(currentStep);
})();
