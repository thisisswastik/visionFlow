# automation of browser (playwright setup)
from playwright.sync_api import sync_playwright
from pathlib import Path
import time 

class BrowserExecutor:
    def __init__(self, headless: bool=True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def open(self, url:str):
        """ open url in browser """
        self.page.goto(url)
        time.sleep(2)

    def click_by_text(self, text:str):
        try:
            self.page.get_by_role("button", name=text).first.click(timeout=3000)
        except:
            simplified = text.replace(" button", "").replace(" Button", "")
            self.page.get_by_role("button", name=text).first.click(timeout=3000)

    def type_by_placeholder(self, placeholder:str, value:str):
        self.page.get_by_placeholder(placeholder).fill(value)

    def scroll(self, amount:int=500):
        self.page.mouse.wheel(0,amount)

    def screenshot(self, path:str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=path)

    def wait(self, seconds:float=1.0):
        time.sleep(seconds)

    def close(self):
        self.browser.close()
        self.playwright.stop()


    
