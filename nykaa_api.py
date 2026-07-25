from flask import Flask, jsonify, request
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import subprocess
import os

app = Flask(__name__)
CORS(app)

# Limit to 1 Chrome instance at a time to prevent memory crashes
scrape_lock = threading.Lock()


def kill_zombie_chromes():
    """Kill any leftover Chrome/chromedriver processes."""
    try:
        subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
        time.sleep(1)
    except Exception:
        pass


def get_driver():
    options = Options()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/150.0.7871.186 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def create_driver_with_retry(max_retries=2):
    """Try to create a Chrome driver, retry if it crashes."""
    for attempt in range(max_retries):
        try:
            return get_driver()
        except Exception as e:
            if attempt < max_retries - 1:
                kill_zombie_chromes()
                time.sleep(2)
            else:
                raise e


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

    with scrape_lock:
        driver = None
        try:
            driver = create_driver_with_retry()
            driver.get(data['url'])
            wait_seconds = data.get('wait', 0)
            if wait_seconds:
                time.sleep(wait_seconds)
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
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass


# ── /scrape/text  →  returns innerText (single selector) ─────────────────────

@app.route('/scrape/text', methods=['POST'])
def scrape_text():
    data = request.get_json()
    if not data or 'url' not in data or 'selector' not in data:
        return jsonify({"success": False, "error": "Both 'url' and 'selector' are required"}), 400

    with scrape_lock:
        driver = None
        try:
            driver = create_driver_with_retry()
            driver.get(data['url'])
            wait_seconds = data.get('wait', 0)
            if wait_seconds:
                time.sleep(wait_seconds)
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
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass


# ── /scrape/multi  →  multiple selectors from the same page ───────────────────

@app.route('/scrape/multi', methods=['POST'])
def scrape_multi():
    data = request.get_json()
    if not data or 'url' not in data or 'selectors' not in data:
        return jsonify({"success": False, "error": "'url' and 'selectors' (array) are required"}), 400

    selectors = data['selectors']
    if not isinstance(selectors, list) or len(selectors) == 0:
        return jsonify({"success": False, "error": "'selectors' must be a non-empty array"}), 400

    with scrape_lock:
        driver = None
        try:
            driver = create_driver_with_retry()
            driver.get(data['url'])
            wait_seconds = data.get('wait', 0)
            if wait_seconds:
                time.sleep(wait_seconds)
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
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1777)
