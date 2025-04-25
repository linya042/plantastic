const tg = (window as any).Telegram.WebApp;
tg.ready(); // Telegram сообщит, что мини-приложение готово

// Расширим интерфейс
const imageInput = document.getElementById("imageInput") as HTMLInputElement;
const uploadButton = document.getElementById("uploadButton") as HTMLButtonElement;
const resultDiv = document.getElementById("result") as HTMLDivElement;

// Получим данные пользователя Telegram
const user = tg.initDataUnsafe.user;
if (user) {
  resultDiv.innerHTML = 'Привет, <strong>${user.first_name}</strong>!';
}

// Обработчик кнопки
uploadButton.addEventListener("click", async () => {
  const file = imageInput.files?.[0];

  if (!file) {
    resultDiv.textContent = "Пожалуйста, выбери изображение.";
    return;
  }

  const formData = new FormData();
  formData.append("image", file);
  formData.append("user_id", String(user?.id ?? "unknown"));

  try {
    const response = await fetch("https://example.com/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Ошибка при отправке");

    const data = await response.json();
    resultDiv.textContent = 'Диагноз: ${data.result}';
  } catch (err) {
    resultDiv.textContent = "Произошла ошибка при анализе.";
    console.error(err);
  }
});