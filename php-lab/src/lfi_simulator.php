<?php
header('Content-Type: text/plain; charset=utf-8');
$file = $_GET['file'] ?? '';
if (!is_string($file) || str_contains($file, "\0") || str_contains($file, '://')) {
    http_response_code(400);
    exit('Invalid path');
}
$root = realpath(__DIR__ . '/uploads');
$path = realpath($root . '/' . $file);
if ($path === false || !str_starts_with($path, $root . DIRECTORY_SEPARATOR) || !is_file($path)) {
    http_response_code(403);
    exit('Only files inside uploads may be included');
}
include $path;