<?php

define('MAIN_PATH', '/var/www/html/gavel');

require_once MAIN_PATH . '/includes/config.php';
require_once MAIN_PATH . '/includes/db.php';

define('MAX_ACTIVE_AUCTIONS', 3);

// === 1. End expired auctions ===
$stmt = $pdo->prepare("SELECT * FROM auctions WHERE ends_at <= NOW() AND status = 'active'");
$stmt->execute();
$expired = $stmt->fetchAll(PDO::FETCH_ASSOC);

foreach ($expired as $auction) {
    $pdo->beginTransaction();

    $update = $pdo->prepare("UPDATE auctions SET status = 'ended' WHERE id = :id");
    $update->execute(['id' => $auction['id']]);

    $ruleFile = ROOT_PATH . '/rules/auction_' . $auction['id'] . '.yaml';
    if (file_exists($ruleFile)) {
        unlink($ruleFile);
    }

    echo "[*] Auction ended for: {$auction['item_name']}\n";

    if (!empty($auction['highest_bidder'])) {
        $userStmt = $pdo->prepare("SELECT id FROM users WHERE username = :username");
        $userStmt->execute(['username' => $auction['highest_bidder']]);
        $user = $userStmt->fetch(PDO::FETCH_ASSOC);

        if ($user) {
            $itemStmt = $pdo->prepare("SELECT id, name, image, description FROM items WHERE name = :name");
            $itemStmt->execute(['name' => $auction['item_name']]);
            $item = $itemStmt->fetch(PDO::FETCH_ASSOC);

            if ($item) {
                $upsert = $pdo->prepare("
                    INSERT INTO inventory (user_id, item_id, item_name, item_image, item_description, quantity)
                    VALUES (:user_id, :item_id, :item_name, :item_image, :item_description, 1)
                    ON DUPLICATE KEY UPDATE quantity = quantity + 1
                ");
                $upsert->execute([
                    'user_id' => $user['id'],
                    'item_id' => $item['id'],
                    'item_name' => $item['name'],
                    'item_image' => $item['image'],
                    'item_description' => $item['description']
                ]);
                echo "[+] Winner '{$auction['highest_bidder']}' received '{$auction['item_name']}'\n";
            }
        }
    }

    $pdo->commit();
}

// === 2. Start new auctions if under limit ===
$stmt = $pdo->prepare("SELECT COUNT(*) FROM auctions WHERE ends_at > NOW() AND status = 'active'");
$stmt->execute();
$activeCount = (int)$stmt->fetchColumn();

if ($activeCount >= MAX_ACTIVE_AUCTIONS) exit;

$items = json_decode(file_get_contents(ROOT_PATH . '/assets/items.json'), true);
if (!$items) exit("[-] Failed to load items.json\n");

$rules = yaml_parse_file(ROOT_PATH . '/rules/default.yaml');
if (!$rules) exit("[-] Failed to load rules.yaml\n");

$available = $items;
shuffle($available);

while ($activeCount < MAX_ACTIVE_AUCTIONS) {
    $entry = array_shift($available);
    if (!$entry) continue;

    $selectedRule = $rules['rules'][array_rand($rules['rules'])];

    $stmt = $pdo->prepare("INSERT INTO auctions
        (item_name, item_image, item_description, starting_price, current_price, highest_bidder, rule, message, started_at, ends_at, status)
        VALUES (:name, :img, :desc, :start, :start, NULL, :rule, :message, NOW(), DATE_ADD(NOW(), INTERVAL 3 MINUTE), 'active')");

    $stmt->execute([
        'name'    => $entry['name'],
        'img'     => $entry['image'],
        'desc'    => $entry['description'],
        'start'   => rand(500, 2000),
        'rule'    => $selectedRule['rule'],
        'message' => $selectedRule['message']
    ]);

    $auctionId = $pdo->lastInsertId();
    file_put_contents(ROOT_PATH . '/rules/auction_' . $auctionId . '.yaml', yaml_emit($selectedRule));

    echo "[+] New auction started for: {$entry['name']}\n";
    $activeCount++;
}
