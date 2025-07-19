from PySide6.QtCore import QThread, Signal
from src.core_settings import SettingsManager

class WorkerThread(QThread):
    progress = Signal(int, int)  # текущий, всего
    finished = Signal()
    error = Signal(str)
    log = Signal(str)

    def __init__(self, function, *args, **kwargs):
        """
        Инициализация потока-работника.
        Аргументы:
            function (callable): Функция, которую нужно выполнить в потоке.
            *args: Позиционные аргументы для функции.
            **kwargs: Именованные аргументы для функции.
        """
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Запускает выполнение функции в отдельном потоке с поддержкой логирования и прогресса.
        В случае ошибки сигнализирует через error.
        """
        try:
            # Обработчик логов
            def log_handler(message):
                self.log.emit(str(message))

            # Обработчик прогресса
            def progress_handler(current, total):
                self.progress.emit(current, total)

            # Добавляем обработчики в kwargs
            self.kwargs['log_callback'] = log_handler
            self.kwargs['progress_callback'] = progress_handler

            self.function(*self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
