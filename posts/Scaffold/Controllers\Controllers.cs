using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ScaffoldPortal.Models;
using ScaffoldPortal.Services;
using ScaffoldPortal.ViewModels;

namespace ScaffoldPortal.Controllers
{
    [Authorize]
    public class HomeController : Controller
    {
        private readonly IPackageService _packages;
        private readonly ILogger<HomeController> _log;

        public HomeController(IPackageService packages, ILogger<HomeController> log)
        {
            _packages = packages; _log = log;
        }

        public async Task<IActionResult> Index()
        {
            var vm = await _packages.GetDashboardDataAsync();
            ViewBag.CurrentUser = User.Identity?.Name ?? "Unknown";
            ViewBag.IsValidator = User.IsInRole(@"SCAFFOLD\Package_Validators");
            ViewBag.IsAdmin = User.IsInRole(@"SCAFFOLD\Deployment_Admins");
            ViewBag.IsDeveloper = User.IsInRole(@"SCAFFOLD\Package_Developers");
            return View(vm);
        }

        public IActionResult Error() => View();
    }

    // ── Package Controller ────────────────────────────────────────────────────
    [Authorize]
    public class PackageController : Controller
    {
        private readonly IPackageService _packages;
        private readonly IMsiMetadataService _msiMeta;
        private readonly IFileStorageService _fileStorage;
        private readonly IAuditService _audit;
        private readonly ILogger<PackageController> _log;

        public PackageController(IPackageService packages, IMsiMetadataService msiMeta,
            IFileStorageService fileStorage, IAuditService audit, ILogger<PackageController> log)
        {
            _packages = packages; _msiMeta = msiMeta;
            _fileStorage = fileStorage; _audit = audit; _log = log;
        }

        // GET /Package — list all packages (admin/validator see all; developer sees own)
        public async Task<IActionResult> Index(string? status, string? search)
        {
            IEnumerable<Package> packages;
            var isPrivileged = User.IsInRole(@"SCAFFOLD\Package_Validators")
                            || User.IsInRole(@"SCAFFOLD\Deployment_Admins");

            if (isPrivileged)
            {
                packages = status != null && Enum.TryParse<PackageStatus>(status, out var s)
                    ? await _packages.GetPackagesByStatusAsync(s)
                    : await _packages.GetAllPackagesAsync();
            }
            else
            {
                // Developers only see their own submissions
                packages = await _packages.GetPackagesByUploaderAsync(User.Identity!.Name!);
            }

            if (!string.IsNullOrWhiteSpace(search))
                packages = packages.Where(p =>
                    (p.ProductName?.Contains(search, StringComparison.OrdinalIgnoreCase) ?? false) ||
                    (p.OriginalFileName.Contains(search, StringComparison.OrdinalIgnoreCase)) ||
                    (p.ProductCode?.Contains(search, StringComparison.OrdinalIgnoreCase) ?? false));

            ViewBag.StatusFilter = status;
            ViewBag.Search = search;
            return View(packages);
        }

        // GET /Package/Details/5
        public async Task<IActionResult> Details(int id)
        {
            var pkg = await _packages.GetPackageByIdAsync(id);
            if (pkg == null) return NotFound();

            // Developers may only view their own packages
            if (!User.IsInRole(@"SCAFFOLD\Package_Validators")
                && !User.IsInRole(@"SCAFFOLD\Deployment_Admins")
                && pkg.UploadedBy != User.Identity!.Name)
                return Forbid();

            return View(pkg);
        }

        // GET /Package/Upload
        [Authorize(Policy = "PackageDeveloper")]
        public IActionResult Upload() => View();

        // POST /Package/Upload
        [HttpPost, Authorize(Policy = "PackageDeveloper")]
        public async Task<IActionResult> Upload(IFormFile file)
        {
            if (file == null || file.Length == 0)
            {
                ModelState.AddModelError("", "No file selected.");
                return View();
            }

            // Security: validate MSI magic bytes + extension before touching disk
            if (!_fileStorage.IsValidMsiFile(file))
            {
                ModelState.AddModelError("", "Invalid file. Only MSI packages up to 7 MB are accepted.");
                await _audit.LogAsync(User.Identity!.Name!, "UPLOAD_REJECTED_INVALID",
                    $"Invalid file rejected: {file.FileName}", severity: "WARN");
                return View();
            }

            try
            {
                var storedName = _fileStorage.GenerateStoredFileName(file.FileName);
                var incomingPath = await _fileStorage.SaveIncomingAsync(file, storedName);

                // Compute SHA256 and extract metadata asynchronously
                var hashTask = _msiMeta.ComputeSha256Async(incomingPath);
                var metaTask = _msiMeta.ExtractMetadataAsync(incomingPath);
                var certTask = _msiMeta.ExtractCertificateInfoAsync(incomingPath);
                await Task.WhenAll(hashTask, metaTask, certTask);

                var hash = hashTask.Result;
                var meta = metaTask.Result;
                var cert = certTask.Result;

                var pkg = new Package
                {
                    OriginalFileName = Path.GetFileName(file.FileName),
                    StoredFileName = storedName,
                    IncomingPath = incomingPath,
                    FileSizeBytes = file.Length,
                    Sha256Hash = hash,
                    ProductName = meta.ProductName,
                    ProductCode = meta.ProductCode,
                    ProductVersion = meta.ProductVersion,
                    Manufacturer = meta.Manufacturer,
                    CertSubject = cert.Subject,
                    CertIssuer = cert.Issuer,
                    CertThumbprint = cert.Thumbprint,
                    CertNotBefore = cert.NotBefore,
                    CertNotAfter = cert.NotAfter,
                    IsSigned = cert.IsSigned,
                    UploadedBy = User.Identity!.Name!,
                    Status = PackageStatus.Pending
                };

                await _packages.CreatePackageAsync(pkg);

                await _audit.LogAsync(User.Identity.Name!, "PACKAGE_UPLOADED",
                    $"MSI uploaded: {file.FileName} ({file.Length:N0} bytes)",
                    pkg.Id, pkg.OriginalFileName, hash);

                _log.LogInformation("[UPLOAD] Package {Id} uploaded by {User}: {File}",
                    pkg.Id, User.Identity.Name, file.FileName);

                TempData["Success"] = $"Package '{pkg.OriginalFileName}' uploaded successfully. SHA256: {hash[..16]}...";
                return RedirectToAction("Details", new { id = pkg.Id });
            }
            catch (Exception ex)
            {
                _log.LogError(ex, "[UPLOAD] Failed to process uploaded file {Name}", file.FileName);
                ModelState.AddModelError("", "Upload failed. Please contact your administrator.");
                return View();
            }
        }
    }

    // ── Validation Controller ─────────────────────────────────────────────────
    [Authorize(Policy = "ValidatorOrAdmin")]
    public class ValidationController : Controller
    {
        private readonly IValidationService _validation;
        private readonly IPackageService _packages;
        private readonly IAuditService _audit;
        private readonly ILogger<ValidationController> _log;

        public ValidationController(IValidationService validation, IPackageService packages,
            IAuditService audit, ILogger<ValidationController> log)
        {
            _validation = validation; _packages = packages; _audit = audit; _log = log;
        }

        public async Task<IActionResult> Index()
        {
            var queue = await _validation.GetValidationQueueAsync();
            return View(queue);
        }

        public async Task<IActionResult> Review(int id)
        {
            var pkg = await _packages.GetPackageByIdAsync(id);
            if (pkg == null) return NotFound();
            return View(pkg);
        }

        [HttpPost]
        public async Task<IActionResult> Approve(int id, string notes,
            bool signatureOk, bool hashOk, bool productCodeOk, bool metadataOk)
        {
            if (string.IsNullOrWhiteSpace(notes))
            {
                TempData["Error"] = "Validation notes are required before approving.";
                return RedirectToAction("Review", new { id });
            }

            var checklist = new ValidationChecklist
            {
                SignatureOk = signatureOk, HashOk = hashOk,
                ProductCodeOk = productCodeOk, MetadataOk = metadataOk
            };

            await _validation.ApprovePackageAsync(id, User.Identity!.Name!, notes, checklist);
            TempData["Success"] = "Package approved and moved to Ready queue.";
            return RedirectToAction("Index");
        }

        [HttpPost]
        public async Task<IActionResult> Reject(int id, string notes)
        {
            if (string.IsNullOrWhiteSpace(notes))
            {
                TempData["Error"] = "Rejection reason is required.";
                return RedirectToAction("Review", new { id });
            }

            await _validation.RejectPackageAsync(id, User.Identity!.Name!, notes);
            TempData["Warning"] = "Package rejected and moved to Rejected folder.";
            return RedirectToAction("Index");
        }
    }

    // ── Deployment Controller ─────────────────────────────────────────────────
    [Authorize(Policy = "DeploymentAdmin")]
    public class DeploymentController : Controller
    {
        private readonly IDeploymentService _deployment;
        private readonly IPackageService _packages;
        private readonly IAuditService _audit;

        public DeploymentController(IDeploymentService deployment, IPackageService packages, IAuditService audit)
        {
            _deployment = deployment; _packages = packages; _audit = audit;
        }

        public async Task<IActionResult> Index()
        {
            var history = await _deployment.GetRecentDeploymentsAsync(100);
            return View(history);
        }

        public async Task<IActionResult> Queue()
        {
            var approved = await _packages.GetPackagesByStatusAsync(PackageStatus.Approved);
            return View(approved);
        }

        [HttpPost]
        public async Task<IActionResult> QueuePackage(int id)
        {
            await _deployment.QueueForDeploymentAsync(id, User.Identity!.Name!);
            TempData["Success"] = "Package queued. The Deploy-Engine.ps1 service will pick it up shortly.";
            return RedirectToAction("Queue");
        }
    }

    // ── Audit Controller ──────────────────────────────────────────────────────
    [Authorize(Policy = "DeploymentAdmin")]
    public class AuditController : Controller
    {
        private readonly IAuditService _audit;

        public AuditController(IAuditService audit) { _audit = audit; }

        public async Task<IActionResult> Index(string? user, string? action, DateTime? from, DateTime? to)
        {
            var logs = await _audit.SearchLogsAsync(user, action, from, to);
            ViewBag.UserFilter = user;
            ViewBag.ActionFilter = action;
            ViewBag.From = from;
            ViewBag.To = to;
            return View(logs);
        }
    }

    // ── Admin Controller ──────────────────────────────────────────────────────
    [Authorize(Policy = "DeploymentAdmin")]
    public class AdminController : Controller
    {
        private readonly ScaffoldPortal.Data.ScaffoldDbContext _db;
        private readonly ILogger<AdminController> _log;

        public AdminController(ScaffoldPortal.Data.ScaffoldDbContext db, ILogger<AdminController> log)
        {
            _db = db; _log = log;
        }

        public async Task<IActionResult> Repository()
        {
            var apps = await _db.RepositoryApps.ToListAsync();
            return View(apps);
        }

        public IActionResult Settings() => View();
    }
}
