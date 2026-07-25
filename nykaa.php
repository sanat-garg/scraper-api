<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');

$apiUrl = 'https://scraper-api-5u5b.onrender.com/scrape';

$payload = json_encode([
    'url' => 'https://www.ajio.com/signaxo-rechargeable-vacuum-blackhead-remover-/p/701801019_white?',
    'selector' => '#appContainer > div.content > div > div > div.prod-container > div > div.col-4 > div > div.rating-popup'
]);

$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_TIMEOUT, 120);

$response = curl_exec($ch);

if (curl_errno($ch)) {
    echo 'cURL Error: ' . curl_error($ch);
} else {
    $data = json_decode($response, true);
    if ($data['success']) {
        echo $data['html'];
    } else {
        echo 'Error: ' . $data['error'];
    }
}

curl_close($ch);
?>
