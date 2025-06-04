"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m;
let selectedCalendarDate = null;
function renderTasksForSelectedDate() {
    const list = document.getElementById("calendarTaskList");
    if (!list || !selectedCalendarDate)
        return;
    list.innerHTML = "";
    fetchTasksByDate(formatDate(selectedCalendarDate)).then(tasks => {
        tasks.forEach(task => {
            const li = document.createElement("li");
            li.textContent = task;
            list.appendChild(li);
        });
    });
}
function renderCalendarTasksForDate(dateStr) {
    return __awaiter(this, void 0, void 0, function* () {
        const taskList = document.getElementById("calendarTaskList");
        if (!taskList)
            return;
        taskList.innerHTML = "";
        const tasks = yield fetchTasksByDate(dateStr);
        tasks.forEach(t => {
            const li = document.createElement("li");
            li.textContent = t;
            taskList.appendChild(li);
        });
    });
}
document.addEventListener("DOMContentLoaded", () => {
    const addEventButton = document.getElementById("addEventButton");
    if (addEventButton) {
        addEventButton.addEventListener("click", () => __awaiter(void 0, void 0, void 0, function* () {
            if (!selectedCalendarDate)
                return;
            const dateStr = formatDate(selectedCalendarDate);
            const typeSelect = document.getElementById("eventType");
            const plantSelect = document.getElementById("plantSelect");
            const type = typeSelect.value;
            const plant = plantSelect.value;
            yield createEvent(dateStr, type, plant);
            yield renderCalendarTasksForDate(dateStr);
        }));
    }
});
function createEvent(dateStr, type, plant) {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const response = yield fetch("https://plantastic-backend.onrender.com/tasks", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    date: dateStr,
                    text: `${type} — ${plant}`
                })
            });
            if (!response.ok) {
                throw new Error("Не удалось добавить событие");
            }
        }
        catch (error) {
            console.error("Ошибка при добавлении события:", error);
        }
    });
}
const API_URL = "https://plantastic-backend.onrender.com";
const daysOfWeek = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"];
const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
function navigateTo(pageId) {
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    const target = document.getElementById(pageId);
    if (target) {
        target.classList.add("active");
        if (pageId === "water")
            setupWaterCalculator();
    }
}
function formatDate(date) {
    return date.toISOString().split("T")[0];
}
function isSameDay(d1, d2) {
    return d1.getDate() === d2.getDate() &&
        d1.getMonth() === d2.getMonth() &&
        d1.getFullYear() === d2.getFullYear();
}
function fetchTasksByDate(dateStr) {
    return __awaiter(this, void 0, void 0, function* () {
        const res = yield fetch(`${API_URL}/tasks?date=${dateStr}`);
        return res.ok ? (yield res.json()).map((t) => t.text) : [];
    });
}
function addTask(dateStr, text) {
    return __awaiter(this, void 0, void 0, function* () {
        yield fetch(`${API_URL}/tasks`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ date: dateStr, text })
        });
    });
}
// === Виджет недели ===
let currentStartDate = new Date();
currentStartDate.setDate(currentStartDate.getDate() - ((currentStartDate.getDay() + 6) % 7));
function renderWeek(startDate) {
    return __awaiter(this, void 0, void 0, function* () {
        const container = document.getElementById("calendarDays");
        const monthSpan = document.getElementById("calendarMonth");
        container.innerHTML = "";
        for (let i = 0; i < 7; i++) {
            const date = new Date(startDate);
            date.setDate(startDate.getDate() + i);
            const dateStr = formatDate(date);
            const tasks = yield fetchTasksByDate(dateStr);
            const div = document.createElement("div");
            div.classList.add("calendar-day");
            if (isSameDay(date, new Date()))
                div.classList.add("today");
            // Добавление индикатора задачи, если задачи есть
            if (tasks.length) {
                const dot = document.createElement("div");
                dot.classList.add("task-dot");
                div.appendChild(dot);
            }
            // Добавление дня недели
            const weekday = document.createElement("div");
            weekday.classList.add("weekday");
            weekday.textContent = daysOfWeek[(date.getDay() + 6) % 7];
            div.appendChild(weekday);
            // Добавление числа
            const dayNumber = document.createElement("div");
            dayNumber.classList.add("date");
            dayNumber.textContent = String(date.getDate());
            div.appendChild(dayNumber);
            div.addEventListener("click", () => __awaiter(this, void 0, void 0, function* () {
                document.querySelectorAll(".calendar-day").forEach(el => el.classList.remove("selected"));
                div.classList.add("selected");
                const tasks = yield fetchTasksByDate(dateStr);
                tasks.forEach(t => {
                    const li = document.createElement("li");
                    li.textContent = t;
                    monthSpan.appendChild(li);
                });
            }));
            container.appendChild(div);
        }
        monthSpan.textContent = monthNames[startDate.getMonth()];
    });
}
(_a = document.getElementById("prevWeekBtn")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", () => {
    currentStartDate.setDate(currentStartDate.getDate() - 7);
    renderWeek(currentStartDate);
    setupCalendarSelectionDelegated();
});
(_b = document.getElementById("nextWeekBtn")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", () => {
    currentStartDate.setDate(currentStartDate.getDate() + 7);
    renderWeek(currentStartDate);
    setupCalendarSelectionDelegated();
});
// === Календарь месяца ===
let selectedDate = new Date();
function updateSelectedDateLabel() {
    const label = document.getElementById("selectedDateLabel");
    label.textContent = `${selectedDate.getDate()} ${monthNames[selectedDate.getMonth()]}`;
}
function renderMonth(date) {
    return __awaiter(this, void 0, void 0, function* () {
        const grid = document.getElementById("monthGrid");
        const label = document.getElementById("calendarMonthName");
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const startDay = (firstDay.getDay() + 6) % 7;
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        grid.innerHTML = "";
        for (let i = 0; i < startDay; i++)
            grid.appendChild(document.createElement("div"));
        for (let day = 1; day <= daysInMonth; day++) {
            const d = new Date(year, month, day);
            const cell = document.createElement("div");
            cell.classList.add("calendar-cell");
            cell.textContent = day.toString();
            if (isSameDay(d, new Date()))
                cell.classList.add("today");
            if (isSameDay(d, selectedDate))
                cell.classList.add("selected");
            cell.addEventListener("click", () => {
                document.querySelectorAll(".calendar-cell").forEach(c => c.classList.remove("selected"));
                cell.classList.add("selected");
                selectedCalendarDate = new Date(cell.dataset.date);
                renderTasksForSelectedDate();
                document.querySelectorAll(".calendar-cell").forEach(c => c.classList.remove("selected"));
                cell.classList.add("selected");
                selectedCalendarDate = new Date(cell.dataset.date);
                renderTasksForSelectedDate();
                updateSelectedDateLabel();
                renderMonth(selectedDate);
            });
            grid.appendChild(cell);
        }
        label.textContent = `${monthNames[month]} ${year}`;
    });
}
(_c = document.getElementById("prevMonth")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", () => {
    selectedDate.setMonth(selectedDate.getMonth() - 1);
    renderMonth(selectedDate);
    updateSelectedDateLabel();
});
(_d = document.getElementById("nextMonth")) === null || _d === void 0 ? void 0 : _d.addEventListener("click", () => {
    selectedDate.setMonth(selectedDate.getMonth() + 1);
    renderMonth(selectedDate);
    updateSelectedDateLabel();
});
(_e = document.getElementById("addEventButton")) === null || _e === void 0 ? void 0 : _e.addEventListener("click", () => __awaiter(void 0, void 0, void 0, function* () {
    const type = document.getElementById("eventType").value;
    const plant = document.getElementById("plantSelect").value;
    const text = `${type}: ${plant}`;
    const dateStr = formatDate(selectedDate);
    yield addTask(dateStr, text);
    alert("Событие добавлено!");
}));
// === Распознавание по фото (заглушка) ===
(_f = document.getElementById("infoBtn")) === null || _f === void 0 ? void 0 : _f.addEventListener("click", () => {
    const result = document.getElementById("recognitionResult");
    result.textContent = "Информация: Это Монстера. Любит рассеянный свет.";
});
(_g = document.getElementById("sortBtn")) === null || _g === void 0 ? void 0 : _g.addEventListener("click", () => {
    const result = document.getElementById("recognitionResult");
    result.textContent = "Сорт: Монстера делициоза";
});
(_h = document.getElementById("diseaseBtn")) === null || _h === void 0 ? void 0 : _h.addEventListener("click", () => {
    const result = document.getElementById("recognitionResult");
    result.textContent = "Болезнь: Паутинный клещ";
});
// === Калькулятор воды ===
let waterSetupDone = false;
function setupWaterCalculator() {
    var _a;
    if (waterSetupDone)
        return;
    waterSetupDone = true;
    (_a = document.getElementById("calcWaterBtn")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", () => {
        const temp = parseInt(document.getElementById("temperature").textContent);
        const humidity = parseInt(document.getElementById("humidity").textContent);
        const potSize = parseInt(document.getElementById("potSize").textContent);
        const growth = document.querySelector('input[name="growth"]:checked').value;
        let multiplier = 1.0;
        if (growth === "rest")
            multiplier *= 0.7;
        if (temp < 15)
            multiplier *= 0.8;
        if (humidity > 60)
            multiplier *= 0.85;
        const result = Math.round(potSize * 100 * multiplier);
        const resultDiv = document.getElementById("waterResult");
        resultDiv.textContent = `Вашему растению нужно: ${result} мл`;
    });
}
function changeValue(id, delta) {
    const el = document.getElementById(id);
    let value = parseInt(el.textContent || "0");
    value = Math.max(0, value + delta);
    el.textContent = value.toString();
}
// === Инициализация ===
window.addEventListener("DOMContentLoaded", () => {
    navigateTo("diagnose");
    loadPlants();
    renderWeek(currentStartDate);
    setupCalendarSelectionDelegated();
    renderMonth(selectedDate);
    updateSelectedDateLabel();
});
let plants = [];
function renderPlants() {
    const container = document.getElementById("plantsContainer");
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
        const select = document.getElementById("plantSelect");
        if (!select)
            return;
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
(_j = document.getElementById("addByNameBtn")) === null || _j === void 0 ? void 0 : _j.addEventListener("click", () => {
    const name = prompt("Введите название растения:");
    if (!name)
        return;
    const plant = {
        name,
        photoUrl: "icons/placeholder.png" // заглушка
    };
    plants.push(plant);
    savePlants();
    renderPlants();
});
// Добавить по фото
(_k = document.getElementById("addByPhotoBtn")) === null || _k === void 0 ? void 0 : _k.addEventListener("click", () => {
    const input = document.getElementById("plantPhotoInput");
    input.click();
});
(_l = document.getElementById("plantPhotoInput")) === null || _l === void 0 ? void 0 : _l.addEventListener("change", (event) => {
    const input = event.target;
    if (!input.files || !input.files[0])
        return;
    const file = input.files[0];
    const reader = new FileReader();
    reader.onload = () => {
        const name = prompt("Введите название растения:");
        if (!name)
            return;
        const plant = {
            name,
            photoUrl: reader.result
        };
        plants.push(plant);
        savePlants();
        renderPlants();
    };
    reader.readAsDataURL(file);
});
document.querySelectorAll('.calendar-day').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.calendar-day').forEach(b => b.classList.remove('selected-day'));
        btn.classList.add('selected-day');
    });
});
function setupCalendarSelectionDelegated() {
    const container = document.getElementById("calendarDays");
    if (!container)
        return;
    container.addEventListener("click", (e) => {
        const target = e.target;
        if (target.classList.contains("calendar-day")) {
            document.querySelectorAll(".calendar-day").forEach(btn => btn.classList.remove("selected-day"));
            target.classList.add("selected-day");
        }
    });
}
(_m = document.getElementById("savePlantChanges")) === null || _m === void 0 ? void 0 : _m.addEventListener("click", () => {
    var _a;
    const newNotes = document.getElementById("editPlantNotes").value;
    const photoFile = (_a = document.getElementById("editPlantPhoto").files) === null || _a === void 0 ? void 0 : _a[0];
    if (currentlyEditingPlantName) {
        updatePlant(currentlyEditingPlantName, {
            notes: newNotes,
            photo: photoFile
        });
    }
    showPage("garden");
});
function updatePlant(name, data) {
    const plants = JSON.parse(localStorage.getItem("myPlants") || "[]");
    const index = plants.findIndex((p) => p.name === name);
    if (index !== -1) {
        if (data.notes !== undefined)
            plants[index].notes = data.notes;
        if (data.photo) {
            const reader = new FileReader();
            reader.onload = () => {
                plants[index].photoData = reader.result;
                localStorage.setItem("myPlants", JSON.stringify(plants));
                renderMyGarden();
            };
            reader.readAsDataURL(data.photo);
        }
        else {
            localStorage.setItem("myPlants", JSON.stringify(plants));
            renderMyGarden();
        }
    }
}
// === [GLOBAL VAR for editing] ===
let currentlyEditingPlantName = null;
// === [PAGE SWITCHING FUNCTION] ===
function showPage(pageId) {
    var _a;
    document.querySelectorAll(".page").forEach(page => page.classList.remove("active"));
    (_a = document.getElementById(pageId)) === null || _a === void 0 ? void 0 : _a.classList.add("active");
}
// === [RENDER MY GARDEN FUNCTION] ===
function renderMyGarden() {
    const gardenList = document.getElementById("myPlantList");
    if (!gardenList)
        return;
    gardenList.innerHTML = "";
    const plants = JSON.parse(localStorage.getItem("myPlants") || "[]");
    plants.forEach((plant) => {
        const li = document.createElement("li");
        li.textContent = plant.name;
        if (plant.photoData) {
            const img = document.createElement("img");
            img.src = plant.photoData;
            img.alt = plant.name;
            img.style.maxWidth = "100px";
            li.appendChild(img);
        }
        li.addEventListener("click", () => {
            currentlyEditingPlantName = plant.name;
            document.getElementById("editPlantName").value = plant.name;
            document.getElementById("editPlantNotes").value = plant.notes || "";
            showPage("plantEditor");
        });
        gardenList.appendChild(li);
    });
}
