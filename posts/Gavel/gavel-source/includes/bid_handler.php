<?php
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/db.php';
require_once __DIR__ . '/session.php';

header('Content-Type: application/json');

if (!isset($_SESSION['user'])) {
    echo json_encode(['success' => false, 'message' => 'You must be logged in.']);
    exit;
}

$auction_id = (int) ($_POST['auction_id'] ?? 0);
$bid_amount = (int) ($_POST['bid_amount'] ?? 0);
$id = $_SESSION['user']['id'] ?? null;
$username = $_SESSION['user']['username'] ?? null;

$stmt = $pdo->prepare("SELECT * FROM auctions WHERE id = ?");
$stmt->execute([$auction_id]);
$auction = $stmt->fetch();

if (!$auction || $auction['status'] !== 'active' || strtotime($auction['ends_at']) < time()) {
    echo json_encode(['success' => false, 'message' => 'Auction has ended.']);
    exit;
}

if ($bid_amount <= 0) {
    echo json_encode(['success' => false, 'message' => 'Your bid must be greater than 0.']);
    exit;
}

if ($bid_amount <= $auction['current_price']) {
    echo json_encode(['success' => false, 'message' => 'Your bid must be more than the current bid amount!']);
    exit;
}

$stmt = $pdo->prepare("SELECT money FROM users WHERE id = ?");
$stmt->execute([$id]);
$user = $stmt->fetch();

if (!$user || $user['money'] < $bid_amount) {
    echo json_encode(['success' => false, 'message' => 'Insufficient funds to place this bid.']);
    exit;
}

$current_bid = $bid_amount;
$previous_bid = $auction['current_price'];
$bidder = $username;

$rule = $auction['rule'];
$rule_message = $auction['message'];

$allowed = false;

try {
    if (function_exists('ruleCheck')) {
        runkit_function_remove('ruleCheck');
    }
    runkit_function_add('ruleCheck', '$current_bid, $previous_bid, $bidder', $rule);
    error_log("Rule: " . $rule);
    $allowed = ruleCheck($current_bid, $previous_bid, $bidder);
} catch (Throwable $e) {
    error_log("Rule error: " . $e->getMessage());
    $allowed = false;
}

if (!$allowed) {
    echo json_encode(['success' => false, 'message' => $rule_message]);
    exit;
}

try {
    $pdo->beginTransaction();
    $newEndsAt = date('Y-m-d H:i:s', time() + 120);
    $stmt = $pdo->prepare("UPDATE auctions SET current_price = ?, highest_bidder = ?, ends_at = ? WHERE id = ?");
    $stmt->execute([$bid_amount, $username, $newEndsAt, $auction_id]);

    $stmt = $pdo->prepare("UPDATE users SET money = money - ? WHERE id = ?");
    $stmt->execute([$bid_amount, $id]);

    $pdo->commit();
} catch (Exception $e) {
    $pdo->rollBack();
    echo json_encode(['success' => false, 'message' => 'Transaction failed. Try again.']);
    exit;
}

echo json_encode(['success' => true, 'message' => 'Bid placed successfully!']);