import logging
import os
import glob
import traceback
import asyncio
from pathlib import Path
import subprocess
import sys

logger = logging.getLogger('playwright_automation')

class PlaywrightAutomation:
    def __init__(self, login, password, input_folder, log_callback=None, progress_callback=None):
        self.login = login
        self.password = password
        self.input_folder = Path(input_folder)
        self.log_callback = log_callback
        self.progress_callback = progress_callback

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        logger.info(message)

    def progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def _find_chromium_executable(self) -> str | None:
        """Ищет chromium.exe в пользовательской и системной папках ms-playwright."""
        # Пользовательская папка
        user_dir = os.path.expanduser(r"~\AppData\Local\ms-playwright")
        patterns = [
            os.path.join(user_dir, "chromium-*", "chrome-win", "chrome.exe"),
        ]
        # Системная папка
        system_dir = r"C:\ProgramData\ms-playwright"
        patterns.append(os.path.join(system_dir, "chromium-*", "chrome-win", "chrome.exe"))

        for pattern in patterns:
            matches = glob.glob(pattern)
            if matches:
                # Берём самый новый билд
                matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                return matches[0]
        return None

    async def run_async(self) -> bool:
        try:
            self.log("Запуск Playwright автоматизации...")
            async with async_playwright() as p:
                launch_args = {
                    "headless": False,
                    "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
                }

                exe = self._find_chromium_executable()
                try:
                    if exe and os.path.exists(exe):
                        browser = await p.chromium.launch(executable_path=exe, **launch_args)
                        self.log(f"Используется Chromium: {exe}")
                    else:
                        browser = await p.chromium.launch(**launch_args)
                        self.log("Используется стандартный Chromium Playwright")
                except Exception as e:
                    self.log(f"Не удалось запустить Chromium: {e}")
                    browser = await p.chromium.launch(**launch_args)
                    self.log("Повторный запуск стандартного Chromium Playwright")

                context = await browser.new_context()
                page = await context.new_page()

                self.log("Переход на страницу входа...")
                await page.goto("https://logos.grandtrade.world/login")
                await page.wait_for_load_state("networkidle")

                self.log("Заполнение формы входа...")
                await page.fill('input[name="login"]', self.login)
                try:
                    await page.fill('div.line-password input.clone', self.password)
                except Exception:
                    await page.fill('input[name="password"]', self.password)

                self.log("Вход в систему...")
                await page.click('button.button-login')
                await page.wait_for_load_state("networkidle")

                if "login" in page.url:
                    self.log("Ошибка: Не удалось войти в систему")
                    await browser.close()
                    return False

                self.log("Успешный вход в систему")

                self.log("Переход в раздел 'Грузы'...")
                await page.click('li.menu-li a[href="javascript:void(0)"]')
                await page.wait_for_timeout(1000)

                await page.click('ul.dropdown-menu li.tab-elem a[cid="c11617"]')
                await page.wait_for_load_state("networkidle")

                self.log("Поиск вкладки 'Playwright'...")
                await page.locator("div.GridTabs--tabButton >> text=Playwright").first.click()
                await page.wait_for_load_state("networkidle")

                self.log("Успешно перешли на вкладку 'Playwright'")

                await page.wait_for_timeout(3000)

                await browser.close()
                self.log("Автоматизация завершена")
                return True
        except Exception as e:
            tb = traceback.format_exc()
            self.log(f"Ошибка автоматизации: {e}")
            self.log(tb)
            logger.error(f"Playwright automation error: {e}\n{tb}")
            return False

def run_playwright_automation(login, password, input_folder, log_callback=None, progress_callback=None, worker=None):
    """Запускает отдельный процесс-раннер, чтобы изолировать event loop/greenlet."""
    # Путь к интерпретатору текущего окружения
    python_exe = sys.executable
    runner = Path(__file__).with_name('playwright_runner.py')
    env = os.environ.copy()
    env['QMANAGER_PW_LOGIN'] = str(login)
    env['QMANAGER_PW_PASSWORD'] = str(password)
    env['QMANAGER_INPUT_DIR'] = str(input_folder)

    # Стримим вывод построчно в лог
    try:
        proc = subprocess.Popen(
            [python_exe, str(runner)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(Path(__file__).parent),
            env=env,
            text=True,
            bufsize=1
        )
    except Exception as e:
        if log_callback:
            log_callback(f"Ошибка запуска процесса Playwright: {e}")
        return False

    if log_callback and proc.stdout:
        for line in proc.stdout:
            if line:
                log_callback(line.rstrip())
    ret = proc.wait()
    return ret == 0
