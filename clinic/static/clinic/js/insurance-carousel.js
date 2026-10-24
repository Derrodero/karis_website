(() => {
    const track = document.querySelector("[data-insurance-track]");
    const toggle = document.querySelector("[data-insurance-toggle]");
    const firstSet = track?.querySelector(".footer-insurance-set");
    if (!track || !toggle || !firstSet || typeof track.animate !== "function") return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const animationDuration = 30000;
    let animation = null;
    let manuallyPaused = false;

    const duplicateSet = firstSet.cloneNode(true);
    duplicateSet.setAttribute("aria-hidden", "true");
    duplicateSet.querySelectorAll("img").forEach((image) => {
        image.alt = "";
    });
    track.append(duplicateSet);

    function stopRotation() {
        animation?.cancel();
        animation = null;
    }

    function startRotation() {
        stopRotation();
        toggle.hidden = reducedMotion.matches;
        if (reducedMotion.matches) return;

        animation = track.animate(
            [{ transform: "translateX(-50%)" }, { transform: "translateX(0)" }],
            { duration: animationDuration, iterations: Infinity, easing: "linear" },
        );
        if (manuallyPaused) animation.pause();
    }

    toggle.addEventListener("click", () => {
        manuallyPaused = !manuallyPaused;
        if (manuallyPaused) animation?.pause();
        else animation?.play();
        toggle.textContent = manuallyPaused ? "Resume" : "Pause";
        toggle.setAttribute(
            "aria-label",
            `${manuallyPaused ? "Resume" : "Pause"} insurance logo rotation`,
        );
    });

    reducedMotion.addEventListener("change", startRotation);
    startRotation();
})();
