"use strict";
var _a, _b;
// Telegram init
const tg = window.Telegram.WebApp;
tg.ready();
// Переход между страницами
function navigateTo(pageId) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    const target = document.getElementById(pageId);
    if (target)
        target.classList.add('active');
    const calendarWidget = document.getElementById('calendarWidget');
    const tasksToday = document.getElementById('tasksToday');
    if (pageId === 'diagnose') {
        calendarWidget.style.display = 'block';
        tasksToday.style.display = 'block';
    }
    else {
        calendarWidget.style.display = 'none';
        tasksToday.style.display = 'none';
    }
}
// ======= Календарь =======
const daysOfWeek = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'];
const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
let currentStartDate = new Date();
currentStartDate.setDate(currentStartDate.getDate() - ((currentStartDate.getDay() + 6) % 7)); // сдвиг на понедельник
function renderWeek(startDate) {
    const container = document.getElementById('calendarDays');
    const monthSpan = document.getElementById('calendarMonth');
    container.innerHTML = '';
    for (let i = 0; i < 7; i++) {
        const day = new Date(startDate);
        day.setDate(startDate.getDate() + i);
        const isToday = isSameDay(day, new Date());
        const dayDiv = document.createElement('div');
        dayDiv.classList.add('calendar-day');
        if (isToday)
            dayDiv.classList.add('today');
        const weekday = daysOfWeek[(day.getDay() + 6) % 7];
        dayDiv.innerHTML = `
      <div class="weekday">${weekday}</div>
      <div class="date">${day.getDate()}</div>
    `;
        container.appendChild(dayDiv);
    }
    monthSpan.textContent = monthNames[startDate.getMonth()];
}
function isSameDay(d1, d2) {
    return d1.getDate() === d2.getDate() &&
        d1.getMonth() === d2.getMonth() &&
        d1.getFullYear() === d2.getFullYear();
}
// Кнопки переключения недель
(_a = document.getElementById('prevWeekBtn')) === null || _a === void 0 ? void 0 : _a.addEventListener('click', () => {
    currentStartDate.setDate(currentStartDate.getDate() - 7);
    renderWeek(currentStartDate);
});
(_b = document.getElementById('nextWeekBtn')) === null || _b === void 0 ? void 0 : _b.addEventListener('click', () => {
    currentStartDate.setDate(currentStartDate.getDate() + 7);
    renderWeek(currentStartDate);
});
// Запуск при загрузке
window.addEventListener('DOMContentLoaded', () => {
    renderWeek(currentStartDate);
    navigateTo('diagnose');
});
