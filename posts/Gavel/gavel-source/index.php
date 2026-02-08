<?php
require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/session.php';
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Gavel 2.0 - Fantasy auction house with cursed items, goblin logic, and chaotic energy.">
    <title>Gavel Auction</title>
    <link rel="icon" type="image/x-icon" href="<?= ASSETS_URL ?>/img/favicon.ico">
    <link href="<?= ASSETS_URL ?>/vendor/fontawesome-free/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css?family=Nunito:300,400,700&display=swap" rel="stylesheet">

    <!-- Main CSS -->
    <link href="<?= ASSETS_URL ?>/css/sb-admin-2.css" rel="stylesheet">
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
                <li class="nav-item active">
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
                <li class="nav-item active">
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
                    <li class="nav-item">
                        <a class="nav-link" href="admin.php">
                            <i class="fas fa-tools"></i>
                            <span>Admin Panel</span>
                        </a>
                    </li>
                <?php endif; ?>
            <?php endif; ?>

        </ul>
        <!-- End of Sidebar -->

        <div class="jumbotron bg-light text-center py-5">
            <h1 class="display-4">Welcome to Gavel 2.0</h1>
            <p class="lead">The only auction house foolish enough to rise from its own ashes. Twice.</p>
            <div class="text-justify px-5">
                <p>We don't talk about Gavel 1.0. Ever. (It ended in fire, lawsuits, and one mysteriously vanishing moon.)</p>
                <p>After the Great Goblin Uprising of '22, one lone, sleep-deprived developer (Hi!) forged a new system wrapped in more wards, scripts, and sanity checks than a necromancer's tax return.</p>
                <p>Now our auctioneers wield an arcane Rule Engine so over-engineered it occasionally gains sentience and denies bids for "being too chaotic." Every item is verified. Every bid scrutinized. Every loophole patched, re-opened, and patched again with duct tape and mild hexes.</p>
                <p class="mb-0">Is it overkill? Absolutely. Is it fair? Legally, yes. Is it safe? Debatable. But one thing's for sure—you won't find a more dramatic place to bid on a possibly cursed spoon.</p>
            </div>
            <hr>
            <div class="container-fluid">
                <?php
                $items = json_decode(file_get_contents(__DIR__ . '/assets/items.json'), true);
                if (!is_array($items)) {
                    $items = [];
                } else {
                    shuffle($items);
                    $items = array_slice($items, 0, 3);
                }
                ?>
                <h2 class="text-left"><i class="fas fa-eye"></i> Here's what we've got in our lootbox:</h2>
                <div class="row">
                    <?php foreach ($items as $item): ?>
                        <div class="col-md-4">
                            <div class="card shadow mb-4">
                                <div class="card-body">
                                    <img src="<?= ASSETS_URL ?>/img/<?= htmlspecialchars($item['image']) ?>" class="card-img-top" alt="<?= htmlspecialchars($item['name']) ?>"><hr>
                                    <h5 class="card-title"><strong><?= htmlspecialchars($item['name']) ?></strong></h5><hr>
                                    <p class="card-text text-justify"><?= htmlspecialchars($item['description']) ?></p>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            </div>
            <hr>
            <div class="container-fluid">
                <h2 class="text-left mb-4"><i class="fas fa-quote-left"></i> Testimonies:</h2>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-user-ninja fa-lg mr-2"></i>
                        <strong>Merlox the Mild</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i> (4.5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Bought an invisibility cloak. Lost it instantly. 10/10 would vanish again."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-user-astronaut fa-lg mr-2"></i>
                        <strong>BidGazer99</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="far fa-star"></i><i class="far fa-star"></i> (3/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Was abducted mid-bid. Still got the item tho. Support is out of this world."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-user-secret fa-lg mr-2"></i>
                        <strong>ShadowMartha</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i> (5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Traded my neighbor's soul for a slightly haunted spoon. Best deal yet."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-user-tie fa-lg mr-2"></i>
                        <strong>RuneSniffer42</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i> (5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Accidentally bought a cursed amulet. Now I only sleep upside-down."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-male fa-lg mr-2"></i>
                        <strong>ElvenEarl77</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i><i class="far fa-star"></i> (3.5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Smooth bidding process. Lost the auction, lost my wife. Still fun!"</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-dragon fa-lg mr-2"></i>
                        <strong>WandWarrantyVoid</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i> (5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"The logic engine denied my bid for being 'too lawful'. Respect."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-vial fa-lg mr-2"></i>
                        <strong>VialCollector69</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i><i class="far fa-star"></i> (3.5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Great selection of slightly haunted items. Will shop again (from a distance)."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-skull fa-lg mr-2"></i>
                        <strong>ZedIsDead</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i> (5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"I rose from the grave just to bid. Would recommend."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-dog fa-lg mr-2"></i>
                        <strong>BoneBidderX</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i> (5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Shipping took 3 lunar cycles but the bone was pristine."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-ghost fa-lg mr-2"></i>
                        <strong>GrantMeThis</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i><i class="far fa-star"></i> (3.5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Bidding was intense. Got into a duel. Still won the toothbrush."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-lock fa-lg mr-2"></i>
                        <strong>OwlexaPrime<span style="color: var(--red-curse);"> [banned]</span></strong> — <i class="far fa-star"></i><i class="far fa-star"></i><i class="far fa-star"></i><i class="far fa-star"></i><i class="far fa-star"></i> (0/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Site said 'intelligent bidding system' — I still outsmarted it."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-user-circle fa-lg mr-2"></i>
                        <strong>HalfPriceOgre</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i><i class="far fa-star"></i> (3/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Won a goblin contract. Still reading the fine print. Might be married now."</p>
                </div>

                <div class="mb-4 p-3 bg-light rounded">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas fa-trash fa-lg mr-2"></i>
                        <strong>MagicalTrashbin</strong> — <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i> (5/5 curses)
                    </div>
                    <p class="mb-0 text-justify">"Found my ex's soul jar here. Great condition. Wouldn't return."</p>
                </div>
            </div>
            <!-- Footer -->
            <footer class="sticky-footer bg-white">
                <div class="container my-auto">
                    <div class="text-center my-auto">
                        <hr>
                        <span>Gavel Auction &copy; 2025</span><br>
                        <em class="text-muted">This platform is protected by overengineered automation and mild hexes. Please auction responsibly.</em>
                    </div>
                </div>
            </footer>
            <!-- End of Footer -->
        </div>
    </div>

    <!-- JS Scripts -->
    <script src="<?= ASSETS_URL ?>/vendor/jquery/jquery.min.js"></script>
    <script src="<?= ASSETS_URL ?>/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="<?= ASSETS_URL ?>/vendor/jquery-easing/jquery.easing.min.js"></script>
    <script src="<?= ASSETS_URL ?>/js/sb-admin-2.min.js"></script>
</body>

</html>
