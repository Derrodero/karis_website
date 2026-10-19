(() => {
    const slideshow = document.querySelector("[data-home-slideshow]");
    if (!slideshow) return;

    const slides = [...slideshow.querySelectorAll("[data-home-slide]")];
    if (slides.length < 2) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let activeIndex = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));
    let timerId = null;

    function showSlide(index) {
        activeIndex = (index + slides.length) % slides.length;
        slides.forEach((slide, slideIndex) => {
            slide.classList.toggle("is-active", slideIndex === activeIndex);
        });
    }

    function stopSlideshow() {
        if (timerId !== null) window.clearInterval(timerId);
        timerId = null;
    }

    function startSlideshow() {
        if (reducedMotion.matches || timerId !== null) return;
        timerId = window.setInterval(() => showSlide(activeIndex + 1), 6500);
    }

    reducedMotion.addEventListener("change", () => {
        if (reducedMotion.matches) stopSlideshow();
        else startSlideshow();
    });

    if (reducedMotion.matches) stopSlideshow();
    else startSlideshow();
})();