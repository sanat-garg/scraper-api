from flask import Flask, jsonify, request
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

app = Flask(__name__)
CORS(app)


def get_driver():
    service = Service(log_output='/tmp/chromedriver.log')
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
    return webdriver.Chrome(options=options, service=service)


def check_for_block(driver):
    """Detect if the page is a CAPTCHA/bot-block page."""
    blocked = driver.execute_script('''
        var body = document.body ? document.body.innerHTML : '';
        if (body.includes('validateCaptcha') || body.includes('robot') || 
            body.includes('captcha') || body.includes('blocked')) {
            return true;
        }
        return false;
    ''')
    return blocked


def scrape_elements_js(driver, selectors):
    """Use JavaScript to find elements — avoids ChromeDriver crash on complex pages."""
    results = []
    for selector in selectors:
        result = driver.execute_script('''
            var el = document.querySelector(arguments[0]);
            if (el) {
                return {
                    selector: arguments[0],
                    outerHTML: el.outerHTML,
                    innerHTML: el.innerHTML,
                    text: el.innerText || el.textContent || ''
                };
            }
            return null;
        ''', selector)

        if result:
            results.append(result)
        else:
            results.append({"selector": selector, "error": "Element not found"})

    return results


def wait_for_selector_js(driver, selector, timeout=15):
    """Poll for an element using JS instead of WebDriverWait."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        found = driver.execute_script(
            'return document.querySelector(arguments[0]) !== null;', selector
        )
        if found:
            return True
        time.sleep(0.5)
    return False


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

    driver = None
    try:
        driver = get_driver()
        driver.get(data['url'])
        wait_seconds = data.get('wait', 0)
        if wait_seconds:
            time.sleep(wait_seconds)

        if check_for_block(driver):
            return jsonify({"success": False, "error": "Page blocked by anti-bot protection (CAPTCHA). Try again later or use a different IP."}), 403

        selector = data['selector']
        if not wait_for_selector_js(driver, selector):
            return jsonify({"success": False, "error": f"Element not found: {selector}"}), 404

        results = scrape_elements_js(driver, [selector])
        result = results[0]
        if 'error' in result:
            return jsonify({"success": False, "error": result['error']}), 404

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

    driver = None
    try:
        driver = get_driver()
        driver.get(data['url'])
        wait_seconds = data.get('wait', 0)
        if wait_seconds:
            time.sleep(wait_seconds)

        if check_for_block(driver):
            return jsonify({"success": False, "error": "Page blocked by anti-bot protection (CAPTCHA). Try again later or use a different IP."}), 403

        selector = data['selector']
        if not wait_for_selector_js(driver, selector):
            return jsonify({"success": False, "error": f"Element not found: {selector}"}), 404

        results = scrape_elements_js(driver, [selector])
        result = results[0]
        if 'error' in result:
            return jsonify({"success": False, "error": result['error']}), 404

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

    driver = None
    try:
        driver = get_driver()
        driver.get(data['url'])
        wait_seconds = data.get('wait', 0)
        if wait_seconds:
            time.sleep(wait_seconds)

        if check_for_block(driver):
            return jsonify({"success": False, "error": "Page blocked by anti-bot protection (CAPTCHA). Try again later or use a different IP."}), 403

        # Wait for at least the first selector
        wait_for_selector_js(driver, selectors[0])

        results = scrape_elements_js(driver, selectors)
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
