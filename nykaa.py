from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = "https://www.nykaa.com/signaxo-glow-rechargeable-battery-operated-7-color-led-light-therapy-face-mask/reviews/10090541?skuId=10090541&ptype=reviews"

css_selector = "#app > div.css-e82s8r > div > div.css-17hovqr.e13gq3a61 > div.css-bql5ld.e13gq3a62 > section > div.css-nyh3cj"

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

try:
    driver.get(url)

    # Wait for the target element to load (up to 15 seconds)
    element = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )

    print(element.get_attribute("innerHTML"))

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()
