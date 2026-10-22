const directory = document.querySelector("[data-doctor-directory]");

if (directory) {
  const searchInput = document.querySelector("[data-doctor-search]");
  const branchSelect = document.querySelector("[data-doctor-branch]");
  const specialtyInputs = directory.querySelectorAll("[data-specialty-filter]");
  const cards = directory.querySelectorAll("[data-doctor-card]");
  const resultCount = directory.querySelector("[data-result-count]");
  const noResults = directory.querySelector("[data-no-results]");

  const updateResults = () => {
    const query = searchInput.value.trim().toLocaleLowerCase();
    const branch = branchSelect.value;
    const selectedSpecialties = new Set(
      [...specialtyInputs]
        .filter((input) => input.checked)
        .map((input) => input.value),
    );
    let visibleCount = 0;

    cards.forEach((card) => {
      const matchesQuery = card.dataset.search.toLocaleLowerCase().includes(query);
      const matchesBranch = !branch || card.dataset.branch === branch;
      const matchesSpecialty =
        selectedSpecialties.size === 0 ||
        selectedSpecialties.has(card.dataset.specialty);
      const isVisible = matchesQuery && matchesBranch && matchesSpecialty;

      card.hidden = !isVisible;
      if (isVisible) visibleCount += 1;
    });

    resultCount.textContent = `${visibleCount} ${
      visibleCount === 1 ? "profile" : "profiles"
    }`;
    noResults.hidden = visibleCount !== 0;
  };

  searchInput.addEventListener("input", updateResults);
  branchSelect.addEventListener("change", updateResults);
  specialtyInputs.forEach((input) =>
    input.addEventListener("change", updateResults),
  );
}
