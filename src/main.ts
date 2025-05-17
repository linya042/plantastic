// Telegram init
const tg = (window as any).Telegram.WebApp;
tg.ready();

// Переход между страницами
function navigateTo(pageId: string) {
  const pages = document.querySelectorAll('.page');
  pages.forEach(page => page.classList.remove('active'));

  const target = document.getElementById(pageId);
  if (target) target.classList.add('active');

  const calendarWidget = document.getElementById('calendarWidget');
  const tasksToday = document.getElementById('tasksToday');

  if (pageId === 'diagnose') {
    calendarWidget!.style.display = 'block';
    tasksToday!.style.display = 'block';
  } else {
    calendarWidget!.style.display = 'none';
    tasksToday!.style.display = 'none';
  }
}

// ======= Календарь =======
const daysOfWeek = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'];
const monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];

let currentStartDate = new Date();
currentStartDate.setDate(currentStartDate.getDate() - ((currentStartDate.getDay() + 6) % 7)); // сдвиг на понедельник

function renderWeek(startDate: Date) {
  const container = document.getElementById('calendarDays')!;
  const monthSpan = document.getElementById('calendarMonth')!;
  container.innerHTML = '';

  for (let i = 0; i < 7; i++) {
    const day = new Date(startDate);
    day.setDate(startDate.getDate() + i);

    const isToday = isSameDay(day, new Date());

    const dayDiv = document.createElement('div');
    dayDiv.classList.add('calendar-day');
    if (isToday) dayDiv.classList.add('today');

    const weekday = daysOfWeek[(day.getDay() + 6) % 7];

    dayDiv.innerHTML = `
      <div class="weekday">${weekday}</div>
      <div class="date">${day.getDate()}</div>
    `;
    container.appendChild(dayDiv);
  }

  monthSpan.textContent = monthNames[startDate.getMonth()];
}

function isSameDay(d1: Date, d2: Date): boolean {
  return d1.getDate() === d2.getDate() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getFullYear() === d2.getFullYear();
}

// Кнопки переключения недель
document.getElementById('prevWeekBtn')?.addEventListener('click', () => {
  currentStartDate.setDate(currentStartDate.getDate() - 7);
  renderWeek(currentStartDate);
});

document.getElementById('nextWeekBtn')?.addEventListener('click', () => {
  currentStartDate.setDate(currentStartDate.getDate() + 7);
  renderWeek(currentStartDate);
});

// Запуск при загрузке
window.addEventListener('DOMContentLoaded', () => {
  renderWeek(currentStartDate);
  navigateTo('diagnose');
});
const monthGrid = document.getElementById("monthGrid")!;
const calendarMonthName = document.getElementById("calendarMonthName")!;
const selectedDateLabel = document.getElementById("selectedDateLabel")!;
let selectedDate = new Date();

function renderMonth(date: Date) {
  const year = date.getFullYear();
  const month = date.getMonth();

  const firstDay = new Date(year, month, 1);
  const startDay = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  monthGrid.innerHTML = "";

  // Пустые ячейки перед началом месяца
  for (let i = 0; i < startDay; i++) {
    const emptyCell = document.createElement("div");
    monthGrid.appendChild(emptyCell);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const cell = document.createElement("div");
    cell.textContent = day.toString();
    cell.classList.add("calendar-cell");

    const cellDate = new Date(year, month, day);
    if (isSameDay(cellDate, new Date())) cell.classList.add("today");
    if (isSameDay(cellDate, selectedDate)) cell.classList.add("selected");

    cell.addEventListener("click", () => {
      selectedDate = cellDate;
      updateSelectedDate();
      renderMonth(selectedDate); // Перерисовка, чтобы обновить выделение
    });

    monthGrid.appendChild(cell);
  }

  const monthName = monthNames[month];
  calendarMonthName.textContent = `${monthName} ${year}`;
}

function updateSelectedDate() {
  selectedDateLabel.textContent = `${selectedDate.getDate()} ${monthNames[selectedDate.getMonth()]}`;
}

// Кнопки переключения месяцев
document.getElementById("prevMonth")?.addEventListener("click", () => {
  selectedDate.setMonth(selectedDate.getMonth() - 1);
  renderMonth(selectedDate);
  updateSelectedDate();
});

document.getElementById("nextMonth")?.addEventListener("click", () => {
  selectedDate.setMonth(selectedDate.getMonth() + 1);
  renderMonth(selectedDate);
  updateSelectedDate();
});

// Добавить событие
document.getElementById("addEventButton")?.addEventListener("click", () => {
  const type = (document.getElementById("eventType") as HTMLSelectElement).value;
  const plant = (document.getElementById("plantSelect") as HTMLSelectElement).value;
  alert(`Добавлено: ${type} — ${plant} на ${selectedDate.toLocaleDateString("ru-RU")}`);
});

renderMonth(selectedDate);
updateSelectedDate();