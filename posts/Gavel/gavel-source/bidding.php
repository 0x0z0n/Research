<?php
require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/session.php';
require_once __DIR__ . '/includes/auction.php';

if (!isset($_SESSION['user'])) {
    header('Location: index.php');
    exit;
}

$auctions = get_all_active_auctions($pdo);
$userId = $_SESSION['user']['id'];
$stmt = $pdo->prepare("SELECT money FROM users WHERE id = :id");
$stmt->execute(['id' => $userId]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

$money = $user['money'];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Live Auction</title>
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
                <div class="sidebar-brand-icon rotate-n-15"><i class="fas fa-gavel"></i></div>
                <div class="sidebar-brand-text mx-3">Gavel</div>
            </a>
            <hr class="sidebar-divider my-0">

            <?php if (!isset($_SESSION['user'])): ?>
                <li class="nav-item"><a class="nav-link" href="index.php"><i class="fas fa-fw fa-home"></i><span>Home</span></a></li>
                <li class="nav-item"><a class="nav-link" href="login.php"><i class="fas fa-fw fa-sign-in-alt"></i><span>Login</span></a></li>
                <li class="nav-item"><a class="nav-link" href="register.php"><i class="fas fa-fw fa-user-plus"></i><span>Register</span></a></li>
            <?php else: ?>
                <li class="nav-item"><a class="nav-link" href="index.php"><i class="fas fa-fw fa-home"></i><span>Home</span></a></li>
                <li class="nav-item"><a class="nav-link" href="inventory.php"><i class="fas fa-box-open"></i><span>Inventory</span></a></li>
                <li class="nav-item active"><a class="nav-link" href="bidding.php"><i class="fas fa-hammer"></i><span>Bidding</span></a></li>
                <?php if ($_SESSION['user']['role'] === 'auctioneer'): ?>
                    <li class="nav-item"><a class="nav-link" href="admin.php"><i class="fas fa-tools"></i><span>Admin Panel</span></a></li>
                <?php endif; ?>
                <hr class="sidebar-divider d-none d-md-block">
                <li class="nav-item"><a class="nav-link" href="logout.php"><i class="fas fa-sign-out-alt"></i><span>Logout</span></a></li>
            <?php endif; ?>
        </ul>
        <!-- End of Sidebar -->

        <div class="container-fluid pt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h3 text-gray-800"><i class="fas fa-hammer"></i> Live Auctions</h1>
                <h1 class="h5 text-gray-800 mb-0"><i class="fas fa-coins"></i> <strong><?= number_format($money, 0, '.', ',') ?></strong></h1>
            </div>
            <hr>
            <?php if (!$auctions): ?>
                <div class="alert alert-warning">No active auctions at the moment. Please check back later or <a href="#" onclick="location.reload(); return false;">refresh.</a></div>
            <?php else: ?>
                <p class="text-justify mb-4 text-gray-800">Bidding is binding. In the event you are outbid by another participant, or if you submit overlapping bids, the amount you bid remains non-refundable.</p>
                <div class="row">
                    <?php foreach ($auctions as $auction):
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
                                    <div class="d-flex justify-content-between mb-1">
                                        <p class="mb-0"><strong>Starting:</strong> <?= $auction['starting_price'] ?> <i class="fas fa-coins"></i></p>
                                        <p class="mb-0"><strong>Current:</strong> <?= $auction['current_price'] ?> <i class="fas fa-coins"></i></p>
                                    </div>
                                    <p class="mb-1 text-justify"><strong>Message:</strong> <?= $auction['message'] ?></p>
                                    <p class="mb-1 text-justify"><strong>Highest Bidder:</strong> <?= htmlspecialchars($auction['highest_bidder'] ?? 'None') ?></p>
                                    <p class="mb-1 text-justify"><strong>Time Remaining:</strong> <span class="timer" data-end="<?= strtotime($auction['ends_at']) ?>"><?= $remaining ?></span> seconds <i class="fas fa-clock"></i></p>
                                    <form class="bidForm mt-4" method="POST">
                                        <input type="hidden" name="auction_id" value="<?= $auction['id'] ?>">
                                        <div class="form-group">
                                            <input type="number" class="form-control form-control-user" step="1" name="bid_amount" placeholder="Enter your bid">
                                        </div>
                                        <div class="bidStatus"></div>
                                        <button class="btn btn-dark btn-user btn-block" type="submit"><i class="fas fa-gavel"></i> Place Bid</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>

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
    <script>
        document.querySelectorAll('form.bidForm').forEach(form => {
            form.addEventListener('submit', async function (e) {
                e.preventDefault();

                const formData = new FormData(form);
                const statusDiv = form.querySelector('.bidStatus');

                try {
                    const response = await fetch('includes/bid_handler.php', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        statusDiv.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        statusDiv.innerHTML = `<div class="alert alert-danger">${result.message}</div>`;
                    }
                } catch (err) {
                    statusDiv.innerHTML = `<div class="alert alert-danger">Unexpected error</div>`;
                }
            });
        });
    </script>
</body>
</html>
