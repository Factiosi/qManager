import os
import sys
import asyncio
import traceback
from playwright.async_api import async_playwright

async def main():
    login = os.environ.get('QMANAGER_PW_LOGIN', '')
    password = os.environ.get('QMANAGER_PW_PASSWORD', '')
    input_dir = os.environ.get('QMANAGER_INPUT_DIR', '')

    print('[Runner] Старт Playwright')
    async with async_playwright() as p:
        launch_args = {
            'headless': False,
            'args': ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        }
        browser = await p.chromium.launch(**launch_args)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        print('[Runner] Открываю страницу логина')
        await page.goto('https://logos.grandtrade.world/login')
        await page.wait_for_load_state('networkidle')
        print('[Runner] Ввожу логин')
        await page.fill('input[name="login"]', login)
        print('[Runner] Ввожу пароль')
        try:
            await page.fill('div.line-password input.clone', password)
        except Exception:
            await page.fill('input[name="password"]', password)
        print('[Runner] Нажимаю Войти')
        await page.click('button.button-login')
        await page.wait_for_load_state('networkidle')
        if 'login' in page.url:
            print('[Runner][ERROR] Логин не удался')
            await browser.close()
            return 2
        print('[Runner] Кликаю меню Грузы')
        await page.click('li.menu-li a[href="javascript:void(0)"]')
        await page.wait_for_timeout(1000)
        print('[Runner] Выбираю Грузы в меню')
        await page.click('ul.dropdown-menu li.tab-elem a[cid="c11617"]')
        await page.wait_for_load_state('networkidle')
        print('[Runner] Ищу вкладку Playwright')
        await page.locator('div.GridTabs--tabButton >> text=Playwright').first.click()
        await page.wait_for_load_state('networkidle')
        print('[Runner] Готово')
        await page.wait_for_timeout(1500)
        await browser.close()
        return 0

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
    except Exception:
        print('[Runner][EXCEPTION]')
        print(traceback.format_exc())
        sys.exit(1)
    sys.exit(exit_code)
