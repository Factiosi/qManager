# qManager

Приложение для организации АФК.

## Функциональность

- Разделение PDF файлов по цветовым маркерам
- Автоматическое переименование документов с использованием OCR
- Организация файлов с поддержкой Excel

## Требования

- Python 3.10
- Tesseract OCR (включен в поставку)
- Poppler (включен в поставку)
- PySide6
- OpenCV (для обработки изображений)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/factiosi/qManager.git
cd qManager
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

```bash
python src/main.py
```

## Сборка

Сборка проекта осуществляется с помощью nuitka:

```bash
python -m nuitka --standalone --enable-plugin=pyside6 --windows-icon-from-ico=src/resources/Icon.ico --output-dir=dist `
--include-data-dir=src/resources=resources `
--include-data-dir=vendor/poppler/bin=vendor/poppler/bin `
--include-data-dir=vendor/Tesseract-OCR=vendor/Tesseract-OCR `
--include-data-file=src/settings.json=settings.json `
--include-module=src.ui_windows_main_window `
--include-module=src.ui_areas_splitter `
--include-module=src.ui_areas_renamer `
--include-module=src.ui_areas_organizer `
--include-module=src.ui_styles `
--include-module=src.core_settings `
--include-module=src.core_worker `
--include-module=src.pdf_splitter `
--include-module=src.pdf_renamer `
--include-module=src.pdf_organizer `
--include-module=src.utils_data_manager `
start.py
```

## Структура проекта

- `src/` - исходный код
  - `core_settings.py` - управление настройками приложения (хранение в %APPDATA%)
  - `core_worker.py` - основные рабочие процессы и многопоточная обработка
  - `main.py` - точка входа в графический интерфейс
  - `pdf_organizer.py` - интеллектуальная организация PDF файлов
  - `pdf_renamer.py` - переименование с использованием OCR
  - `pdf_splitter.py` - разделение по цветовым маркерам
  - `ui_areas_*.py` - компоненты интерфейса для каждой функции
  - `ui_styles.py` - настройки стилей и тем оформления
  - `ui_windows_main_window.py` - главное окно приложения
  - `utils_data_manager.py` - работа с данными и интеграция с Excel
- `vendor/` - внешние зависимости (включены в сборку)
  - `Tesseract-OCR/` - OCR движок для распознавания текста
  - `poppler/` - библиотека для работы с PDF
- `resources/` - ресурсы приложения (иконки, конфигурации)
- `start.py` - точка входа для запуска и сборки
- `qManager.spec` - конфигурация сборки
- `requirements.txt` - зависимости Python

## Примечание

Проект требует Python 3.10 и использует систему сборки Nuitka для создания исполняемого файла. Все внешние зависимости включаются в сборку, что делает возможным запуск на компьютерах без установленного Python.
