from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException

def setup_edge_driver(headless=True):
    options = EdgeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")

    driver_path = r'D:\edge_driver\msedgedriver.exe'
    driver = webdriver.Edge(service=EdgeService(driver_path), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })
    return driver

def fetch_product_details(link: str) -> dict:
    try:
        driver = setup_edge_driver(headless=True)
        driver.get(link)
        time.sleep(random.uniform(2, 5))
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        title = driver.find_element(By.TAG_NAME, "h1").text.strip() if driver.find_elements(By.TAG_NAME, "h1") else "не найдено"

        prices = fetch_prices(driver)
        price_card = prices.get('price_with_card', "N/A")
        price_discounted = prices.get('price_discounted', "N/A")
        price_original = prices.get('price_original', "N/A")

        return {
            "title": title,
            "price_with_card": price_card,
            "price_no_card": price_discounted,
            "price_original": price_original
        }
    except Exception as e:
        return {"error": f"Ошибка при обработке страницы: {str(e)}"}
    finally:
        driver.quit()

def fetch_price(driver: WebDriver, xpath: str) -> str:
    """
    Получает цену с использованием универсального XPath.
    """
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text.strip()
    except NoSuchElementException:
        return "N/A"

def fetch_prices(driver: WebDriver) -> dict:
    """
    Универсальный метод для получения цен с использованием структуры страницы.
    """
    prices = {}

    # XPath для цены с картой
    prices['price_with_card'] = fetch_price(driver, "//span[@class='tl3_27 t1l_27']")

    # XPath для скидочной цены
    prices['price_discounted'] = fetch_price(driver, "//span[@class='l8t_27 tl8_27 u1l_27']")

    # XPath для оригинальной цены
    prices['price_original'] = fetch_price(driver, "//span[@class='t7l_27 t8l_27 t6l_27 lt8_27']")

    return prices