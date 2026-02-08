<?php
if (session_status() === PHP_SESSION_NONE) {
    ini_set('session.cookie_httponly', 1);
    ini_set('session.use_strict_mode', 1);
    ini_set('session.use_only_cookies', 1);
    ini_set('session.cookie_samesite', 'Strict');
    session_name('gavel_session');
    session_start();
}

if (isset($_SESSION['LAST_ACTIVITY']) && (time() - $_SESSION['LAST_ACTIVITY'] > 1800)) {
    session_unset();
    session_destroy();
}
$_SESSION['LAST_ACTIVITY'] = time();

function set_register_error($error) {
    $_SESSION['register_error'] = $error;
}

function get_register_error() {
    $error = $_SESSION['register_error'] ?? '';
    unset($_SESSION['register_error']);
    return $error;
}

function set_register_success($success) {
    $_SESSION['register_success'] = $success;
}

function get_register_success() {
    $success = $_SESSION['register_success'] ?? '';
    unset($_SESSION['register_success']);
    return $success;
}
