import platform
import os

_DISABLE_HIDER = os.environ.get('QMANAGER_DISABLE_SUBPROCESS_HIDER', '').lower() in ('1', 'true', 'yes')

if platform.system() == "Windows" and not _DISABLE_HIDER:
    try:
        import subprocess
        
        CREATE_NO_WINDOW = 0x08000000
        
        _hidden_startupinfo = subprocess.STARTUPINFO()
        _hidden_startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        _hidden_startupinfo.wShowWindow = subprocess.SW_HIDE
        
        _original_popen_class = subprocess.Popen
        _original_call = subprocess.call
        _original_run = subprocess.run
        
        class HiddenPopen(_original_popen_class):
            def __init__(self, *args, **kwargs):
                if 'startupinfo' not in kwargs:
                    kwargs['startupinfo'] = _hidden_startupinfo
                if 'creationflags' not in kwargs:
                    kwargs['creationflags'] = CREATE_NO_WINDOW
                super().__init__(*args, **kwargs)
        
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
        
        subprocess.Popen = HiddenPopen
        subprocess.call = _hidden_call
        subprocess.run = _hidden_run
        
    except Exception:
        pass