<?php
require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/session.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    $confirm = $_POST['confirm_password'] ?? '';

    $errors = [];
    if (!preg_match('/^[a-zA-Z0-9_]{3,20}$/', $username)) {
        $errors[] = "Username must be 3-20 characters, alphanumeric with underscores only.";
    }

    if (!$username || !$password || !$confirm) {
        $errors[] = "All fields are required.";
    } elseif (strlen($password) < 8) {
        $errors[] = "Password must be at least 8 characters.";
    } elseif ($password !== $confirm) {
        $errors[] = "Passwords do not match.";
    }

    if (empty($errors)) {
        try {
            $stmt = $pdo->prepare("SELECT id FROM users WHERE username = :username");
            $stmt->execute(['username' => $username]);

            if ($stmt->fetch()) {
                $errors[] = "Username already taken.";
            } else {
                $hash = password_hash($password, PASSWORD_DEFAULT);
                $createdAt = date('Y-m-d H:i:s');
                $money = 50000;

                $stmt = $pdo->prepare("INSERT INTO users (username, password, role, created_at, money) VALUES (:username, :password, :role, :created_at, :money)");
                $stmt->execute([
                    'username' => $username,
                    'password' => $hash,
                    'role' => 'user',
                    'created_at' => $createdAt,
                    'money'    => $money,
                ]);

                $_SESSION['register_success'] = "Account created successfully. Please login.";
                header("Location: login.php");
                exit;
            }
        } catch (PDOException $e) {
            $errors[] = "Server error. Please try again.";
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Gavel Auction - Register</title>
    <!-- Assets URL -->
    <?php require_once __DIR__ . '/includes/config.php'; ?>
    <link rel="icon" type="image/x-icon" href="<?= ASSETS_URL ?>/img/favicon.ico">

    <!-- Fonts & Icons -->
    <link href="<?= ASSETS_URL ?>/vendor/fontawesome-free/css/all.min.css" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Caudex&display=swap" rel="stylesheet" />

    <!-- Styles -->
    <link href="<?= ASSETS_URL ?>/css/sb-admin-2.css" rel="stylesheet" />
</head>

<body class="bg-gradient-dark">

<div class="container">
    <div class="row justify-content-center">
        <div class="col-xl-10 col-lg-12 col-md-9">
            <div class="card o-hidden border-0 shadow-lg my-5">
                <div class="card-body p-0">
                    <div class="row">
                    <div class="col-lg-6 d-none d-lg-flex align-items-center justify-content-center flex-column text-white"
                        style="background-image: url('<?= ASSETS_URL ?>/img/welcome.png'); background-size: cover; background-position: center;"></div>
                        <div class="col-lg-6">
                            <div class="p-5">
                        <div class="mb-4">
                            <h1 class="text-center h4 text-gray-900"><i class="fas fa-scroll"></i> Join the Gavel Auction</h1>
                            <p class="small text-justify text-gray-900">Join the Gavel to bid on items that are probably fine, mostly not cursed, and won't summon an ancient evil. Probably.<br />
                            As a bonus, you'll get <strong>50,000 coins</strong> <i class="fas fa-coins fa-fw"></i> to spend on your new favorite hobby: buying mystery artifacts.<br />
                            Oh, and if you refer a friend, you'll both get an additional 10,000 coins each. Because nothing says <i>"I care about you"</i> like <i>"hey, come join me in this sketchy auction house"</i>.</p>
                        </div>

                        <?php if (!empty($errors)): ?>
                            <div class="alert alert-danger">
                                <ul class="mb-0">
                                    <?php foreach ($errors as $error): ?>
                                        <li><?= htmlspecialchars($error) ?></li>
                                    <?php endforeach; ?>
                                </ul>
                            </div>
                        <?php endif; ?>

                        <form class="user" method="post" action="">
                            <div class="form-group">
                                <input type="text" name="username" class="form-control form-control-user"
                                    placeholder="Username" required />
                            </div>
                            <div class="form-group row">
                                <div class="col-sm-6 mb-3 mb-sm-0">
                                    <input type="password" name="password" class="form-control form-control-user"
                                        placeholder="Password" required />
                                </div>
                                <div class="col-sm-6">
                                    <input type="password" name="confirm_password" class="form-control form-control-user"
                                        placeholder="Repeat Password" required />
                                </div>
                                <div class="text-justify small text-muted">
                                    <i class="fas fa-info-circle"></i> At least 8 characters long</i>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-dark btn-user btn-block">
                                Create Account
                            </button>
                        </form>
                        <hr />
                        <div class="text-center">
                            <a class="small" href="index.php"><i class="fas fa-home"></i> Go Home</a>
                        </div>
                        <hr>
                        <div class="small text-justify">
                            Already an esteemed member of the Gavel Auction? Proceed to the <a class="text-primary" href="login.php">login page</a>.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Scripts -->
<script src="<?= ASSETS_URL ?>/vendor/jquery/jquery.min.js"></script>
<script src="<?= ASSETS_URL ?>/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
<script src="<?= ASSETS_URL ?>/vendor/jquery-easing/jquery.easing.min.js"></script>
<script src="<?= ASSETS_URL ?>/js/sb-admin-2.min.js"></script>

</body>
</html>
