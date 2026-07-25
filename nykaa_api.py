from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)


def get_driver():
    options = Options()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def scrape_single(driver, css_selector):
    """Scrape a single selector from an already-loaded page."""
    try:
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return {
            "selector": css_selector,
            "outerHTML": element.get_attribute("outerHTML"),
            "innerHTML": element.get_attribute("innerHTML"),
            "text": element.text
        }
    except Exception as e:
        return {
            "selector": css_selector,
            "error": str(e)
        }


# ── Health check ─────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Working fine"}), 200


# ── /scrape/html  →  returns outerHTML (single selector) ──────────────────────

@app.route('/scrape/html', methods=['POST'])
def scrape_html():
    data = request.get_json()
    if not data or 'url' not in data or 'selector' not in data:
        return jsonify({"success": False, "error": "Both 'url' and 'selector' are required"}), 400

    driver = get_driver()
    try:
        driver.get(data['url'])
        result = scrape_single(driver, data['selector'])
        if 'error' in result:
            return jsonify({"success": False, "error": result['error']}), 500
        return jsonify({
            "success": True,
            "outerHTML": result['outerHTML'],
            "innerHTML": result['innerHTML']
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        driver.quit()


# ── /scrape/text  →  returns innerText (single selector) ─────────────────────

@app.route('/scrape/text', methods=['POST'])
def scrape_text():
    data = request.get_json()
    if not data or 'url' not in data or 'selector' not in data:
        return jsonify({"success": False, "error": "Both 'url' and 'selector' are required"}), 400

    driver = get_driver()
    try:
        driver.get(data['url'])
        result = scrape_single(driver, data['selector'])
        if 'error' in result:
            return jsonify({"success": False, "error": result['error']}), 500
        return jsonify({
            "success": True,
            "text": result['text']
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        driver.quit()


# ── /scrape/multi  →  multiple selectors from the same page ───────────────────

@app.route('/scrape/multi', methods=['POST'])
def scrape_multi():
    """
    Request body:
    {
        "url": "https://example.com",
        "selectors": ["#title", ".price", "div.reviews"]
    }

    Response:
    {
        "success": true,
        "results": [
            {"selector": "#title", "outerHTML": "...", "innerHTML": "...", "text": "..."},
            {"selector": ".price", "outerHTML": "...", "innerHTML": "...", "text": "..."},
            {"selector": "div.reviews", "error": "element not found..."}
        ]
    }
    """
    data = request.get_json()
    if not data or 'url' not in data or 'selectors' not in data:
        return jsonify({"success": False, "error": "'url' and 'selectors' (array) are required"}), 400

    selectors = data['selectors']
    if not isinstance(selectors, list) or len(selectors) == 0:
        return jsonify({"success": False, "error": "'selectors' must be a non-empty array"}), 400

    driver = get_driver()
    try:
        driver.get(data['url'])
        # Wait for first selector to ensure page is loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selectors[0]))
        )

        results = []
        for selector in selectors:
            results.append(scrape_single(driver, selector))

        return jsonify({"success": True, "results": results})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        driver.quit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1777)
