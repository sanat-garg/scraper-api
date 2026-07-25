from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()

    if not data or 'url' not in data or 'selector' not in data:
        return jsonify({"success": False, "error": "Both 'url' and 'selector' are required"}), 400

    url = data['url']
    css_selector = data['selector']

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--single-process")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )

        html_content = element.get_attribute("innerHTML")
        text_content = element.text

        return jsonify({
            "success": True,
            "html": html_content,
            "text": text_content
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        driver.quit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
