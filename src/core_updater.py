"""Проверка и загрузка обновлений с GitHub Releases."""
import json
import re
import tempfile
import urllib.request

from PySide6.QtCore import QThread, Signal

VERSION = "1.9.3a"
_GITHUB_REPO = "Factiosi/qManager"
_API_URL = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
_CHECK_TIMEOUT = 15
_DOWNLOAD_TIMEOUT = 120

_PRERELEASE_LABELS = {'a': 'alpha', 'b': 'beta'}
_pre = re.search(r'([a-zA-Z]+)$', VERSION.split('.')[-1])
PRERELEASE = _PRERELEASE_LABELS.get(_pre.group().lower(), _pre.group().upper()) if _pre else None


def _ver(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r'\d+', v))


class UpdateChecker(QThread):
    update_available = Signal(str, str)  # (latest_version, download_url)
    no_update = Signal()
    error = Signal(str)

    def run(self):
        try:
            req = urllib.request.Request(
                _API_URL, headers={"User-Agent": "qManager-updater"}
            )
            with urllib.request.urlopen(req, timeout=_CHECK_TIMEOUT) as r:
                data = json.loads(r.read())
            latest = data["tag_name"].lstrip("v")
            if _ver(latest) > _ver(VERSION):
                url = next(
                    a["browser_download_url"]
                    for a in data.get("assets", [])
                    if a["name"].lower().endswith(".exe")
                )
                self.update_available.emit(latest, url)
            else:
                self.no_update.emit()
        except StopIteration:
            self.error.emit("Установщик не найден в релизе")
        except Exception as e:
            self.error.emit(str(e))


class UpdateDownloader(QThread):
    progress = Signal(int)   # 0–100
    finished = Signal(str)   # путь к скачанному установщику
    error = Signal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            path = tempfile.mktemp(suffix=".exe", prefix="qManagerSetup_")
            req = urllib.request.Request(
                self.url, headers={"User-Agent": "qManager-updater"}
            )
            with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as r:
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(path, "wb") as f:
                    while chunk := r.read(16384):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            self.progress.emit(int(downloaded / total * 100))
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))
