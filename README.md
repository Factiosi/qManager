# qManager v1.9.3

Инструмент автоматизации обработки сканов АКФК (Актов Карантинного Фитосанитарного Контроля). Приложение решает три последовательные задачи: разделение многостраничных сканов, переименование файлов по номерам контейнеров и распределение по папкам согласно реестру.

## Модули

### PDF Splitter
Разделяет объединённый скан пакета АКФК на отдельные файлы. Зелёная страница в скане является маркером границы документа. Порог определения зелёного цвета настраивается.

### PDF Renamer
Извлекает номер контейнера из скана методом OCR и переименовывает файл соответственно. Поддерживает форматы Logos и Отчёт.

### PDF Organizer
Раскладывает файлы по папкам по данным из Excel-реестра. Поддерживает автоматическое объединение документов по юнитам.

### Playwright
Веб-автоматизация для работы с порталом.

## Требования

- Windows 10/11 x64
- Python 3.10.11
- Poppler (конвертация PDF)
- Tesseract OCR (распознавание текста)

## Установка (для разработчиков)

```bash
git clone https://github.com/Factiosi/qManager.git
cd qManager
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python start.py
```

## Установка (для пользователей)

Скачать актуальный установщик из раздела [Releases](https://github.com/Factiosi/qManager/releases) и запустить `qManager-Setup.exe`.

## Сборка

```bash
python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=pyside6 --windows-icon-from-ico=src/resources/Icon.ico --include-data-dir=src/resources=src/resources --include-data-dir=vendor=vendor --include-package=googleapiclient --include-package=google.oauth2 --output-dir=dist --output-filename=qManager.exe start.py
```

## Структура проекта

```
qManager/
├── start.py
├── src/
│   ├── core_*.py          # Ядро: воркер, настройки, обновление
│   ├── pdf_*.py           # Логика: splitter, renamer, organizer
│   ├── ui_windows_*.py    # Главное окно
│   ├── ui_areas_*.py      # Вкладки интерфейса
│   ├── ui_widgets_*.py    # Кастомные виджеты
│   ├── ui_styles.py       # Темы оформления
│   ├── utils_*.py         # Утилиты: данные, Google Sheets
│   └── resources/         # Иконки и прочие ресурсы
├── vendor/
│   ├── poppler/
│   └── Tesseract-OCR/
├── requirements.txt
└── installer.iss
```
