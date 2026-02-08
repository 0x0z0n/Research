<?php
require_once __DIR__ . '/includes/session.php';
session_unset();
session_destroy();
session_regenerate_id(true);
header('Location: index.php');
exit;