(() => {
    const navigation = document.querySelector(".site-nav");
    const currentPage = navigation?.dataset.currentPage;
    navigation?.querySelectorAll("a[data-page]").forEach((link) => {
        if (link.dataset.page === currentPage) link.setAttribute("aria-current", "page");
    });

    const navigationToggle = document.querySelector(".nav-toggle");
    if (navigation && navigationToggle) {
        navigationToggle.hidden = false;
        navigation.classList.add("is-collapsible");
        function setNavigationOpen(isOpen) {
            navigation.classList.toggle("is-open", isOpen);
            navigationToggle.setAttribute("aria-expanded", String(isOpen));
            navigationToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
            navigationToggle.title = isOpen ? "Close navigation" : "Open navigation";
            navigationToggle.innerHTML = isOpen ? '<i class="bi bi-x-lg" aria-hidden="true"></i>' : '<i class="bi bi-list" aria-hidden="true"></i>';
        }
        navigationToggle.addEventListener("click", () => {
            setNavigationOpen(navigationToggle.getAttribute("aria-expanded") !== "true");
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && navigationToggle.getAttribute("aria-expanded") === "true") {
                setNavigationOpen(false);
                navigationToggle.focus();
            }
        });
    }

    const selector = document.querySelector("[data-theme-select]");
    if (!selector) return;

    const storageKey = "app-theme";
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

    function applyTheme(preference) {
        const theme = preference === "system" ? (systemTheme.matches ? "dark" : "light") : preference;
        document.documentElement.dataset.theme = theme;
        selector.value = preference;
    }

    let preference = "system";
    try {
        const saved = window.localStorage.getItem(storageKey);
        if (["system", "light", "dark"].includes(saved)) preference = saved;
    } catch {
        preference = "system";
    }

    applyTheme(preference);
    selector.addEventListener("change", () => {
        preference = selector.value;
        try {
            window.localStorage.setItem(storageKey, preference);
        } catch {
            preference = "system";
        }
        applyTheme(preference);
    });
    systemTheme.addEventListener("change", () => {
        if (preference === "system") applyTheme(preference);
    });
})();
