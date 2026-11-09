<?php
// Intentionally vulnerable, loopback-only educational scenarios.
header('Content-Type: application/json; charset=utf-8');
function reply(int $status, array $data): never {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_SLASHES);
    exit;
}
$scenario = $_GET['scenario'] ?? 'content_type';
$scenarios = ['content_type', 'double_ext', 'weak_strip', 'null_byte_sim', 'magic_bytes', 'exif_polyglot', 'path_traversal'];
if (!in_array($scenario, $scenarios, true)) reply(400, ['error' => 'Unknown scenario']);
if ($_SERVER['REQUEST_METHOD'] !== 'POST') reply(200, ['scenarios' => $scenarios]);
if (!isset($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) reply(400, ['error' => 'Invalid upload']);
$upload = $_FILES['file'];
$raw = $upload['full_path'] ?? $upload['name'];
$name = basename($upload['name']);
$parts = explode('.', $name);
$ext = strtolower(end($parts));
$accepted = false;
$relative = $name;
switch ($scenario) {
    case 'content_type':
        $accepted = ($upload['type'] === 'image/jpeg' || $upload['type'] === 'image/png') && $upload['size'] < 100000;
        break;
    case 'double_ext':
        $accepted = in_array($ext, ['jpg', 'png'], true);
        break;
    case 'weak_strip':
        $relative = str_replace('php', '', $name);
        $accepted = true;
        break;
    case 'null_byte_sim':
        $accepted = in_array($ext, ['png', 'jpg'], true);
        $relative = preg_split('/%00|\x00/', $name, 2)[0];
        break;
    case 'magic_bytes':
        $handle = fopen($upload['tmp_name'], 'rb');
        $magic = fread($handle, 6);
        fclose($handle);
        $accepted = in_array($magic, ['GIF87a', 'GIF89a'], true);
        break;
    case 'exif_polyglot':
        $accepted = in_array($ext, ['jpg', 'jpeg', 'png'], true) && @getimagesize($upload['tmp_name']) !== false;
        break;
    case 'path_traversal':
        $relative = 'sub/' . $raw;
        $accepted = true;
        break;
}
if (!$accepted) reply(415, ['error' => 'Scenario validation rejected file']);
$target = __DIR__ . '/uploads/' . $relative;
if (!@move_uploaded_file($upload['tmp_name'], $target)) reply(500, ['error' => 'Storage failed']);
reply(200, ['stored' => true, 'scenario' => $scenario, 'name' => $relative, 'url' => '/uploads/' . $relative]);