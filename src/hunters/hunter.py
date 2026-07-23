import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service

# Set browser and driver paths for Chromium
CHROME_BIN       = "/usr/bin/chromium"
CHROMEDRIVER_BIN = "/usr/bin/chromedriver" # chromium-driver's binary is chromedriver

# Fallback user agent, only used if reading the live one fails
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Configure browser
options = webdriver.ChromeOptions()
options.binary_location = CHROME_BIN
options.add_argument("--headless=new") # modern headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--lang=en-US,en")
# Reduce the most obvious automation fingerprints that passive bot-detection
# (Cloudflare / DataDome on Kamernet and Pararius) checks for.
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

service = Service(CHROMEDRIVER_BIN)
browser = webdriver.Chrome(service=service, options=options)

# Headless Chrome advertises "HeadlessChrome" in its UA and sets
# navigator.webdriver=true; both are trivial bot tells. Strip the first (using
# the browser's real version so we don't mismatch) and mask the second.
try:
    live_ua = browser.execute_script("return navigator.userAgent")
    ua = live_ua.replace("HeadlessChrome", "Chrome") if live_ua else USER_AGENT
except WebDriverException:
    ua = USER_AGENT
browser.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": ua})
browser.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
)

def shutdown_browser():
    browser.quit()

class Prey:
    def __init__(self, name: str, price: str, link: str, agency: str, website: str, city: str = None):
        self.name = name
        self.price = price
        self.link = link
        self.agency = agency
        self.website = website
        self.city = city

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        if not isinstance(other, Prey):
            return False
        return self.link == other.link

    def __str__(self):
        return f"{self.name} | {self.link} | {self.agency} | {self.price}"

class Hunter:
    def __init__(self, name: str):
        self.name = name
        self.city_urls: dict[str, str] = {}

    def start(self):
        pass

    def stop(self):
        pass

    def hunt(self):
        preys: set[Prey] = set()
        city_urls = list(self.city_urls.items())
        for (i, (city, url)) in enumerate(city_urls):
            browser.get(url)
            try:
                found = self.process()
            except TimeoutException:
                print(f'[{self.name}] No listings for {city}: timed out waiting for '
                      f'the results container at {url} (page title: "{browser.title}").')
                found = []
            for prey in found:
                prey.city = city
                preys.add(prey) # add to set (avoids duplicates)
            if i < len(city_urls) - 1: time.sleep(2) # delay between requests to avoid 429
        return preys

    def process(self) -> list[Prey]:
        # This method should be overloaded by derived classes
        raise NotImplementedError(f"process not implemented for {self.name}")

    def supported_cities(self) -> dict[str, str]:
        # This method should be overloaded by derived classes
        raise NotImplementedError(f"supported_cities not implemented for {self.name}")

    # Set the cities and return unsupported ones
    def set_cities(self, cities: set[str]) -> set[str]:
        all_cities = self.supported_cities()

        # Set URLs for supported cities
        intersection = cities & set(all_cities.keys())
        self.city_urls = {city: all_cities[city] for city in intersection}

        # Return the unsupported cities
        return cities - intersection
