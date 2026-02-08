<?php
require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/session.php';

if (!isset($_SESSION['user'])) {
    header('Location: index.php');
    exit;
}

$sortItem = $_POST['sort'] ?? $_GET['sort'] ?? 'item_name';
$userId = $_POST['user_id'] ?? $_GET['user_id'] ?? $_SESSION['user']['id'];
$col = "`" . str_replace("`", "", $sortItem) . "`";
$itemMap = [];
$itemMeta = $pdo->prepare("SELECT name, description, image FROM items WHERE name = ?");
try {
    if ($sortItem === 'quantity') {
        $stmt = $pdo->prepare("SELECT item_name, item_image, item_description, quantity FROM inventory WHERE user_id = ? ORDER BY quantity DESC");
        $stmt->execute([$userId]);
    } else {
        $stmt = $pdo->prepare("SELECT $col FROM inventory WHERE user_id = ? ORDER BY item_name ASC");
        $stmt->execute([$userId]);
    }
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
} catch (Exception $e) {
    $results = [];
}
foreach ($results as $row) {
    $firstKey = array_keys($row)[0];
    $name = $row['item_name'] ?? $row[$firstKey] ?? null;
    if (!$name) {
        continue;
    }
    $meta = [];
    try {
        $itemMeta->execute([$name]);
        $meta = $itemMeta->fetch(PDO::FETCH_ASSOC);
    } catch (Exception $e) {
        $meta = [];
    }
    $itemMap[$name] = [
        'name' => $name ?? "",
        'description' => $meta['description'] ?? "",
        'image' => $meta['image'] ?? "",
        'quantity' => $row['quantity'] ?? (is_numeric($row[$firstKey]) ? $row[$firstKey] : 1)
    ];
}
$stmt = $pdo->prepare("SELECT money FROM users WHERE id = ?");
$stmt->execute([$_SESSION['user']['id']]);
$money = $stmt->fetchColumn();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Your Inventory</title>
    <link href="<?= ASSETS_URL ?>/vendor/fontawesome-free/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css?family=Nunito:300,400,700&display=swap" rel="stylesheet">
    <link href="<?= ASSETS_URL ?>/css/sb-admin-2.css" rel="stylesheet">
    <link id="favicon" rel="icon" type="image/x-icon" href="<?= ASSETS_URL ?>/img/favicon.ico">
</head>
<body id="page-top">
    <div id="wrapper">
        <!-- Sidebar -->
        <ul class="navbar-nav bg-gradient-primary sidebar sidebar-dark accordion" id="accordionSidebar">
            <a class="sidebar-brand d-flex align-items-center justify-content-center" href="index.php">
                <div class="sidebar-brand-icon rotate-n-15">
                    <i class="fas fa-gavel"></i>
                </div>
                <div class="sidebar-brand-text mx-3">Gavel</div>
            </a>
            <hr class="sidebar-divider my-0">

            <?php if (!isset($_SESSION['user'])): ?>
                <li class="nav-item">
                    <a class="nav-link" href="index.php">
                        <i class="fas fa-fw fa-home"></i>
                        <span>Home</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="login.php">
                        <i class="fas fa-fw fa-sign-in-alt"></i>
                        <span>Login</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="register.php">
                        <i class="fas fa-fw fa-user-plus"></i>
                        <span>Register</span>
                    </a>
                </li>
            <?php else: ?>
                <li class="nav-item">
                    <a class="nav-link" href="index.php">
                        <i class="fas fa-fw fa-home"></i>
                        <span>Home</span>
                    </a>
                </li>
                <li class="nav-item active">
                    <a class="nav-link" href="inventory.php">
                        <i class="fas fa-box-open"></i>
                        <span>Inventory</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="bidding.php">
                        <i class="fas fa-hammer"></i>
                        <span>Bidding</span>
                    </a>
                </li>
                <?php if ($_SESSION['user']['role'] === 'auctioneer'): ?>
                    <li class="nav-item">
                        <a class="nav-link" href="admin.php">
                            <i class="fas fa-tools"></i>
                            <span>Admin Panel</span>
                        </a>
                    </li>
                <?php endif; ?>
                <hr class="sidebar-divider d-none d-md-block">
                <li class="nav-item">
                    <a class="nav-link" href="logout.php">
                        <i class="fas fa-sign-out-alt"></i>
                        <span>Logout</span>
                    </a>
                </li>
            <?php endif; ?>
        </ul>
        <!-- End of Sidebar -->
        <div class="container-fluid pt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h3 text-gray-800"><i class="fas fa-box-open"></i> Inventory of <?= htmlspecialchars($_SESSION['user']['username']) ?></h1>
                <h1 class="h5 text-gray-800 mb-0"><i class="fas fa-coins"></i> <strong><?= number_format($money, 0, '.', ',') ?></strong></h1>
            </div>
            <hr>
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div class="flex-grow-1 mr-3">
                    <?php if (empty($itemMap)): ?>
                        <div class="alert alert-info mb-0">Your inventory is empty.</div>
                    <?php else: ?>
                        <div class="alert alert-success mb-0">
                            Your inventory.
                        </div>
                    <?php endif; ?>
                </div>
                <form action="" method="POST" class="form-inline" id="sortForm">
                    <label for="sort" class="mr-2 text-dark"><strong>Sort by:</strong></label>
                    <input type="hidden" name="user_id" value="<?= $_SESSION['user']['id'] ?>">
                    <select name="sort" id="sort" class="form-control form-control-sm mr-2" onchange="document.getElementById('sortForm').submit();">
                        <option value="item_name" <?= $sortItem === 'item_name' ? 'selected' : '' ?>>Name</option>
                        <option value="quantity" <?= $sortItem === 'quantity' ? 'selected' : '' ?>>Quantity</option>
                    </select>
                </form>
            </div>
            <div class="row">
                <?php foreach ($itemMap as $item): ?>
                    <div class="col-md-4">
                        <div class="card shadow mb-4">
                            <div class="card-body">
                                <img src="<?= ASSETS_URL ?>/img/<?= htmlspecialchars($item['image']) ?>" class="card-img-top" alt="<?= htmlspecialchars($item['name']) ?>">
                                <hr>
                                <h5 class="card-title"><strong><?= htmlspecialchars($item['name']) ?></strong>
                                <?php if ($item['quantity'] > 1): ?>
                                    <span class="badge badge-pill badge-dark">x<?= $item['quantity'] ?></span>
                                <?php endif; ?>
                                </h5><hr>
                                <p class="card-text text-justify"><?= htmlspecialchars($item['description']) ?></p>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        </div>
    </div>
    <script src="<?= ASSETS_URL ?>/vendor/jquery/jquery.min.js"></script>
    <script src="<?= ASSETS_URL ?>/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="<?= ASSETS_URL ?>/vendor/jquery-easing/jquery.easing.min.js"></script>
    <script src="<?= ASSETS_URL ?>/js/sb-admin-2.min.js"></script>
</body>
</html>
