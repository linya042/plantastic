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
const tg = window.Telegram.WebApp;
tg.ready();
const imageInput = document.getElementById("imageInput");
const uploadButton = document.getElementById("uploadButton");
const resultDiv = document.getElementById("result");
const user = tg.initDataUnsafe.user;
if (user) {
    resultDiv.innerHTML = 'Привет, <strong>${user.first_name}</strong>!';
}
uploadButton.addEventListener("click", () => __awaiter(void 0, void 0, void 0, function* () {
    var _a, _b;
    const file = (_a = imageInput.files) === null || _a === void 0 ? void 0 : _a[0];
    if (!file) {
        resultDiv.textContent = "Пожалуйста, выбери изображение.";
        return;
    }
    const formData = new FormData();
    formData.append("image", file);
    formData.append("user_id", String((_b = user === null || user === void 0 ? void 0 : user.id) !== null && _b !== void 0 ? _b : "unknown"));
    try {
        const response = yield fetch("https://example.com/analyze", {
            method: "POST",
            body: formData,
        });
        if (!response.ok)
            throw new Error("Ошибка при отправке");
        const data = yield response.json();
        resultDiv.textContent = 'Диагноз: ${data.result}';
    }
    catch (err) {
        resultDiv.textContent = "Произошла ошибка при анализе.";
        console.error(err);
    }
}));
function navigateTo(pageId) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(p => p.classList.remove('active'));
    const target = document.getElementById(pageId);
    if (target)
        target.classList.add('active');
}
window.addEventListener('DOMContentLoaded', () => {
    navigateTo('diagnose');
});
