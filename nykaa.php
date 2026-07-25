<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');

$apiUrl = 'http://localhost:5000/scrape';

$response = file_get_contents($apiUrl);
$data = json_decode($response, true);

if ($data['success']) {
    echo $data['data'];
} else {
    echo 'Error: ' . $data['error'];
}
?>
