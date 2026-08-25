const toggleBtn = document.getElementById('theme-toggle');
const body = document.body;

if (localStorage.getItem('theme') === 'dark') {
  body.classList.add('dark-mode');
}

toggleBtn.addEventListener('click', () => {
  body.classList.toggle('dark-mode');
  localStorage.setItem('theme', body.classList.contains('dark-mode') ? 'dark' : 'light');
});


const SearchInput = document.getElementById("SearchInput");
const FilterButton = document.getElementById("FilterForRoomMate");
const FilterMenu = document.getElementById("FilterMenu");
const FilterOptions = document.querySelectorAll(".FilterOption");
const RoomateCells = document.querySelectorAll(".RoomateCell");

let activeCity = "all";

function applyFilters() {
  const query = SearchInput.value.trim().toLowerCase();
  RoomateCells.forEach((cell) => {
    const matchesQuery = cell.textContent.toLowerCase().includes(query);
    const matchesCity =
      activeCity === "all" || cell.textContent.includes(activeCity);
    cell.style.display = matchesQuery && matchesCity ? "" : "none";
  });
}

SearchButton.addEventListener("click", () => {
  const isOpen = SearchInput.style.display === "block";
  SearchInput.style.display = isOpen ? "none" : "block";
  if (!isOpen) {
    SearchInput.focus();
  }
});

FilterButton.addEventListener("click", () => {
  FilterMenu.classList.toggle("ShowFilterMenuAnimation");
});

FilterOptions.forEach((option) => {
  option.addEventListener("click", () => {
    FilterOptions.forEach((other) => other.classList.remove("Active"));
    option.classList.add("Active");
    activeCity = option.dataset.filter;
    applyFilters();
    FilterMenu.classList.remove("ShowFilterMenuAnimation");
  });
});

document.addEventListener("click", (event) => {
  const clickedInsideButtons = event.target.closest("#ButtonsGroup");
  if (!clickedInsideButtons && SearchInput.style.display === "block") {
    SearchInput.style.display = "none";
  }
  if (!event.target.closest("#FilterWrapper")) {
    FilterMenu.classList.remove("ShowFilterMenuAnimation");
  }
});

