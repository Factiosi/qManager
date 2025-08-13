"""
Глобальный перехватчик subprocess для скрытия консоли на Windows
"""
import platform

if platform.system() == "Windows":
    try:
        import subprocess
        import os
        
        # Константа для скрытия консоли
        CREATE_NO_WINDOW = 0x08000000
        
        # Создаем startupinfo для скрытия консоли
        _hidden_startupinfo = subprocess.STARTUPINFO()
        _hidden_startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        _hidden_startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Сохраняем оригинальные функции
        _original_popen = subprocess.Popen
        _original_call = subprocess.call
        _original_run = subprocess.run
        
        # Функции-обертки для скрытия консоли
        def _hidden_popen(*args, **kwargs):
            if 'startupinfo' not in kwargs:
                kwargs['startupinfo'] = _hidden_startupinfo
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = CREATE_NO_WINDOW
            return _original_popen(*args, **kwargs)
        
        def _hidden_call(*args, **kwargs):
            if 'startupinfo' not in kwargs:
                kwargs['startupinfo'] = _hidden_startupinfo
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = CREATE_NO_WINDOW
            return _original_call(*args, **kwargs)
        
        def _hidden_run(*args, **kwargs):
            if 'startupinfo' not in kwargs:
                kwargs['startupinfo'] = _hidden_startupinfo
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = CREATE_NO_WINDOW
            return _original_run(*args, **kwargs)
        
        # Заменяем глобально
        subprocess.Popen = _hidden_popen
        subprocess.call = _hidden_call
        subprocess.run = _hidden_run
        
    except Exception:
        pass
