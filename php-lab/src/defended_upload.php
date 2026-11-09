<?php
header('Content-Type: application/json; charset=utf-8');
function respond(int $status, array $data): never {
    http_response_code($status);
    echo json_encode($data);
    exit;
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') respond(405, ['error' => 'POST multipart field file required']);
// PHP discards the entire multipart body when post_max_size is exceeded.
$post_limit = 3 * 1024 * 1024; // Matches php.ini post_max_size=3M.
if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > $post_limit) respond(413, ['error' => 'Request body too large']);
if (!isset($_FILES['file']) || !isset($_FILES['file']['error']) || is_array($_FILES['file']['error'])) respond(400, ['error' => 'Invalid upload']);
if (in_array($_FILES['file']['error'], [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true)) respond(413, ['error' => 'Upload too large']);
if ($_FILES['file']['error'] !== UPLOAD_ERR_OK) respond(400, ['error' => 'Invalid upload']);
$file = $_FILES['file'];
if ($file['size'] > 1048576) respond(413, ['error' => 'Maximum size is 1 MiB']);
$ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
$allowed = ['jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'png' => 'image/png'];
$mime = finfo_file(new finfo(FILEINFO_MIME_TYPE), $file['tmp_name']);
$info = @getimagesize($file['tmp_name']);
if (!isset($allowed[$ext]) || $mime !== $allowed[$ext] || $info === false || $info['mime'] !== $allowed[$ext]) {
    respond(415, ['error' => 'Extension, MIME or image validation failed']);
}
if ($info[0] > 4096 || $info[1] > 4096 || $info[0] * $info[1] > 4000000) respond(413, ['error' => 'Pixel budget exceeded']);
$image = $ext === 'png' ? @imagecreatefrompng($file['tmp_name']) : @imagecreatefromjpeg($file['tmp_name']);
if ($image === false) respond(415, ['error' => 'Image decoder rejected file']);
$safe_name = bin2hex(random_bytes(16)) . '.' . $ext;
$target = '/var/www/storage_outside_webroot/' . $safe_name;
if ($ext === 'png') imagesavealpha($image, true);
$ok = $ext === 'png' ? imagepng($image, $target) : imagejpeg($image, $target, 90);
imagedestroy($image);
if (!$ok) respond(500, ['error' => 'Re-encoding failed']);
chmod($target, 0600);
$bytes = file_get_contents($target);
respond(201, ['stored' => true, 'id' => $safe_name, 'marker_present' => str_contains($bytes, 'B22_UFU_EXEC_SUCCESS')]);