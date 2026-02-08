<?php
require_once __DIR__ . '/db.php';

function get_all_active_auctions(PDO $pdo): array {
    $stmt = $pdo->query("SELECT * FROM auctions WHERE ends_at > NOW() AND status = 'active' ORDER BY ends_at ASC");
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

function get_item_by_name(string $name): ?array {
    $items = json_decode(file_get_contents(__DIR__ . '/../assets/items.json'), true);
    foreach ($items as $item) {
        if ($item['name'] === $name) {
            return $item;
        }
    }
    return null;
}