const locationLinks = document.querySelectorAll(".branch-location");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

if ("IntersectionObserver" in window && !reducedMotion.matches) {
  const locationObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        entry.target.classList.toggle("is-shaking", entry.isIntersecting);
      });
    },
    { threshold: 0.25 },
  );

  locationLinks.forEach((link) => locationObserver.observe(link));
}
