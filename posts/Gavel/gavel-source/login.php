<?php
require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/session.php';

if (isset($_SESSION['user'])) {
    header("Location: index.php");
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';

    $username = filter_var($username, FILTER_SANITIZE_STRING);

    if (!$username || !$password) {
        $_SESSION['login_error'] = "Username and password are required.";
    } else {
        try {
            $stmt = $pdo->prepare("SELECT id, password, role FROM users WHERE username = :username");
            $stmt->execute(['username' => $username]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);

            if ($user && password_verify($password, $user['password'])) {
		session_regenerate_id(true);
                $_SESSION['user'] = [
                    'id' => $user['id'],
                    'username' => $username,
                    'role' => $user['role']
                ];
                header("Location: index.php");
                exit;
            } else {
                $_SESSION['login_error'] = "Invalid username or password.";
            }
        } catch (PDOException $e) {
            $_SESSION['login_error'] = "Server error. Please try again.";
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Gavel Auction - Enter the Hall</title>
    <link rel="icon" type="image/x-icon" href="<?= ASSETS_URL ?>/img/favicon.ico">
    <link href="<?= ASSETS_URL ?>/vendor/fontawesome-free/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Caudex&display=swap" rel="stylesheet">
    <link href="<?= ASSETS_URL ?>/css/sb-admin-2.css" rel="stylesheet">
</head>

<body class="bg-gradient-dark">
    <?php if (!empty($_SESSION['register_success'])): ?>
        <div class="alert alert-success text-center">
            <?= htmlspecialchars($_SESSION['register_success']) ?>
        </div>
        <?php unset($_SESSION['register_success']); ?>
    <?php endif; ?>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-xl-10 col-lg-12 col-md-9">
                <div class="card o-hidden border-0 shadow-lg my-5">
                    <div class="card-body p-0">
                        <div class="row">
                            <div class="col-lg-6 d-none d-lg-flex align-items-center justify-content-center flex-column text-white"
                                style="background-image: url(<?= ASSETS_URL ?>/img/welcome.png); background-size: cover; background-position: center;">
                            </div>
                            <div class="col-lg-6">
                                <div class="p-5">
                                    <div class="text-center mb-4">
                                        <h1 class="h4 text-gray-900"><i class="fas fa-coins"></i> Welcome, Bidders!</h1>
                                        <p class="small">Only those with true intent may enter the sacred auction.</p>
                                    </div>

                                    <?php if (!empty($_SESSION['login_error'])): ?>
                                        <div class="alert alert-danger text-center">
                                            <?= htmlspecialchars($_SESSION['login_error']) ?>
                                        </div>
                                        <?php unset($_SESSION['login_error']); ?>
                                    <?php endif; ?>

                                    <form class="user" action="" method="POST">
                                        <div class="form-group">
                                            <input type="text" name="username" class="form-control form-control-user"
                                                placeholder="Username" required>
                                        </div>
                                        <div class="form-group">
                                            <input type="password" name="password" class="form-control form-control-user"
                                                placeholder="Password" required>
                                        </div>
                                        <div class="text-center small text-muted mb-1">
                                            <a><i class="fas fa-question-circle"></i> Forgot your password? Click here</a>
                                        </div>
                                        <button type="submit" class="btn btn-dark btn-user btn-block">
                                            <i class="fas fa-sign-in-alt"></i> Enter the Auction Hall
                                        </button>
                                    </form>
                                    <hr class="my-2">
                                    <div class="text-left">
                                        <div class="d-flex justify-content-between">
                                            <a class="small" href="index.php"><i class="fas fa-home"></i> Go to Home</a>
                                            <a class="small" href="register.php">No account? Create one</a>
                                        </div>
                                    </div>
                                    <div class="text-justify mt-3">
                                        <small class="text-gray-900"> By entering, you acknowledge that you are responsible for your own actions.</small>
                                    </div>
                                </div>
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
