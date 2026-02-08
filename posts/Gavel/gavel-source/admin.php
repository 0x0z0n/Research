<?php
require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/session.php';
require_once __DIR__ . '/includes/auction.php';

if (!isset($_SESSION['user']) || $_SESSION['user']['role'] !== 'auctioneer') {
    header('Location: index.php');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $auction_id = intval($_POST['auction_id'] ?? 0);
    $rule = trim($_POST['rule'] ?? '');
    $message = trim($_POST['message'] ?? '');

    if ($auction_id > 0 && (empty($rule) || empty($message))) {
        $stmt = $pdo->prepare("SELECT rule, message FROM auctions WHERE id = ?");
        $stmt->execute([$auction_id]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$row) {
            $_SESSION['success'] = 'Auction not found.';
            header('Location: admin.php');
            exit;
        }
        if (empty($rule))    $rule = $row['rule'];
        if (empty($message)) $message = $row['message'];
    }

    if ($auction_id > 0 && $rule && $message) {
        $stmt = $pdo->prepare("UPDATE auctions SET rule = ?, message = ? WHERE id = ?");
        $stmt->execute([$rule, $message, $auction_id]);
        $_SESSION['success'] = 'Rule and message updated successfully!';
        header('Location: admin.php');
        exit;
    }
}

$stmt = $pdo->query("SELECT * FROM auctions WHERE status = 'active' ORDER BY id");
$current_auction = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Auction Admin</title>
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
                <li class="nav-item">
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
                    <li class="nav-item active">
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
            <h1 class="h3 text-gray-800 text-center"><i class="fa fa-lock"></i> Admin Panel</h1>
            <hr>
            <?php if (!empty($_SESSION['success'])): ?>
                <div class="alert alert-success text-center">Rule and message updated successfully!</div>
                <?php unset($_SESSION['success']); ?>
            <?php endif; ?>
            <?php if (!$current_auction): ?>
                <div class="alert alert-warning">No active auctions at the moment. Please check back later.</div>
            <?php else: ?>
                <div class="row">
                    <?php foreach ($current_auction as $auction):
                        $itemDetails = get_item_by_name($auction['item_name']);
                        $remaining = strtotime($auction['ends_at']) - time();
                        ?>
                        <div class="col-md-4">
                            <div class="card shadow mb-4">
                                <div class="card-body text-center">
                                    <img src="<?= ASSETS_URL ?>/img/<?= $itemDetails['image'] ?>" alt="" class="img-fluid mb-3" style="max-height: 200px;">
                                    <h3 class="mb-1"><?= htmlspecialchars($itemDetails['name']) ?></h3>
                                    <p class="mb-1"><?= htmlspecialchars($itemDetails['description']) ?></p>
                                    <hr>
                                    <form class="bidForm mt-4" method="POST">
                                    <input type="hidden" name="auction_id" value="<?= $auction['id'] ?>">
                                    <!-- p class="mb-1 text-justify"><strong>Rule:</strong> <code lang="php"><?= htmlspecialchars($auction['rule']) ?></code></p -->
                                    <input type="text" class="form-control form-control-user" name="rule" placeholder="Edit rule">
                                    <!-- <p class="mb-1 text-justify"><strong>Message:</strong> <?= htmlspecialchars($auction['message']) ?></p> -->
                                    <input type="text" class="form-control form-control-user" name="message" placeholder="Edit message">
                                    <p class="mb-1 text-justify"><strong>Time Remaining:</strong> <span class="timer" data-end="<?= strtotime($auction['ends_at']) ?>"><?= $remaining ?></span> seconds <i class="fas fa-clock"></i></p>
                                    <button class="btn btn-dark btn-user btn-block" type="submit"><i class="fas fa-pencil-alt"></i> Edit</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>

    <!-- Scripts -->
    <script src="<?= ASSETS_URL ?>/vendor/jquery/jquery.min.js"></script>
    <script src="<?= ASSETS_URL ?>/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="<?= ASSETS_URL ?>/vendor/jquery-easing/jquery.easing.min.js"></script>
    <script src="<?= ASSETS_URL ?>/js/sb-admin-2.min.js"></script>
    <script>
        document.querySelectorAll('.timer').forEach(timer => {
            const end = parseInt(timer.dataset.end);
            const pTag = timer.closest('p');
            const interval = setInterval(() => {
                const now = Math.floor(Date.now() / 1000);
                const remaining = end - now;
                if (remaining <= 0) {
                    clearInterval(interval);
                    location.reload();
                } else {
                    timer.innerText = remaining;
                }
            }, 1000);
        });
    </script>
</body>
</html>
