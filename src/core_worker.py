from PySide6.QtCore import QThread, Signal

class WorkerThread(QThread):
    progress_signal = Signal(int, int)  # current, total
    message_signal = Signal(str)
    error_signal = Signal(str)
    finished = Signal()

    def __init__(self, function=None, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._stop_requested = False

    def set_target(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def is_stop_requested(self):
        return self._stop_requested

    def check_stop(self):
        if self._stop_requested:
            raise InterruptedError("Операция остановлена пользователем")

    def _emit_log(self, message: str):
        self.message_signal.emit(str(message))

    def _emit_progress(self, current: int, total: int):
        self.progress_signal.emit(current, total)

    def _emit_error(self, message: str):
        self.error_signal.emit(str(message))

    def run(self):
        if self.function is None:
            self._emit_error("WorkerThread: target function is not set")
            return
        try:
            def log_handler(message):
                if self._stop_requested:
                    return
                self._emit_log(message)

            def progress_handler(current, total):
                if self._stop_requested:
                    return
                self._emit_progress(current, total)

            self.kwargs.setdefault('log_callback', log_handler)
            self.kwargs.setdefault('progress_callback', progress_handler)
            self.kwargs.setdefault('worker', self)

            if self._stop_requested:
                return

            self.function(*self.args, **self.kwargs)
            
            if not self._stop_requested:
                self.finished.emit()
                
        except InterruptedError:
            pass
        except Exception as e:
            if not self._stop_requested:
                self._emit_error(str(e))
        finally:
            self._stop_requested = False
