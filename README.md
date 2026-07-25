# 🕷 Scraper API

A simple REST API that scrapes any webpage using headless Chrome (Selenium) and returns the content of specific CSS-selected elements. Handles JavaScript-rendered pages.

**Base URL:** `http://93.127.172.192:1777`

---

## Endpoints

### 1. Health Check

```
GET /
```

Verifies the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Working fine"
}
```

---

### 2. Scrape HTML (Single Element)

```
POST /scrape/html
```

Returns the `outerHTML` and `innerHTML` of a single element.

**Request Body:**
```json
{
  "url": "https://www.example.com/page",
  "selector": "#app > div.content"
}
```

| Field      | Type   | Required | Description                        |
|------------|--------|----------|------------------------------------|
| `url`      | string | ✅       | Full URL of the page to scrape     |
| `selector` | string | ✅       | CSS selector of the target element |

**Success Response (200):**
```json
{
  "success": true,
  "outerHTML": "<div class=\"content\"><h1>Hello</h1></div>",
  "innerHTML": "<h1>Hello</h1>"
}
```

**Error Response (500):**
```json
{
  "success": false,
  "error": "Message: no such element..."
}
```

---

### 3. Scrape Text (Single Element)

```
POST /scrape/text
```

Returns only the visible `innerText` of a single element (no HTML tags).

**Request Body:**
```json
{
  "url": "https://www.example.com/page",
  "selector": ".product-title"
}
```

| Field      | Type   | Required | Description                        |
|------------|--------|----------|------------------------------------|
| `url`      | string | ✅       | Full URL of the page to scrape     |
| `selector` | string | ✅       | CSS selector of the target element |

**Success Response (200):**
```json
{
  "success": true,
  "text": "Nykaa Face Mask - 7 Color LED Therapy"
}
```

---

### 4. Scrape Multiple Elements (Same Page)

```
POST /scrape/multi
```

Loads the page **once** and scrapes multiple elements. More efficient than multiple single requests.

**Request Body:**
```json
{
  "url": "https://www.example.com/product",
  "selectors": [
    ".product-title",
    ".product-price",
    ".reviews-section"
  ]
}
```

| Field       | Type     | Required | Description                             |
|-------------|----------|----------|-----------------------------------------|
| `url`       | string   | ✅       | Full URL of the page to scrape          |
| `selectors` | string[] | ✅       | Array of CSS selectors to extract       |

**Success Response (200):**
```json
{
  "success": true,
  "results": [
    {
      "selector": ".product-title",
      "outerHTML": "<h1 class=\"product-title\">LED Mask</h1>",
      "innerHTML": "LED Mask",
      "text": "LED Mask"
    },
    {
      "selector": ".product-price",
      "outerHTML": "<span class=\"product-price\">₹2,499</span>",
      "innerHTML": "₹2,499",
      "text": "₹2,499"
    },
    {
      "selector": ".reviews-section",
      "error": "Message: no such element: Unable to locate element..."
    }
  ]
}
```

Each result object includes:
- `selector` — the selector that was used
- `outerHTML` — full element including its own tag
- `innerHTML` — content inside the element
- `text` — visible text only
- `error` — present instead of HTML fields if that selector wasn't found

---

## Usage Examples

### cURL

```bash
# Single HTML
curl -X POST http://93.127.172.192:1777/scrape/html \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.nykaa.com/product-page/reviews/123", "selector": "div.reviews"}'

# Single Text
curl -X POST http://93.127.172.192:1777/scrape/text \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.nykaa.com/product-page", "selector": "h1.title"}'

# Multiple elements
curl -X POST http://93.127.172.192:1777/scrape/multi \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.nykaa.com/product-page", "selectors": ["h1.title", ".price", ".rating"]}'
```

### JavaScript (fetch)

```javascript
const res = await fetch('http://93.127.172.192:1777/scrape/html', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://www.nykaa.com/product',
    selector: '.product-info'
  })
});
const data = await res.json();
console.log(data.outerHTML);
```

### PHP (cURL)

```php
<?php
$payload = json_encode([
    'url' => 'https://www.nykaa.com/product',
    'selectors' => ['.title', '.price', '.reviews']
]);

$ch = curl_init('http://93.127.172.192:1777/scrape/multi');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_TIMEOUT, 120);

$response = json_decode(curl_exec($ch), true);
curl_close($ch);

foreach ($response['results'] as $result) {
    echo $result['text'] . "\n";
}
```

### Python (requests)

```python
import requests

res = requests.post('http://93.127.172.192:1777/scrape/multi', json={
    'url': 'https://www.nykaa.com/product',
    'selectors': ['.title', '.price', '.rating']
})

for item in res.json()['results']:
    print(item.get('text', item.get('error')))
```

---

## Notes

- **Timeout:** Requests may take 10-20 seconds. The API waits up to 15s for elements to appear on the page. Set your client timeout to at least 120s.
- **JS-rendered pages:** Fully supported. The API uses headless Chrome so JavaScript-heavy SPAs (React, Next.js, etc.) work fine.
- **CSS Selectors:** Use your browser's DevTools → right-click element → "Copy selector" to get the exact selector.
- **CORS:** Enabled for all origins. Can be called from any frontend.
- **Rate limiting:** None currently. Be reasonable with requests — each one spins up a Chrome instance.

---

## Finding CSS Selectors

1. Open the target page in Chrome
2. Right-click the element you want → **Inspect**
3. In DevTools, right-click the highlighted HTML → **Copy** → **Copy selector**
4. Paste it into the `selector` field

---

## Tech Stack

- **Python 3.12** + Flask
- **Selenium** + headless Chrome
- **Gunicorn** (production server)
- **pm2** (process manager)

---

## Server Management

```bash
# Check status
pm2 status

# View logs
pm2 logs scraper-api

# Restart
pm2 restart scraper-api

# Update code
cd ~/scraper-api && git pull && pm2 restart scraper-api
```
