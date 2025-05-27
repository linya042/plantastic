
const API_URL = "https://plantastic-backend.onrender.com";
const daysOfWeek = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"];
const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];

function navigateTo(pageId: string) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  const target = document.getElementById(pageId);
  if (target){ 
    target.classList.add("active");

    if (pageId === "water") setupWaterCalculator();
  }
}


function formatDate(date: Date): string {
  return date.toISOString().split("T")[0];
}
function isSameDay(d1: Date, d2: Date): boolean {
  return d1.getDate() === d2.getDate() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getFullYear() === d2.getFullYear();
}

async function fetchTasksByDate(dateStr: string): Promise<string[]> {
  const res = await fetch(`${API_URL}/tasks?date=${dateStr}`);
  return res.ok ? (await res.json()).map((t: any) => t.text) : [];
}
async function addTask(dateStr: string, text: string) {
  await fetch(`${API_URL}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ date: dateStr, text })
  });
}

// === Виджет недели ===
let currentStartDate = new Date();
currentStartDate.setDate(currentStartDate.getDate() - ((currentStartDate.getDay() + 6) % 7));

async function renderWeek(startDate: Date) {
  const container = document.getElementById("calendarDays")!;
  const monthSpan = document.getElementById("calendarMonth")!;
  container.innerHTML = "";

  for (let i = 0; i < 7; i++) {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + i);
    const dateStr = formatDate(date);
    const tasks = await fetchTasksByDate(dateStr);

    const div = document.createElement("div");
    div.classList.add("calendar-day");
    if (isSameDay(date, new Date())) div.classList.add("today");
    if (tasks.length) div.innerHTML = '<div class="task-dot"></div>';
    div.innerHTML += `<div class="weekday">${daysOfWeek[(date.getDay() + 6) % 7]}</div><div class="date">${date.getDate()}</div>`;
    div.addEventListener("click", async () => {
      const taskList = document.getElementById("weekTaskList")!;
      taskList.innerHTML = "";
      const tasks = await fetchTasksByDate(dateStr);
      tasks.forEach(t => {
        const li = document.createElement("li");
        li.textContent = t;
        taskList.appendChild(li);
      });
    });
    container.appendChild(div);
  }
  monthSpan.textContent = monthNames[startDate.getMonth()];
}

document.getElementById("prevWeekBtn")?.addEventListener("click", () => {
  currentStartDate.setDate(currentStartDate.getDate() - 7);
  renderWeek(currentStartDate);
});
document.getElementById("nextWeekBtn")?.addEventListener("click", () => {
  currentStartDate.setDate(currentStartDate.getDate() + 7);
  renderWeek(currentStartDate);
});

// === Календарь месяца ===
let selectedDate = new Date();

function updateSelectedDateLabel() {
  const label = document.getElementById("selectedDateLabel")!;
  label.textContent = `${selectedDate.getDate()} ${monthNames[selectedDate.getMonth()]}`;
}

async function renderMonth(date: Date) {
  const grid = document.getElementById("monthGrid")!;
  const label = document.getElementById("calendarMonthName")!;
  const year = date.getFullYear();
  const month = date.getMonth();
  const firstDay = new Date(year, month, 1);
  const startDay = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  grid.innerHTML = "";
  for (let i = 0; i < startDay; i++) grid.appendChild(document.createElement("div"));

  for (let day = 1; day <= daysInMonth; day++) {
    const d = new Date(year, month, day);
    const cell = document.createElement("div");
    cell.classList.add("calendar-cell");
    cell.textContent = day.toString();
    if (isSameDay(d, new Date())) cell.classList.add("today");
    if (isSameDay(d, selectedDate)) cell.classList.add("selected");
    cell.addEventListener("click", () => {
      selectedDate = d;
      updateSelectedDateLabel();
      renderMonth(selectedDate);
    });grid.appendChild(cell);
  }

  label.textContent = `${monthNames[month]} ${year}`;
}

document.getElementById("prevMonth")?.addEventListener("click", () => {
  selectedDate.setMonth(selectedDate.getMonth() - 1);
  renderMonth(selectedDate);
  updateSelectedDateLabel();
});
document.getElementById("nextMonth")?.addEventListener("click", () => {
  selectedDate.setMonth(selectedDate.getMonth() + 1);
  renderMonth(selectedDate);
  updateSelectedDateLabel();
});

document.getElementById("addEventButton")?.addEventListener("click", async () => {
  const type = (document.getElementById("eventType") as HTMLSelectElement).value;
  const plant = (document.getElementById("plantSelect") as HTMLSelectElement).value;
  const text = `${type}: ${plant}`;
  const dateStr = formatDate(selectedDate);
  await addTask(dateStr, text);
  alert("Событие добавлено!");
});

// === Распознавание по фото (заглушка) ===
document.getElementById("infoBtn")?.addEventListener("click", () => {
  const result = document.getElementById("recognitionResult")!;
  result.textContent = "Информация: Это Монстера. Любит рассеянный свет.";
});

document.getElementById("sortBtn")?.addEventListener("click", () => {
  const result = document.getElementById("recognitionResult")!;
  result.textContent = "Сорт: Монстера делициоза";
});

document.getElementById("diseaseBtn")?.addEventListener("click", () => {
  const result = document.getElementById("recognitionResult")!;
  result.textContent = "Болезнь: Паутинный клещ";
});
// === Калькулятор воды ===
let waterSetupDone = false;

function setupWaterCalculator() {
  if (waterSetupDone) return;
  waterSetupDone = true;

  document.getElementById("calcWaterBtn")?.addEventListener("click", () => {
    const temp = parseInt(document.getElementById("temperature")!.textContent!);
    const humidity = parseInt(document.getElementById("humidity")!.textContent!);
    const potSize = parseInt(document.getElementById("potSize")!.textContent!);
    const growth = (document.querySelector('input[name="growth"]:checked') as HTMLInputElement).value;

    let multiplier = 1.0;
    if (growth === "rest") multiplier *= 0.7;
    if (temp < 15) multiplier *= 0.8;
    if (humidity > 60) multiplier *= 0.85;

    const result = Math.round(potSize * 100 * multiplier);
    const resultDiv = document.getElementById("waterResult")!;
    resultDiv.textContent = `Вашему растению нужно: ${result} мл`;
  });
}

function changeValue(id: string, delta: number) {
  const el = document.getElementById(id)!;
  let value = parseInt(el.textContent || "0");
  value = Math.max(0, value + delta);
  el.textContent = value.toString();
}


// === Инициализация ===
window.addEventListener("DOMContentLoaded", () => {
  navigateTo("diagnose");
  loadPlants();
  renderWeek(currentStartDate);
  renderMonth(selectedDate);
  updateSelectedDateLabel();
});
type Plant = {
  name: string;
  photoUrl: string;
};

let plants: Plant[] = [];

function renderPlants() {
  const container = document.getElementById("plantsContainer")!;
  container.innerHTML = "";
  plants.forEach((plant, index) => {
    const card = document.createElement("div");
    card.className = "plant-card";

    const img = document.createElement("img");
    img.src = plant.photoUrl;

    const name = document.createElement("span");
    name.textContent = plant.name;

    card.appendChild(img);
    card.appendChild(name);
    container.appendChild(card);
  });
function updatePlantOptions() {
  const select = document.getElementById("plantSelect") as HTMLSelectElement;
  if (!select) return;
  select.innerHTML = "";
  plants.forEach(p => {
    const option = document.createElement("option");
    option.value = p.name;
    option.textContent = p.name;
    select.appendChild(option);
  });
}
  updatePlantOptions(); // для календаря
}

function savePlants() {
  localStorage.setItem("myPlants", JSON.stringify(plants));
}

function loadPlants() {
  const stored = localStorage.getItem("myPlants");
  if (stored) {
    plants = JSON.parse(stored);
    renderPlants();
  }
}

// Добавить по названию
document.getElementById("addByNameBtn")?.addEventListener("click", () => {
  const name = prompt("Введите название растения:");
  if (!name) return;

  const plant: Plant = {
    name,
    photoUrl: "icons/placeholder.png" // заглушка
  };
  plants.push(plant);
  savePlants();
  renderPlants();
});

// Добавить по фото
document.getElementById("addByPhotoBtn")?.addEventListener("click", () => {
  const input = document.getElementById("plantPhotoInput") as HTMLInputElement;
  input.click();
});

document.getElementById("plantPhotoInput")?.addEventListener("change", (event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || !input.files[0]) return;

  const file = input.files[0];
  const reader = new FileReader();
  reader.onload = () => {
    const name = prompt("Введите название растения:");
    if (!name) return;

    const plant: Plant = {
      name,
      photoUrl: reader.result as string
    };
    plants.push(plant);
    savePlants();
    renderPlants();
  };
  reader.readAsDataURL(file);
});