from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--single-process")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def scrape_element(url, css_selector):
    """Shared scraping logic. Returns the Selenium element."""
    if not url or not css_selector:
        raise ValueError("Both 'url' and 'selector' are required")

    driver = get_driver()
    try:
        driver.get(url)
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        # Read data before quitting driver
        outer_html = element.get_attribute("outerHTML")
        inner_html = element.get_attribute("innerHTML")
        inner_text = element.text
        return outer_html, inner_html, inner_text
    finally:
        driver.quit()


# ── Health check ─────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Working fine"}), 200


# ── /scrape/html  →  returns outerHTML of the matched element ─────────────────

@app.route('/scrape/html', methods=['POST'])
def scrape_html():
    data = request.get_json()
    if not data or 'url' not in data or 'selector' not in data:
        return jsonify({"success": False, "error": "Both 'url' and 'selector' are required"}), 400

    try:
        outer_html, inner_html, _ = scrape_element(data['url'], data['selector'])
        return jsonify({
            "success": True,
            "outerHTML": outer_html,
            "innerHTML": inner_html
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── /scrape/text  →  returns innerText of the matched element ─────────────────

@app.route('/scrape/text', methods=['POST'])
def scrape_text():
    data = request.get_json()
    if not data or 'url' not in data or 'selector' not in data:
        return jsonify({"success": False, "error": "Both 'url' and 'selector' are required"}), 400

    try:
        _, _, inner_text = scrape_element(data['url'], data['selector'])
        return jsonify({
            "success": True,
            "text": inner_text
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
