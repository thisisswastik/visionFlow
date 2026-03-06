# automation of browser (playwright setup)
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class BrowserExecutor:
    def __init__(self, headless: bool = True):
        self.playwright = sync_playwright().start()
        # Add basic anti-detection args and a common viewport
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        # Route to block some analytics and useless stuff to speed up loading (optional, keeping it simple for now)

    def open(self, url: str):
        """ open url in browser """
        self.page.goto(url, wait_until="domcontentloaded")
        time.sleep(2)
        self._dismiss_overlays()

    def _dismiss_overlays(self):
        """ Add automatic overlay handling for common modals """
        overlay_texts = [
            "Accept", "Accept all", "Accept All", "Agree", "I Agree", "Continue", 
            "OK", "Got it", "Allow all cookies", "Accept all cookies", "I accept"
        ]
        
        for text in overlay_texts:
            candidate = self.page.locator(f"text='{text}'").first
            try:
                if candidate.is_visible(timeout=500):
                    candidate.click(timeout=1000)
                    time.sleep(0.5)
            except Exception:
                pass
            
            # Also try by role button with regex
            try:
                candidate = self.page.get_by_role("button", name=re.compile(f"^{text}$", re.IGNORECASE)).first
                if candidate.is_visible(timeout=500):
                    candidate.click(timeout=1000)
                    time.sleep(0.5)
            except Exception:
                pass

    def _find_element(self, text: str):
        """ 
        Implement a DOM grounding step.
        Search candidate elements using multiple signals and select the best one.
        """
        # Build candidate locators
        selectors = [
            self.page.get_by_placeholder(text, exact=True),
            self.page.get_by_placeholder(re.compile(text, re.IGNORECASE)),
            self.page.get_by_text(text, exact=True),
            self.page.get_by_text(re.compile(text, re.IGNORECASE)),
            self.page.get_by_label(text, exact=True),
            self.page.get_by_label(re.compile(text, re.IGNORECASE)),
            self.page.get_by_title(text, exact=True),
            self.page.get_by_title(re.compile(text, re.IGNORECASE)),
            self.page.get_by_role("button", name=text, exact=True),
            self.page.get_by_role("button", name=re.compile(text, re.IGNORECASE)),
            self.page.locator(f"input[name='{text}']"),
            self.page.locator(f"textarea[name='{text}']"),
            self.page.locator(f"[aria-label='{text}']"),
            self.page.locator(f"[aria-label*='{text}' i]") # case insensitive contains
        ]

        # 1. Return the first one that is attached AND visible
        for loc in selectors:
            try:
                # Playwright locators might resolve to multiple elements
                count = loc.count()
                if count > 0:
                    for i in range(count):
                        el = loc.nth(i)
                        if el.is_visible():
                            return el
            except Exception:
                continue
        
        # 2. Fallback: just return the first one that exists even if not strictly visible (might be scrollable into view)
        for loc in selectors:
            try:
                if loc.count() > 0:
                    return loc.first
            except Exception:
                continue
                
        # 3. Final fallback: original naive text search
        return self.page.locator(f"text='{text}'").first

    def _interact_with_retry(self, action_func, target_text: str, retries: int = 3):
        """ Add retry logic and scroll safety """
        self._dismiss_overlays()
        
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                element = self._find_element(target_text)
                
                if element:
                    # Scroll safety and robust wait
                    try:
                        element.wait_for(state="attached", timeout=3000)
                        element.scroll_into_view_if_needed()
                        # Allow some time for animations after scroll
                        time.sleep(0.5)
                        element.wait_for(state="visible", timeout=3000)
                    except PlaywrightTimeoutError:
                        # Sometimes playwright wait_for visible fails but element is intractable
                        pass 
                        
                    action_func(element)
                    return True
                else:
                    raise Exception(f"Element matching '{target_text}' not found in DOM.")
            except Exception as e:
                last_exception = e
                print(f"Interaction attempt {attempt} failed for '{target_text}': {str(e)}")
                # Scroll safety - page down slightly
                self.page.mouse.wheel(0, 300)
                time.sleep(1) # short wait before retry
                self._dismiss_overlays() # re-check overlays
                
        print(f"Action on '{target_text}' failed after {retries} retries. Last error: {last_exception}")
        return False

    def click_by_text(self, text: str):
        """ Keep compatibility with the current action schema """
        def _click(element):
            try:
                element.click(timeout=3000, force=True)
            except Exception:
                # Absolute fallback: JS click
                try:
                    element.evaluate("el => el.click()")
                except Exception as e:
                    raise e
        
        # Original fallback just in case
        success = self._interact_with_retry(_click, text)
        if not success:
            # Fallback to absolute original just to ensure no regressions
            try:
                simplified = text.replace(" button", "").replace(" Button", "")
                self.page.get_by_role("button", name=simplified).first.click(timeout=3000, force=True)
            except Exception:
                pass


    def type_by_placeholder(self, placeholder: str, value: str):
        """ Improve typing logic: wait, click, clear, type """
        def _type(element):
            try:
                element.click(timeout=3000, force=True)
            except Exception:
                try:
                    element.evaluate("el => el.click()")
                except Exception:
                    pass
            
            try:
                element.fill("", timeout=3000, force=True) # clear existing text
                element.fill(value, timeout=3000, force=True)
            except Exception:
                # JS fallback for text entry
                element.evaluate(f"el => {{ el.value = '{value}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}")
        
        self._interact_with_retry(_type, placeholder)

    def scroll(self, amount: int = 500):
        self.page.mouse.wheel(0, amount)

    def screenshot(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Settle before screenshot
        time.sleep(0.5)
        self.page.screenshot(path=path)

    def wait(self, seconds: float = 1.0):
        time.sleep(seconds)

    def close(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()
