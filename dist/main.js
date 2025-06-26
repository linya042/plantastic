var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};


// function loadCryptoJS() {
//     return new Promise((resolve, reject) => {
//         if (window.CryptoJS) {
//             resolve(window.CryptoJS);
//             return;
//         }
        
//         const script = document.createElement('script');
//         script.src = 'https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js';
//         script.onload = () => resolve(window.CryptoJS);
//         script.onerror = reject;
//         document.head.appendChild(script);
//     });
// }

let user_id = 1; // Значение по умолчанию
// if (typeof window !== "undefined" &&
//     window.Telegram &&
//     window.Telegram.WebApp &&
//     window.Telegram.WebApp.initDataUnsafe &&
//     window.Telegram.WebApp.initDataUnsafe.user &&
//     window.Telegram.WebApp.initDataUnsafe.user.id) {
//     user_id = Number(window.Telegram.WebApp.initDataUnsafe.user.id);
// }

var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m, _o;
const API_URL = "https://plantastic.space/api";
const daysOfWeek = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"];
const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
const monthNamesGen=["Января", "Февраля", "Марта", "Апреля", "Мая", "Июня", "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"];
const potStages = [
    "icons/загрузка_цветок0.svg",
    "icons/загрузка_цветок25.svg",
    "icons/загрузка_цветок50.svg",
    "icons/загрузка_цветок75.svg",
    "icons/загрузка_цветок100.svg"
];
const barStages = [
    "icons/загрузка0.svg",
    "icons/загрузка25.svg",
    "icons/загрузка50.svg",
    "icons/загрузка75.svg",
    "icons/загрузка100.svg"
];

const TASK_TYPE_ICONS = {
    1: "icons/полив.svg",
    2: "icons/удобрения.svg",
    3: "icons/насекомые.svg",
    4: "icons/лечить_заболевания.svg",
    5: "icons/обрезать.svg",
    6: "icons/пересаживать.svg",
    7: "icons/обрезать.svg",
    8: "icons/загрузка_цветок50.svg"
};

async function authenticateUser() {
    // Проверяем доступность Telegram WebApp API
    if (!window.Telegram || !window.Telegram.WebApp) {
        console.error('Доступ запрещен: Telegram Web App API недоступен');
        showAccessDeniedPage();
        return false;
    }

        const tg = window.Telegram.WebApp;
    
    // Проверяем, что приложение запущено в Telegram
    if (!tg.initData || tg.initData.trim() === '') {
        console.error('Доступ запрещен: отсутствуют данные инициализации Telegram');
        showAccessDeniedPage();
        return false;
    }

    // Дополнительные проверки на валидность окружения
    if (!tg.initDataUnsafe || !tg.version) {
        console.error('Доступ запрещен: неполные данные Telegram Web App');
        showAccessDeniedPage();
        return false;
    }

    try {
        const response = await fetch(`${API_URL}/auth`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData, // Отправляем initData в заголовке
            },
            body: JSON.stringify({
                initData: tg.initData,
                platform: tg.platform,
                version: tg.version,
                // Дополнительные данные для верификации
                colorScheme: tg.colorScheme,
                themeParams: tg.themeParams
            }),
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Аутентификация успешна:', data);
            
            // Сохраняем токен авторизации
            if (data.access_token) {
                sessionStorage.setItem('tg_auth_token', data.access_token);
            }
            
            if (data.user_data && data.user_data.user_id) {
                user_id = data.user_data.user_id;
            }
            
            return true;
        } else {
            const errorData = await response.json();
            console.error('Ошибка аутентификации:', errorData);
            showAccessDeniedPage();
            return false;
        }
    } catch (error) {
        console.error('Ошибка при отправке данных на сервер:', error);
        showAccessDeniedPage();
        return false;
    }
}

// Функция показа страницы с ошибкой доступа
function showAccessDeniedPage() {
    document.body.innerHTML = `
        <div style="
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            height: 100vh; 
            background: #f0f0f0; 
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 20px;
        ">
            <h1 style="color: #d32f2f; margin-bottom: 20px;">Доступ запрещен</h1>
            <p style="color: #666; margin-bottom: 30px; max-width: 400px;">
                Это приложение работает только в Telegram. 
                Пожалуйста, откройте его через Telegram бота.
            </p>
            <div style="
                background: #e3f2fd; 
                padding: 15px; 
                border-radius: 8px; 
                border-left: 4px solid #2196f3;
                max-width: 400px;
            ">
                <p style="margin: 0; color: #1976d2;">
                    Для доступа к приложению найдите нашего бота в Telegram 
                    и запустите Web App оттуда.
                </p>
            </div>
        </div>
    `;
}

// Функция для добавления токена ко всем API запросам
function makeAuthenticatedRequest(url, options = {}) {
    const token = sessionStorage.getItem('tg_auth_token');
    
    if (!token) {
        throw new Error('Токен авторизации отсутствует');
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'X-Telegram-Auth': 'true'
    };

    return fetch(url, {
        ...options,
        headers
    });
}

// Переопределяем все API вызовы для использования аутентификации
async function loadUserPlants() {
    try {
        const resp = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/plants/`);
        if (resp.ok) { 
            plants = await resp.json();
            renderPlants();
            const select = document.getElementById('plantSelect')
            select.innerHTML = '<option value="">Выберите Ваше растение</option>';
            plants.forEach(user_plant => {
                const option = document.createElement("option");
                option.value = user_plant.user_plant_id;
                option.textContent = `${user_plant.variety_name} (${user_plant.nickname})`;
                select.appendChild(option);
            });
        } else {
            plants = [];
            renderPlants();
            console.error("Ошибка загрузки растений пользователя");
        }
    } catch (error) {
        console.error("Ошибка аутентификации при загрузке растений:", error);
        // showAccessDeniedPage();
    }
}



let splashStage = 0;

function setSplashStage(stage, message = "") {
    splashStage = stage;
    document.getElementById("splash-pot").src = potStages[stage];
    document.getElementById("splash-bar").src = barStages[stage];
    if (message)
        document.getElementById("splash-label").textContent = message;
}

// Загрузка типов грунта
async function loadSoilTypes(search = "") {
    let url = `${API_URL}/soil_types/`;
    if (search) url += `?search=${encodeURIComponent(search)}`;
    const resp = await fetch(url);
    if (resp.ok) {
        return await resp.json();
    }
    return [];
}


//НОВАЯ ФУНКЦИЯ для загрузки всех сортов растений
async function loadPlantDictionary(search = "") {
    let url = `${API_URL}/variety-search/`;
    if (search) url += `?search=${encodeURIComponent(search)}`;
    const resp = await fetch(url);
    if (resp.ok) {
        return await resp.json();
    }
    return [];
}

//НОВАЯ ФУНКЦИЯ для загрузки родов растений с коэффициентом потребления воды
async function loadGenus() {
    let url = `${API_URL}/genus/`;
    const resp = await fetch(url);
    if (resp.ok) {
        return await resp.json();
    }
    return [];
}

function changeValue(type, delta) {
    const element = document.getElementById(type);
    let currentValue;
    let newValue;

    if (type === 'potSize') {
        currentValue = parseFloat(element.value);
        if (isNaN(currentValue)) {
            currentValue = parseFloat(element.min) || 2;
        }
        newValue = currentValue + delta;

        const min = parseFloat(element.min);
        const max = parseFloat(element.max);

        if (!isNaN(min) && newValue < min) {
            newValue = min;
        }
        if (!isNaN(max) && newValue > max) {
            newValue = max;
        }

        element.value = parseFloat(newValue.toFixed(1));
    } else {
        currentValue = parseInt(element.textContent);
        newValue = currentValue + delta;
        element.textContent = newValue;
    }
}


let waterSetupDone = false;
function setupWaterCalculator() {
    var _a;
    const resultDiv = document.getElementById("waterResult");
    resultDiv.style = "display:none";
    if (waterSetupDone)
        return;
    waterSetupDone = true;
    
    (_a = document.getElementById("calcWaterBtn")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", () => {
        const genusCoefficient = parseFloat(document.getElementById("plantType").value);
        const soilCoefficient = parseFloat(document.getElementById("soilType").value);
        const temp = parseFloat(document.getElementById("temperature").textContent);
        const humidity = parseFloat(document.getElementById("humidity").textContent);
        const potSize = parseFloat(document.getElementById("potSize").value); 
        const growth = document.querySelector('input[name="growth"]:checked').value;
        
        let growthMultiplier = 1.4;
        if (growth === "rest")
            growthMultiplier = 0.7;

        const resultWater = Math.round(potSize * 0.2 * (1 + 0.03*(temp-20)) * (1 - 0.008*(humidity-55)) * growthMultiplier * soilCoefficient * genusCoefficient * 1000);
        const resultFrequency = Math.round(4 * 1/(1 + 0.03*(temp-20)) * 1/(1 - 0.008*(humidity-55)) * 1/growthMultiplier * 1/soilCoefficient * 1/genusCoefficient);
        resultDiv.textContent = `Вашему растению нужно: ${resultWater} мл. Частота полива: раз в ${resultFrequency} дней`;
        resultDiv.style = "";
    });
}

function showRecognitionResult(type, result, resultDivOverride = null) {
    let headerDiv, resultDiv;
    if (type === "plant") {
        headerDiv = document.getElementById("recognitionHeader");
        resultDiv = document.getElementById("recognitionResult");
        headerDiv.textContent = "Распознанные растения";
    } else if (type === "disease") {
        headerDiv = document.getElementById("diseaseRecognitionHeader");
        resultDiv = document.getElementById("diseaseRecognitionResult");
        headerDiv.textContent = "Распознанные болезни";
    }

    if (resultDivOverride) {
        resultDiv = resultDivOverride;
    }

    if (headerDiv) headerDiv.innerHTML = "";
    if (resultDiv) resultDiv.innerHTML = "";

    // if (typeof result === "string") {
    //     resultDiv.textContent = result;
    //     return;
    // }
    // if (!Array.isArray(result) || result.length === 0) {
    //     resultDiv.textContent = "Нет результатов распознавания";
    //     return;
    // }

    if (typeof result === "string" || !Array.isArray(result) || result.length === 0) {
        resultDiv.textContent = typeof result === "string" ? result : "Нет результатов распознавания";
        return;
    }

    result.forEach(item => {
        const block = document.createElement("div");
        block.className = "recognition-item";
        block.style.cursor = "pointer";

        // Картинка
        const img = document.createElement("img");
        img.className = "recognition-img";
        img.src = (item.images && item.images.length > 0) ? item.images[0] : "icons/plant.svg";
        img.alt = item.item_name;

        // Контейнер для текста
        const textContainer = document.createElement("div");
        textContainer.className = "recognition-text";

        // Название растения/болезни
        const name = document.createElement("div");
        name.className = "recognition-name";
        name.textContent = item.item_name;

        // Вероятность
        const confidence = document.createElement("div");
        confidence.className = "recognition-confidence";
        confidence.textContent = `Вероятность: ${item.confidence}%`;
        textContainer.appendChild(name);
        textContainer.appendChild(confidence);

        block.appendChild(img);
        block.appendChild(textContainer);

        block.addEventListener("click", () => {
            if (type === 'plant') {
                showPlantInfoModal(item.item_id);
            } else if (type === 'disease') {
                showDiseaseInfoModal(item.item_id);
            }
        });

        resultDiv.appendChild(block);
    });
}

async function showPlantInfoModal(variety_id) {
    const infoDiv = document.getElementById("plantInfoContent");
    infoDiv.innerHTML = "Загрузка...";
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById("plantInfoSection").classList.add('active');
    try {
        const response = await fetch(`${API_URL}/plants-by-variety/${variety_id}`);
        if (response.ok) {
            const data = await response.json();

            infoDiv.innerHTML = `
                <h2>${data.common_name_ru || data.scientific_name}</h2>
                <img src="${(data.images && data.images.length > 0) ? data.images[0] : "icons/plant.svg"}" style="max-width:200px; margin-bottom:15px; border-radius:8px;">
                <div><b>Научное имя:</b> ${data.scientific_name}</div>
                <div><b>Синонимы:</b> ${data.synonyms || '-'}</div>
                <div><b>Семейство:</b> ${data.family || '-'}</div>
                <div><b>Род:</b> ${data.genus || '-'}</div>
                <div><b>Описание:</b> ${data.description || '-'}</div>
                <div><b>Максимальная высота(см):</b> ${data.max_height_cm || '-'}</div>
                <div><b>Тип роста:</b> ${data.growth_rate || '-'}</div>
                <div><b>Условия:</b> ${data.temperature_range || '-'}</div>
                <div><b>Рекомендуемая влажность:</b> ${data.humidity_requirements || '-'}</div>
                <div><b>Рекомендуемый грунт:</b> ${data.soil_requirements || '-'}</div>
                <div><b>Рекомендуемая частота пересадки:</b> ${data.repotting_frequency || '-'}</div>
                <div><b>Способы размножения:</b> ${data.propagation_methods || '-'}</div>
                <div><b>Токсичность:</b> ${data.toxicity || '-'}</div>
                <div><b>Забота о растении:</b> ${data.care_features || '-'}</div>
                <div><b>Полив:</b> ${data.watering_frequency || '-'}</div>
                <div><b>Освещение:</b> ${data.light_requirements || '-'}</div>
            `;
        } else {
            infoDiv.textContent = "Ошибка загрузки информации о растении";
        }
    } catch (error) {
        infoDiv.textContent = "Ошибка при запросе данных";
    }
}

async function showDiseaseInfoModal(disease_id) {
    const infoDiv = document.getElementById("diseaseInfoContent");
    infoDiv.innerHTML = "Загрузка...";
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById("diseaseInfoSection").classList.add('active');

    try {
        const response = await fetch(`${API_URL}/get_disease/${disease_id}`);

        if (response.ok) {
            const data = await response.json();

            let carouselHTML = '';
            if (data.disease_images_url_list && data.disease_images_url_list.length > 0) {
                const maxImages = 20;
                const limitedImages = data.disease_images_url_list.slice(0, maxImages);

                if (limitedImages.length > 0) {
                    carouselHTML = `
                        <div class="carousel-container" style="max-width: 100%; margin: 0 auto 20px; overflow: hidden;">
                            <div class="carousel-track" style="display: flex; gap: 10px; overflow-x: auto; padding: 10px 0; scroll-behavior: smooth; -webkit-overflow-scrolling: touch;">
                                ${limitedImages.map((img, index) =>
                                    `<img src="${img}" style="min-width: 120px; width: 120px; height: 120px; object-fit: cover; border-radius: 8px; cursor: pointer; transition: transform 0.2s;"
                                        onmouseover="this.style.transform='scale(1.05)'"
                                        onmouseout="this.style.transform='scale(1)'"
                                        onclick="openImageModal('${img}')">`
                                ).join('')}
                            </div>
                            ${data.disease_images_url_list.length > maxImages ? `<p style="text-align: center; color: #666; font-size: 14px; margin-top: 10px;">Показано ${maxImages} из ${data.disease_images_url_list.length} изображений</p>` : ''}
                        </div>
                    `;
                }
            }

            infoDiv.innerHTML = `
                <h2>${data.disease_name_ru || 'Название болезни отсутствует'}</h2>
                ${carouselHTML || `<img src="icons/plant.svg" style="max-width:200px; margin-bottom:15px; border-radius:8px;">`}
                <div><b>Описание:</b> ${data.description || '-'}</div>
                <div><b>Симптомы:</b> ${data.symptoms_description || '-'}</div>
                <div><b>Методы лечения:</b> ${data.treatment || '-'}</div>
                <div><b>Меры профилактики:</b> ${data.prevention || '-'}</div>
                <button id="backToPreviousSectionBtn" class="btn btn--back" style="margin-top:18px;">Назад</button>
            `;

            if (carouselHTML) {
                setupImageModal();
            }

            document.getElementById("backToPreviousSectionBtn").onclick = () => showPage("diseaseResultSection");
        } else {
            infoDiv.textContent = "Ошибка загрузки информации о болезни";
        }
    } catch (error) {
        console.error("Ошибка при запросе данных о болезни:", error);
        infoDiv.textContent = "Ошибка при запросе данных";
    }
}

// Функция для кнопок смены значения температуры, влажности и объёма горшка:
function changeValue(id, delta) {
    const el = document.getElementById(id);
    let value = parseInt(el.textContent || "0");
    value = Math.max(0, value + delta);
    el.textContent = value.toString();
}
function navigateTo(pageId) {
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    const target = document.getElementById(pageId);
    if (target) {
        target.classList.add("active");
        if (pageId === "water")
            setupWaterCalculator();
    }
    document.querySelectorAll(".bottom-nav button").forEach(btn => btn.classList.remove("active"));
    let navIndex = 0;
    if      (pageId === 'recognition') navIndex = 0;
    else if (pageId === 'calendar')    navIndex = 1;
    else if (pageId === 'diagnose')    navIndex = 2;
    else if (pageId === 'water')       navIndex = 3;
    else if (pageId === 'profile')     navIndex = 4;
    document.querySelectorAll(".bottom-nav button")[navIndex].classList.add("active");
}
window.navigateTo = navigateTo;

function formatDate(date) {
    return date.toISOString().split("T")[0];
}


function isSameDay(d1, d2) {
    return d1.getDate() === d2.getDate() &&
        d1.getMonth() === d2.getMonth() &&
        d1.getFullYear() === d2.getFullYear();
}

// --- TASKS ---
async function fetchTasksByDate(dateStr) {
    try {
        const res = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/tasks/daily/?date=${dateStr}`);
        const weekTask = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/tasks/weekly/?start_date=${dateStr}`);
        let wktsk
        if (weekTask.ok) {
            wktsk = weekTask.json()
        }

        if (res.ok) {
            return (await res.json()).map((t) => t.title);
        } else {
            console.warn(`Failed to fetch tasks for date ${dateStr}: ${res.status} ${res.statusText}`);
            return []; 
        }
    } catch (error) {
        console.warn(`Error fetching tasks for date ${dateStr} (likely no token or network issue): ${error.message}`);
        return [];
    }
}

async function addTask() {

    const user_plant_id = document.getElementById("plantSelect").value;
    const task_type_id = document.getElementById("taskTypeSelect").value;
    const due_date = selectedDate.toISOString();

    if (!user_plant_id || !task_type_id) {
        alert("Укажите тип задачи и Ваше растение");
        return;
    }

    const body = {
        user_plant_id,
        task_type_id,
        due_date
    }

    try {
        const resp = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/tasks/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        if (!resp.ok) {
            const errorData = await resp.json();
            console.error("Ошибка сервера:", errorData);
            throw new Error(`Ошибка ${resp.status}: ${errorData.detail || 'Неизвестная ошибка'}`);
        }

        const newTask = await resp.json();
        console.log("Задача создана:", newTask);
        
        alert("Событие добавлено!");
        await renderWeek(currentStartDate);
        
    } catch (error) {
        console.error("Ошибка при добавлении задачи:", error);
        alert(`Ошибка при добавлении задачи: ${error.message}`);
    }
}


async function toggleTaskCompletion(taskId, isCompleted) {
    try {
        let endpoint;
        let method = "POST";
        if (isCompleted) {
            endpoint = `${API_URL}/users/${user_id}/tasks/${taskId}/complete`;
            console.log(`Отметить задачу ${taskId} как выполненную.`);
        } else {
            endpoint = `${API_URL}/users/${user_id}/tasks/${taskId}/uncomplete`;
            console.log(`Отменить выполнение задачи ${taskId}.`);
        }
        const resp = await makeAuthenticatedRequest(endpoint, {
            method: method,
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (!resp.ok) {
            const errorData = await resp.json();
            console.error("Ошибка сервера при обновлении статуса задачи:", errorData);
            throw new Error(`Ошибка ${resp.status}: ${errorData.detail || 'Неизвестная ошибка'}`);
        }

        console.log(`Задача ${taskId} обновлена: is_completed = ${isCompleted}`);
        // Нет необходимости в alert, так как UI обновится автоматически
    } catch (error) {
        console.error("Ошибка при обновлении статуса задачи:", error);
        alert(`Ошибка при обновлении статуса задачи: ${error.message}`);
    }
}


//---Виджет недели---
let currentStartDate = new Date();
currentStartDate.setDate(currentStartDate.getDate() - ((currentStartDate.getDay() + 6) % 7));
let selectedWeekDate = null;
let weekTasksData = {}; // Кэш для задач недели

// Функция для загрузки задач на неделю
async function fetchWeekTasks(startDate) {
    try {
        const dateStr = formatDate(startDate);
        const res = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/tasks/grouped/?start_date=${dateStr}&days=7`);
        
        if (res.ok) {
            const data = await res.json();
            // Преобразуем массив в объект для быстрого доступа по дате
            const tasksMap = {};
            data.forEach(dayData => {
                tasksMap[dayData.date] = dayData.tasks;
            });
            return tasksMap;
        } else {
            console.warn(`Failed to fetch week tasks starting from ${dateStr}: ${res.status} ${res.statusText}`);
            return {};
        }
    } catch (error) {
        console.warn(`Error fetching week tasks starting from ${dateStr}: ${error.message}`);
        return {};
    }
}

// Функция для получения задач конкретного дня из кэша
function getTasksForDate(date) {
    const dateStr = formatDate(date);
    return weekTasksData[dateStr] || [];
}

// Функция для получения заголовков задач
function getTaskTitlesForDate(date) {
    const tasks = getTasksForDate(date);
    return tasks.map(task => {
        const plant = plants.find(plant => plant.user_plant_id === task.user_plant_id);
        let plantDetails = '';
        if (plant) {
            plantDetails = `${plant.variety_name || 'N/A'} (${plant.nickname})`;
        }

        return `${task.task_type.task_name} | ${plantDetails}`;
    });
}

async  function renderWeek(startDate) {
    const container = document.getElementById("calendarDays");
    const monthSpan = document.getElementById("calendarMonth");

    // Загружаем задачи на всю неделю одним запросом
    weekTasksData = await fetchWeekTasks(startDate);

    container.innerHTML = "";
    let todayCell = null; // Для хранения ячейки "сегодня"
    let mondayCell = null;

    for (let i = 0; i < 7; i++) {
        const date = new Date(startDate);
        date.setDate(startDate.getDate() + i);
        const dateStr = formatDate(date);

        // Получаем задачи для текущего дня из кэша
        const tasks = getTasksForDate(date);
        const taskTitles = getTaskTitlesForDate(date);

        const div = document.createElement("div");
        div.classList.add("calendar-day");

        if (isSameDay(date, new Date())) {
            div.classList.add("today");
            todayCell = div;
        }


        if (selectedWeekDate && isSameDay(date, selectedWeekDate))
            div.classList.add("selected");

        // Показываем точку, если есть задачи
        if (tasks.length > 0) {
            const dot = document.createElement("div");
            dot.classList.add("task-dot");
            div.appendChild(dot);
        }

        const weekday = document.createElement("div");
        weekday.classList.add("weekday");
        weekday.textContent = daysOfWeek[(date.getDay() + 6) % 7];
        div.appendChild(weekday);

        const dayNumber = document.createElement("div");
        dayNumber.classList.add("date");
        dayNumber.textContent = String(date.getDate());
        div.appendChild(dayNumber);
        if (i === 0) {
            mondayCell = div;
        }

        // Обработчик клика
        div.addEventListener("click", async () => {
            document.querySelectorAll(".calendar-day").forEach(d => d.classList.remove("selected"));
            div.classList.add("selected");
            selectedWeekDate = new Date(date);

            const taskList = document.getElementById("tasksList");
            taskList.innerHTML = "";

            const clickedTasks = getTasksForDate(date);

            if (clickedTasks.length === 0) {
                taskList.innerHTML = "<div class='task-empty'>Задач нет</div>";
                return;
            }

            clickedTasks.forEach(task => {
                const block = document.createElement("div");
                block.className = "task-block";
                if (task.is_completed) {
                    block.classList.add("completed");
                }

                const leftSection = document.createElement("div");
                leftSection.className = "task-left-section";
                const icon = document.createElement("img");
                icon.src = TASK_TYPE_ICONS[task.task_type_id] || "icons/загрузка_цветок50.svg";
                icon.alt = task.task_type.task_name;
                icon.className = "task-icon";
                leftSection.appendChild(icon);

                const textContent = document.createElement("div");
                textContent.className = "task-text-content";

                const taskTypeName = document.createElement("div");
                taskTypeName.className = "task-type-name";
                taskTypeName.textContent = task.task_type.task_name;
                textContent.appendChild(taskTypeName);

                const plantName = document.createElement("div");
                plantName.className = "task-plant-name";
                const plant = plants.find(p => p.user_plant_id === task.user_plant_id);
                if (plant) {
                    plantName.textContent = `${plant.nickname} (${plant.variety_name})`;
                } else {
                    plantName.textContent = "Растение не найдено";
                }
                textContent.appendChild(plantName);

                leftSection.appendChild(textContent);
                block.appendChild(leftSection);

                const rightSection = document.createElement("div");
                rightSection.className = "task-right-section";

                const completeButton = document.createElement("div");
                completeButton.className = "task-complete-button";
                if (task.is_completed) {
                    completeButton.innerHTML = "&#10003;";
                }
                completeButton.addEventListener("click", async (event) => {
                    event.stopPropagation(); // Предотвращаем клик по родительскому элементу дня
                    await toggleTaskCompletion(task.id, !task.is_completed);
                    await renderWeek(currentStartDate);
                    const selectedDayElement = document.querySelector('.calendar-day.selected');
                    if (selectedDayElement) {
                        selectedDayElement.click();
                    }
                });
                rightSection.appendChild(completeButton);
                block.appendChild(rightSection);

                taskList.appendChild(block);
            });
        });
        container.appendChild(div);
    }

    monthSpan.textContent = monthNames[startDate.getMonth()];

    if (todayCell) {
        todayCell.click();  // Если есть "сегодня", кликаем по нему
    } else if (mondayCell) {
        mondayCell.click();  // Иначе, если "сегодня" нет на этой неделе, кликаем по понедельнику
    }
}

(_c = document.getElementById("prevWeekBtn")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", () => {
    currentStartDate.setDate(currentStartDate.getDate() - 7);
    renderWeek(currentStartDate);
});

(_d = document.getElementById("nextWeekBtn")) === null || _d === void 0 ? void 0 : _d.addEventListener("click", () => {
    currentStartDate.setDate(currentStartDate.getDate() + 7);
    renderWeek(currentStartDate);
});

// Обработчик кнопки "Сегодня" для недельного календаря
document.getElementById("todayBtnWeek")?.addEventListener("click", async () => {
    const today = new Date();
    currentStartDate = new Date(today);
    currentStartDate.setDate(today.getDate() - ((today.getDay() + 6) % 7));
    selectedWeekDate = new Date(today);
    await renderWeek(currentStartDate);
});


let monthTasksData = {}; // Кэш для задач месяца

// Функция для загрузки задач на месяц
async function fetchMonthTasks(date) {
    try {
        const year = date.getFullYear();
        const month = date.getMonth();
        
        // Определяем первый день календарной сетки (может быть из предыдущего месяца)
        const firstDayOfMonth = new Date(year, month, 1);
        const startDay = (firstDayOfMonth.getDay() + 6) % 7;
        const startDate = new Date(year, month, 1 - startDay);
        
        // Загружаем задачи на 42 дня (полная календарная сетка)
        const startDateStr = formatDate(startDate);
        const res = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/tasks/grouped/?start_date=${startDateStr}&days=42`);
        
        if (res.ok) {
            const data = await res.json();
            // Преобразуем массив в объект для быстрого доступа по дате
            const tasksMap = {};
            data.forEach(dayData => {
                tasksMap[dayData.date] = dayData.tasks;
            });
            return tasksMap;
        } else {
            console.warn(`Failed to fetch month tasks for ${startDateStr}: ${res.status} ${res.statusText}`);
            return {};
        }
    } catch (error) {
        console.warn(`Error fetching month tasks: ${error.message}`);
        return {};
    }
}


// --- Календарь месяца ---
let selectedDate = new Date();

function updateSelectedDateLabel() {
    const label = document.getElementById("selectedDateLabel");
    label.textContent = `${selectedDate.getDate()} ${monthNamesGen[selectedDate.getMonth()]}`;

//     document.getElementById("todayBtn")?.addEventListener("click", () => {
//         selectedDate = new Date();
//         renderMonth(selectedDate);
//         updateSelectedDateLabel();
// });
}

async function renderMonth(date) {
    const grid = document.getElementById("monthGrid");
    const label = document.getElementById("calendarMonthName");
    const year = date.getFullYear();
    const month = date.getMonth();

    const firstDayOfMonth = new Date(year, month, 1);
    const startDay = (firstDayOfMonth.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const totalCells = 42;
    const firstDateToShow = new Date(year, month, 1 - startDay);

    // Загружаем задачи на весь месяц одним запросом
    monthTasksData = await fetchMonthTasks(date);

    grid.innerHTML = "";

    for (let i = 0; i < totalCells; i++) {
        const cellDate = new Date(firstDateToShow);
        cellDate.setDate(firstDateToShow.getDate() + i);

        const cell = document.createElement("div");
        cell.classList.add("calendar-cell");
        cell.textContent = cellDate.getDate().toString();

        if (isSameDay(cellDate, new Date())) cell.classList.add("today");
        if (isSameDay(cellDate, selectedDate)) cell.classList.add("selected");
        if (cellDate.getMonth() !== month) cell.classList.add("calendar-cell--other-month");

        cell.addEventListener("click", async function () {
            selectedDate = new Date(cellDate); 
            updateSelectedDateLabel();
            await renderMonth(selectedDate);

            // Обновляем недельный календарь для выбранной даты
            const startOfWeek = new Date(selectedDate);
            startOfWeek.setDate(selectedDate.getDate() - ((selectedDate.getDay() + 6) % 7));
            currentStartDate = startOfWeek;
            selectedWeekDate = new Date(selectedDate);
            
            await renderWeek(currentStartDate);
        });

        grid.appendChild(cell);
    }

    label.textContent = monthNamesGen[month] + " " + year;
}


// Обработчики для навигации по месяцам
document.getElementById("prevMonth")?.addEventListener("click", async () => {
    selectedDate.setMonth(selectedDate.getMonth() - 1);
    await renderMonth(selectedDate);
    updateSelectedDateLabel();
});

document.getElementById("nextMonth")?.addEventListener("click", async () => {
    selectedDate.setMonth(selectedDate.getMonth() + 1);
    await renderMonth(selectedDate);
    updateSelectedDateLabel();
});

// Обработчик кнопки "Сегодня" для месячного календаря
document.getElementById("todayBtnMonth")?.addEventListener("click", async () => {
    selectedDate = new Date();
    await renderMonth(selectedDate);
    updateSelectedDateLabel();
});

document.getElementById("addEventButton")?.addEventListener("click", async () => {
     await addTask();
});


let plants = [];
//const PLANT_API = `${API_URL}/plants`;
let editingPlant = null;

//ИЗМЕНЕНО - изменен эндпоинт и добавлена проверка на успех, тип функции
async function addUserPlant(plant) {
    const resp = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/add_user_plant/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(plant)
    });
    if (resp.ok) {
        const newPlant = await resp.json();
        plants.push(newPlant);
        await loadUserPlants();
        alert("Растение успешно добавлено!");
    } else {
        const error = await resp.json();
        alert("Ошибка при добавлении растения: " + (error.detail || resp.status));
    }
}
//ИЗМЕНЕНО - вся функция
async function updateUserPlant(user_plant_id, plantData) {
    const resp = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/plants/${user_plant_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(plantData)
    });
    if (resp.ok) {
        await loadUserPlants();
        alert("Растение успешно обновлено!");
    } else {
        const error = await resp.json();
        alert("Ошибка при обновлении растения: " + (error.detail || resp.status));
    }
}
//ИЗМЕНЕНО - вся функция
async function deleteUserPlant(user_plant_id) {
    await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/plants/${user_plant_id}`, { method: "DELETE" });
    await loadUserPlants();
}
// Кнопки добавить
(_j = document.getElementById("addByNameBtn")) === null || _j === void 0 ? void 0 : _j.addEventListener("click", () => openEditPlantSection({ id: 0, name: "", description: "", photo_url: "", user_id }));
(_k = document.getElementById("addByPhotoBtn")) === null || _k === void 0 ? void 0 : _k.addEventListener("click", () => openEditPlantSection({ id: 0, name: "", description: "", photo_url: "", user_id }));


// НОВАЯ ФУНКЦИЯ - для заполнения select с id=plantType
async function fillGenusSelect() {
    const genus_list = await loadGenus();
    const select = document.getElementById("plantType");
    select.innerHTML = '<option value="">Не выбрано</option>';
    genus_list.forEach(gns => {
        const option = document.createElement("option");
        option.value = gns.watering_coefficient;
        option.textContent = gns.genus;
        select.appendChild(option);
    });
}

// НОВАЯ ФУНКЦИЯ - для заполнения select с id=editPlantSectionSoilType
async function fillSoilSelectForCalculator(search = "") {
    const soil = await loadSoilTypes(search);
    const select = document.getElementById("soilType");
    select.innerHTML = '<option value="">Не выбрано</option>';
    soil.forEach(soilType => {
        const option = document.createElement("option");
        option.value = soilType.water_retention_coefficient;
        option.textContent = soilType.name_ru;
        select.appendChild(option);
    });
}

// НОВАЯ ФУНКЦИЯ - для заполнения select с id=editPlantSectionSoilType
async function fillSoilSelect(search = "") {
    const soil = await loadSoilTypes(search);
    const select = document.getElementById("editPlantSectionSoilType");
    select.innerHTML = '<option value="">Не выбрано</option>';
    soil.forEach(soilType => {
        const option = document.createElement("option");
        option.value = soilType.soil_type_id;
        option.textContent = soilType.name_ru;
        select.appendChild(option);
    });
}


// НОВАЯ ФУНКЦИЯ -  для заполнения select с id=editPlantSectionPlant
async function fillPlantSelect(select, search = "") {
    const plants = await loadPlantDictionary(search);
    select.innerHTML = '<option value="">Не выбрано</option>';
    plants.forEach(plant => {
        const option = document.createElement("option");
        option.value = plant.class_id;
        option.textContent = `${plant.variety_name} (${plant.class_label})`;
        select.appendChild(option);
    });
}

let imageChanged = false;
//ИЗМЕНЕНО - почти все в функции
async function openEditPlantSection(plant) {
    var _a, _b;
    editingPlant = plant;

    const plant_id = document.getElementById("editPlantSectionPlant");
    const nickname = document.getElementById("editPlantSectionName");
    const notes = document.getElementById("editPlantSectionDescription");
    const acquisition_date = document.getElementById("editPlantSectionAcquisitionDate");
    const soil_type_id = document.getElementById("editPlantSectionSoilType");
    const imagePreview = document.getElementById("editPlantSectionPreview");
    const imageSection = document.getElementById("editPlantSectionPhoto");

    imageChanged = false;
    
    if (editingPlant.id === 0) {
        plant_id.value = "Не выбрано";
        nickname.value = "";
        notes.value = "";
        acquisition_date.value = "";
        soil_type_id.value = "Не выбрано";
        imageSection.value = "";
        imagePreview.src = "icons/plant.svg";
    } else {
        plant_id.value = editingPlant.plant_nn_classes_id || "Не выбрано";
        nickname.value = editingPlant.nickname || "";
        notes.value = editingPlant.notes || "";
        acquisition_date.value = editingPlant.acquisition_date || "";
        soil_type_id.value = editingPlant.soil_type_id || "Не выбрано";
        imageSection.value = "";
        imagePreview.src = editingPlant.user_plant_images_list.length  !== 0 ? editingPlant.user_plant_images_list[0] : "icons/plant.svg";
    };

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('editPlantSection').classList.add('active');
};

// НОВАЯ ФУНКЦИЯ - для сжатия изображения
async function processImage(imageDataUri) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const MAX_WIDTH = 200; // Максимальная ширина изображения
            const MAX_HEIGHT = 200; // Максимальная высота изображения
            const QUALITY = 0.8; // Качество сжатия JPEG (от 0 до 1)

            let width = img.width;
            let height = img.height;

            // Изменяем размеры, сохраняя пропорции
            if (width > height) {
                if (width > MAX_WIDTH) {
                    height *= MAX_WIDTH / width;
                    width = MAX_WIDTH;
                }
            } else {
                if (height > MAX_HEIGHT) {
                    width *= MAX_HEIGHT / height;
                    height = MAX_HEIGHT;
                }
            }

            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            // Получаем сжатый Data URL
            const compressedImageDataUri = canvas.toDataURL('image/jpeg', QUALITY);

            // Устанавливаем сжатое изображение в превью
            document.getElementById("editPlantSectionPreview").src = compressedImageDataUri;
            imageChanged = true; // Устанавливаем флаг, что фото изменено (и теперь сжато)
            resolve(compressedImageDataUri); // Возвращаем сжатый Data URL
        };
        img.src = imageDataUri; // Загружаем исходный Data URL в объект Image
    });
}

// Обработчик выбора фото
(_l = document.getElementById("editPlantSectionPhoto")) === null || _l === void 0 ? void 0 : _l.addEventListener("change", (e) => {
    const input = e.target;
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = (readerEvent) => {
            processImage(readerEvent.target.result); 
        };
        reader.readAsDataURL(input.files[0]);
    }
});
// Кнопка "Сохранить" (для добавления/редактирования)
//ИЗМЕНЕНО - почти вся функция
(_l = document.getElementById("savePlantSectionBtn")) === null || _l === void 0 ? void 0 : _l.addEventListener("click", async () => {
    // const name = document.getElementById("editPlantSectionName").value;
    // const description = document.getElementById("editPlantSectionDescription").value;
    // const photo_url = document.getElementById("editPlantSectionPreview").src;
    const plant_nn_classes_id = Number(document.getElementById("editPlantSectionPlant").value);
    const nickname = document.getElementById("editPlantSectionName").value;
    const notes = document.getElementById("editPlantSectionDescription").value;
    const acquisition_date = document.getElementById("editPlantSectionAcquisitionDate").value;
    const soil_type_id = Number(document.getElementById("editPlantSectionSoilType").value);

    const plantData = {
        plant_nn_classes_id,
        nickname,
        notes,
        acquisition_date,
        soil_type_id
    };
    if (imageChanged) {
        plantData.image_data_uri = document.getElementById("editPlantSectionPreview").src;
    }

    if (editingPlant.id !== 0) {
        await updateUserPlant(editingPlant.user_plant_id, plantData);
    }
    else {
        await addUserPlant(plantData);
    }

    // Вернуться к саду:
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('profile').classList.add('active');
    editingPlant = null;
});

// Кнопка "Отмена"
(_o = document.getElementById("cancelEditPlantSectionBtn")) === null || _o === void 0 ? void 0 : _o.addEventListener("click", () => {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('profile').classList.add('active');
    editingPlant = null;
});

// Выводим все
//  растения (сад)
function renderPlants() {
    const container = document.getElementById("plantsContainer");
    container.innerHTML = "";
    plants.forEach(plant => {
        // var _a; //ИЗМЕНЕНО - удалено
        const card = document.createElement("div");
        card.className = "plant-card";
        const img = document.createElement("img");
        //ИЗМЕНЕНО - где брать изображение
        img.src = (plant.user_plant_images_list && plant.user_plant_images_list.length > 0)
            ? plant.user_plant_images_list[0]
            : "icons/plant.svg";
        img.style.maxWidth = "120px";
        const name = document.createElement("div");
        //ИЗМЕНЕНО - где брать название
        name.textContent = plant.variety_name;
        const descr = document.createElement("div");
        //ИЗМЕНЕНО - где брать заметки
        descr.textContent = plant.nickname || "";
        const editBtn = document.createElement("button");
        editBtn.textContent = "✏️";
        editBtn.onclick =  async () => await openEditPlantSection(plant); //ИЗМЕНЕНО!
        const delBtn = document.createElement("button");
        delBtn.textContent = "🗑";
        delBtn.onclick = async () => await deleteUserPlant(plant.user_plant_id); //ИЗМЕНЕНО - передается user_plant_id вместо id
        card.append(img, name, descr, editBtn, delBtn);
        container.appendChild(card);
    });
}

// --- Новый экран распознавания сорта ---
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
}

document.getElementById("sortBtn")?.addEventListener("click", () => {
    showPage("photoAdviceSection");
});

document.getElementById("adviceContinueBtn")?.addEventListener("click", () => {
    showPage("photoUploadSection");
});

document.getElementById("backToAdviceBtn")?.addEventListener("click", () => {
    showPage("recognition");
});

document.getElementById("backToUploadBtn")?.addEventListener("click", () => {
    showPage("photoUploadSection");
});

document.getElementById("uploadSortPhotoBtn")?.addEventListener("change", async (e) => {
    const input = e.target;
    const preview = document.getElementById("uploadSortPreview");
    preview.innerHTML = "";
    if (input.files && input.files[0]) {
        
        const reader = new FileReader();
        reader.onload = () => {
            preview.innerHTML = `<img src="${reader.result}" style="max-width:120px; border-radius:10px;">`;
        };
        reader.readAsDataURL(input.files[0]);

        const formData = new FormData();
        formData.append("file", input.files[0]);
        formData.append("user_id", user_id.toString());
        const response = await fetch(`${API_URL}/identify_plant`, {
            method: "POST",
            body: formData,
        });

        showPage("sortResultSection");

        const resultDiv = document.getElementById("sortResults");
        if (response.ok) {
            const data = await response.json();
            showRecognitionResult("plant", data.data, resultDiv);  
        } else {
            resultDiv.textContent = "Кажется,это не растение";
        }
    }
});

document.getElementById("closePlantInfoBtn")?.addEventListener("click", () => {
    document.getElementById("plantInfoSection").classList.remove("active");
    navigateTo('sortResultSection');
});

document.getElementById("backToDiseaseResultsBtn")?.addEventListener("click", () => {
    document.getElementById("diseaseInfoSection").classList.remove("active");
    navigateTo('diseaseResultSection');
});

document.getElementById("diseaseBtn")?.addEventListener("click", () => {
  showPage("diseaseAdviceSection");
});


document.getElementById("diseaseAdviceContinueBtn")?.addEventListener("click", () => {
  showPage("diseaseUploadSection");
});

document.getElementById("backToDiseaseAdviceBtn")?.addEventListener("click", () => {
  showPage("recognition");
});

document.getElementById("backToDiseaseUploadBtn")?.addEventListener("click", () => {
  showPage("diseaseUploadSection");
});


document.getElementById("uploadDiseasePhotoBtn")?.addEventListener("change", async (e) => {
  const input = e.target;
  const preview = document.getElementById("uploadDiseasePreview");
  preview.innerHTML = "";
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = () => {
      preview.innerHTML = `<img src="${reader.result}" style="max-width:120px; border-radius:10px;">`;
    };
    reader.readAsDataURL(input.files[0]);

    const formData = new FormData();
    formData.append("file", input.files[0]);
    formData.append("user_id", user_id.toString());
    const response = await fetch(`${API_URL}/identify_disease`, {
      method: "POST",
      body: formData,
    });

    showPage("diseaseResultSection");
    const resultDiv = document.getElementById("diseaseRecognitionResult");

    if (response.ok) {
      const data = await response.json();
      console.log("API disease result:", data); 
      showRecognitionResult("disease", data.data);
    } else {
      resultDiv.textContent = "Кажется,это не растение";
    }
  }
});

async function loadAllPlants(search = "") {
  const listDiv = document.getElementById("allPlantsList");
  listDiv.innerHTML = "Загрузка...";

  try {
    let url = `${API_URL}/plants-search/`;
    if (search && search.trim()) url += `?search=${encodeURIComponent(search.trim())}`;

    const resp = await fetch(url);
    if (!resp.ok) throw new Error("Ошибка загрузки");
    const plants = await resp.json();

    if (!Array.isArray(plants) || plants.length === 0) {
      listDiv.textContent = "В базе пока нет растений";
      return;
    }

    listDiv.innerHTML = "";
    plants.forEach(item => {
      const block = document.createElement("div");
      block.className = "recognition-item";
      block.style.cursor = "pointer";
      const img = document.createElement("img");
      img.className = "recognition-img";
      img.src = item.representative_image || "icons/plant.svg";
      img.alt = (item.common_name_ru || "") + " " + ("("+item.scientific_name+")" || "");
      // Текст
      const textDiv = document.createElement("div");
      textDiv.className = "recognition-text";
      const nameDiv = document.createElement("div");
      nameDiv.className = "recognition-name";
      nameDiv.textContent = (item.common_name_ru ? item.common_name_ru + " " : "") + ("("+item.scientific_name+")" || "");
      textDiv.appendChild(nameDiv);

      block.appendChild(img);
      block.appendChild(textDiv);

      block.addEventListener("click", () => {
        if (item.plant_id) showPlantInfoByVarietyId(item.plant_id);
        else if (item.item_id) showPlantInfoByVarietyId(item.item_id);
        else if (item.id) showPlantInfoByVarietyId(item.id);
        else alert("ID растения не найден.");
      });

      listDiv.appendChild(block);
    });
  } catch (e) {
    listDiv.textContent = "Не удалось загрузить растения";
    console.error(e);
  }
}

document.getElementById("plantSearchBtn").addEventListener("click", () => {
  const query = document.getElementById("plantSearchInput").value.trim();
  loadAllPlants(query);
});

document.getElementById("plantSearchInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const query = e.target.value.trim();
    loadAllPlants(query);
  }
});

async function showPlantInfoByVarietyId(variety_id) {
  showPage("plantInfoSectionforallplants");

  const infoDiv = document.getElementById("plantInfoContentforallplants");
  infoDiv.innerHTML = "Загрузка...";

  try {
    const resp = await fetch(`${API_URL}/plants-by-variety/${variety_id}`);
    if (!resp.ok) throw new Error("Ошибка запроса");

    const data = await resp.json();

    let carouselHTML = '';
    if (data.images && data.images.length > 0) {
      const maxImages = 20;
      const limitedImages = data.images.slice(0, maxImages);
      
      if (limitedImages.length > 0) {
        carouselHTML = `
          <div class="carousel-container" style="max-width: 100%; margin: 0 auto 20px; overflow: hidden;">
            <div class="carousel-track" style="display: flex; gap: 10px; overflow-x: auto; padding: 10px 0; scroll-behavior: smooth; -webkit-overflow-scrolling: touch;">
              ${limitedImages.map((img, index) => 
                `<img src="${img}" style="min-width: 120px; width: 120px; height: 120px; object-fit: cover; border-radius: 8px; cursor: pointer; transition: transform 0.2s;" 
                 onmouseover="this.style.transform='scale(1.05)'" 
                 onmouseout="this.style.transform='scale(1)'"
                 onclick="openImageModal('${img}')">`
              ).join('')}
            </div>
            ${data.images.length > maxImages ? `<p style="text-align: center; color: #666; font-size: 14px; margin-top: 10px;">Показано ${maxImages} из ${data.images.length} изображений</p>` : ''}
          </div>
        `;
      }
    }

    infoDiv.innerHTML = `
      <h2>${(data.common_name_ru ? data.common_name_ru + ' ' : '') + (data.scientific_name || '')}</h2>
      ${carouselHTML || `<img src="icons/plant.svg" style="max-width:200px; margin-bottom:15px; border-radius:8px;">`}
      <div><b>Научное имя:</b> ${data.scientific_name || '-'}</div>
      <div><b>Синонимы:</b> ${data.synonyms || '-'}</div>
      <div><b>Семейство:</b> ${data.family || '-'}</div>
      <div><b>Род:</b> ${data.genus || '-'}</div>
      <div><b>Описание:</b> ${data.description || '-'}</div>
      <div><b>Максимальная высота(см):</b> ${data.max_height_cm || '-'}</div>
      <div><b>Тип роста:</b> ${data.growth_rate || '-'}</div>
      <div><b>Условия:</b> ${data.temperature_range || '-'}</div>
      <div><b>Рекомендуемая влажность:</b> ${data.humidity_requirements || '-'}</div>
      <div><b>Рекомендуемый грунт:</b> ${data.soil_requirements || '-'}</div>
      <div><b>Рекомендуемая частота пересадки:</b> ${data.repotting_frequency || '-'}</div>
      <div><b>Способы размножения:</b> ${data.propagation_methods || '-'}</div>
      <div><b>Токсичность:</b> ${data.toxicity || '-'}</div>
      <div><b>Забота о растении:</b> ${data.care_features || '-'}</div>
      <div><b>Полив:</b> ${data.watering_frequency || '-'}</div>
      <div><b>Освещение:</b> ${data.light_requirements || '-'}</div>
      <button id="backToAllPlantsBtn" class="btn btn--back" style="margin-top:18px;">Назад к списку</button>
    `;

    if (carouselHTML) {
      setupImageModal();
    }

    document.getElementById("backToAllPlantsBtn").onclick = async () => showPage("allPlantsSection");
  } catch (err) {
    infoDiv.textContent = "Не удалось загрузить данные о растении";
  }
}

function setupImageModal() {
  if (!document.getElementById('imageModal')) {
    const modal = document.createElement('div');
    modal.id = 'imageModal';
    modal.style.cssText = `
      display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
      background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center;
    `;
    modal.innerHTML = `
      <div style="position: relative; max-width: 90%; max-height: 90%;">
        <img id="modalImage" style="max-width: 100%; max-height: 100%; border-radius: 8px;">
        <button onclick="closeImageModal()" style="position: absolute; top: -10px; right: -10px; background: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 16px;">×</button>
      </div>
    `;
    document.body.appendChild(modal);
  }
}

window.openImageModal = function(imageSrc) {
  const modal = document.getElementById('imageModal');
  const modalImage = document.getElementById('modalImage');
  modalImage.src = imageSrc;
  modal.style.display = 'flex';
};

window.closeImageModal = function() {
  const modal = document.getElementById('imageModal');
  modal.style.display = 'none';
};

// Закрытие модального окна по клику вне изображения
document.addEventListener('click', function(e) {
  const modal = document.getElementById('imageModal');
  if (e.target === modal) {
    closeImageModal();
  }
});

// async function loadTasksForDate(date) {
//   const tasksContainer = document.getElementById("tasksList");
//   if (!tasksContainer) return;

//   tasksContainer.innerHTML = "Загрузка задач...";

//   try {
//     const resp = await makeAuthenticatedRequest(`${API_URL}/users/${user_id}/tasks/daily/?date=${date.toISOString().split('T')[0]}`);
//     if (!resp.ok) throw new Error("Ошибка загрузки");

//     const data = await resp.json();

//     if (!data || data.length === 0) {
//       tasksContainer.innerHTML = "<div class='task-empty'>Задач нет</div>";
//       return;
//     }

//     tasksContainer.innerHTML = "";
//     data.forEach(task => {
//         const block = document.createElement("div");
//         block.className = "task-block";

//         const title = document.createElement("div");
//         title.className = "task-title";
//         title.textContent = task.title || "Без названия";

//         const description = document.createElement("div");
//         description.className = "task-desc";
//         const plant = plants.find(plant => plant.user_plant_id === task.user_plant_id);
//         let plantDetails = '';
//         if (plant) {
//             plantDetails = `${plant.variety_name || 'N/A'} (${plant.nickname})`;
//         }
//         description.textContent = `${task.task_type.task_name} | ${plantDetails}`;

//         block.appendChild(title);
//         block.appendChild(description);
//         tasksContainer.appendChild(block);
//     });
//   } catch (e) {
//     tasksContainer.innerHTML = "<div class='task-error'>Ошибка загрузки задач</div>";
//     console.error(e);
//   }
// }

let availableTaskTypes = [];

async function loadTaskTypes() {
    try {
        const resp = await fetch(`${API_URL}/task-types/`);
        if (!resp.ok) throw new Error("Ошибка загрузки типов задач");

        availableTaskTypes = await resp.json();
        const select = document.getElementById("taskTypeSelect");

        select.innerHTML = "<option value=''>Выберите тип задачи</option>";
        availableTaskTypes.forEach(type => {
            const option = document.createElement("option");
            option.value = type.task_type_id;
            option.textContent = type.task_name;
            select.appendChild(option);
        });
    } catch (e) {
        console.error("Ошибка при загрузке типов задач", e);
    }
}


document.getElementById("infoBtn")?.addEventListener("click", async () => {
  showPage("allPlantsSection");
  await loadAllPlants();
});


document.getElementById("backFromAllPlantsBtn")?.addEventListener("click", () => {
  showPage("recognition");
});

document.getElementById("adviceBackBtnrecog")?.addEventListener("click", () => {
  showPage("recognition");
});
document.getElementById("diseaseAdviceBackBtn")?.addEventListener("click", () => {
  showPage("recognition");
});

function openAllPlantsSection() {
  showPage("allPlantsSection");
  document.getElementById("plantSearchInput").value = "";
  loadAllPlants();
}


document.getElementById("openAllPlantsBtn")?.addEventListener("click", openAllPlantsSection);


// Инициализация
window.addEventListener("DOMContentLoaded", async () => {
    if (window.Telegram && Telegram.WebApp && Telegram.WebApp.expand) {

        const tg = window.Telegram.WebApp;
        const platform = tg.platform;
        const body = document.body;

        tg.ready();
        tg.expand();

        if (platform === 'ios' || platform === 'android') {
            body.classList.add('platform-mobile');
            if (tg.isVersionAtLeast('6.9')) {
                tg.requestFullscreen();
            }
        } else {
            body.classList.add('platform-desktop');
        }
    }

    try {
        

        setSplashStage(0, "Аутентификация...");
        const authenticated = await authenticateUser();
        if (authenticated) {
            setSplashStage(1, "Загрузка сада...");
            await loadUserPlants();
            await renderMonth(selectedDate);
        } else {
            setSplashStage(1, "Гость. Загрузка сада...");
            console.warn("Аутентификация не удалась. Работа в гостевом режиме.");
            // await renderWeek(currentStartDate); // Загружаем задачи для недели (они будут пустыми без аутентификации)
            // await renderMonth(selectedDate); // Загружаем задачи для месяца (они будут пустыми без аутентификации)
        }
        
        setSplashStage(2, "Загрузка интерфейса...");
        await loadTaskTypes();
        await fillPlantSelect(document.getElementById("editPlantSectionPlant")); // В карточке растения в моем саду
        await fillSoilSelect(); // В карточке растения в моем саду
        await fillGenusSelect(); // В калькуляторе воды
        await fillSoilSelectForCalculator(); // В калькуляторе воды

        setSplashStage(3, "Загрузка задач...");
        await renderWeek(currentStartDate);

        setSplashStage(3, "Загрузка календаря...");
        await renderMonth(selectedDate);

        setSplashStage(4, "Финальные штрихи...");
        await new Promise(r => setTimeout(r, 200));

        setSplashStage(4, "Готово!");
        setTimeout(() => {
            const splash = document.getElementById("splash");
            if (splash) splash.classList.remove("active");
            else console.warn("splash не найден!");

            const mainApp = document.getElementById("main-app");
            if (mainApp) mainApp.style.display = "";
            else console.warn("main-app не найден!");

            navigateTo("diagnose");
            updateSelectedDateLabel();
        }, 700);
    } catch (error) {
        console.error('Ошибка при инициализации:', error);
        setSplashStage(4, "Ошибка загрузки! Проверьте соединение.");
    }
});
