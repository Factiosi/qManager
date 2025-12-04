# qManager v1.9.2

**Универсальный менеджер PDF файлов** с поддержкой разделения, переименования и организации документов на основе данных Excel.

## 🚀 **Основной функционал**

### **PDF Splitter**
- Автоматическое разделение PDF по зелёным страницам (АКФК)
- Настраиваемый порог определения зелёного цвета
- Поддержка Poppler для конвертации страниц

### **PDF Renamer**
- Переименование PDF файлов по номерам контейнеров
- OCR распознавание текста с помощью Tesseract
- Поддержка файлов "Logos" и "Отчёт"

### **PDF Organizer**
- Организация PDF по папкам на основе данных Excel
- Автоматическое создание структуры папок
- Объединение файлов в единые PDF по юнитам

### **Playwright Integration**
- Готовность к интеграции с Playwright для веб-автоматизации

## 🛠 **Технические требования**

- **Python 3.10.11** (строго)
- **Windows 10/11** (x64)
- **PySide6** для GUI
- **Poppler** для работы с PDF
- **Tesseract OCR** для распознавания текста

## 📦 **Установка**

### **Для разработчиков:**
```bash
git clone <repository>
cd qManager
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python start.py
```

### **Для пользователей:**
1. Скачайте последний релиз
2. Запустите `qManager-Setup.exe`
3. Следуйте инструкциям установщика

## 🔨 **Сборка**

### **Nuitka (рекомендуется):**

**Обычная сборка (без консоли, для пользователей):**
```bash
python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=pyside6 --windows-icon-from-ico=src/resources/Icon.ico --include-data-dir=src/resources=src/resources --include-data-dir=vendor=vendor --output-dir=dist --output-filename=qManager.exe start.py
```

### **PyInstaller:**
```bash
pyinstaller --onefile --windowed --add-data "src/resources;src/resources" --add-data "vendor;vendor" start.py
```

## 📁 **Структура проекта**

```
qManager/
├── start.py                # Точка входа в приложение
├── src/                    # Исходный код
│   ├── ui_windows_main_window.py    # Главное окно приложения
│   ├── ui_areas_*.py               # UI области (splitter, renamer, organizer, settings)
│   ├── ui_widgets_*.py             # Кастомные виджеты (console, splitter, checkbox)
│   ├── ui_styles.py                # Стили и темы
│   ├── pdf_*.py                    # Основная логика (splitter, renamer, organizer)
│   ├── core_*.py                   # Ядро приложения (worker, settings)
│   ├── utils_*.py                  # Утилиты (data_manager)
│   ├── subprocess_hider.py         # Скрытие консольных окон
│   └── resources/                  # Ресурсы (иконки)
├── vendor/                 # Внешние зависимости
│   ├── poppler/           # Poppler для работы с PDF
│   └── Tesseract-OCR/     # Tesseract для OCR
├── requirements.txt        # Python зависимости
├── installer.iss          # Inno Setup скрипт
└── debug.log              # Файл детального логирования
```

## ✨ **Ключевые особенности**

- **Современный UI** с поддержкой светлой и тёмной тем
- **Многопоточность** для длительных операций
- **Автоматическое определение** путей к зависимостям
- **Гибкая настройка** параметров для каждого модуля
- **Поддержка русского языка** в интерфейсе

## 🔧 **Настройка**

### **Темы:**
- Автоматическое переключение между светлой и тёмной темами
- Динамическая адаптация цветов и иконок

### **Зависимости:**
- Автоматический поиск Poppler и Tesseract
- Поддержка как системных, так и локальных установок

## 📄 **Лицензия**

MIT License - см. файл [LICENSE](LICENSE)

## 🤝 **Поддержка**

- **Issues:** Создавайте issue для багов и предложений
- **Discussions:** Обсуждайте идеи и задавайте вопросы
- **Wiki:** Документация и примеры использования

## 🚧 **Важные замечания**

- Приложение **НЕ является консольным** - запускается через GUI
- Точка входа: **`start.py`** (НЕ `main.py`)
- Требуется **строго Python 3.10.11** для совместимости

## 🆘 **Решение проблем**

### **Ошибка "Python not found":**
- Убедитесь, что Python 3.10.11 установлен и добавлен в PATH
- Проверьте версию: `python --version`

### **Зависимости не найдены:**
- Проверьте наличие папки `vendor/` с Poppler и Tesseract
- Убедитесь, что пути указаны правильно

### **Ошибки сборки:**
- Используйте **`start.py`** как точку входа
- Проверьте наличие всех необходимых файлов