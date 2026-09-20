using Microsoft.EntityFrameworkCore;
using ScaffoldPortal.Data;
using ScaffoldPortal.Models;
using ScaffoldPortal.ViewModels;
using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace ScaffoldPortal.Services
{
    // ── Package Service Implementation ────────────────────────────────────────
    public class PackageService : IPackageService
    {
        private readonly ScaffoldDbContext _db;
        private readonly ILogger<PackageService> _log;

        public PackageService(ScaffoldDbContext db, ILogger<PackageService> log)
        {
            _db = db;
            _log = log;
        }

        public async Task<IEnumerable<Package>> GetAllPackagesAsync() =>
            await _db.Packages.OrderByDescending(p => p.UploadedAt).ToListAsync();

        public async Task<IEnumerable<Package>> GetPackagesByStatusAsync(PackageStatus status) =>
            await _db.Packages.Where(p => p.Status == status)
                .OrderByDescending(p => p.UploadedAt).ToListAsync();

        public async Task<IEnumerable<Package>> GetPackagesByUploaderAsync(string username) =>
            await _db.Packages.Where(p => p.UploadedBy == username)
                .OrderByDescending(p => p.UploadedAt).ToListAsync();

        public async Task<Package?> GetPackageByIdAsync(int id) =>
            await _db.Packages
                .Include(p => p.ValidationActions)
                .Include(p => p.Deployments)
                .Include(p => p.AuditLogs)
                .FirstOrDefaultAsync(p => p.Id == id);

        public async Task<Package> CreatePackageAsync(Package package)
        {
            _db.Packages.Add(package);
            await _db.SaveChangesAsync();
            return package;
        }

        public async Task UpdatePackageAsync(Package package)
        {
            _db.Packages.Update(package);
            await _db.SaveChangesAsync();
        }

        public async Task<DashboardViewModel> GetDashboardDataAsync()
        {
            var counts = await _db.Packages
                .GroupBy(p => p.Status)
                .Select(g => new { Status = g.Key, Count = g.Count() })
                .ToListAsync();

            var vm = new DashboardViewModel
            {
                PendingCount = counts.FirstOrDefault(c => c.Status == PackageStatus.Pending)?.Count ?? 0,
                UnderReviewCount = counts.FirstOrDefault(c => c.Status == PackageStatus.UnderReview)?.Count ?? 0,
                ApprovedCount = counts.FirstOrDefault(c => c.Status == PackageStatus.Approved)?.Count ?? 0,
                RejectedCount = counts.FirstOrDefault(c => c.Status == PackageStatus.Rejected)?.Count ?? 0,
                DeployedCount = counts.FirstOrDefault(c => c.Status == PackageStatus.Deployed)?.Count ?? 0,
                FailedCount = counts.FirstOrDefault(c => c.Status == PackageStatus.Failed)?.Count ?? 0,
                RecentPackages = await _db.Packages.OrderByDescending(p => p.UploadedAt).Take(10).ToListAsync(),
                RecentDeployments = await _db.DeploymentHistories
                    .Include(d => d.Package)
                    .OrderByDescending(d => d.TriggeredAt).Take(10).ToListAsync(),
                RecentAuditLogs = await _db.AuditLogs.OrderByDescending(a => a.Timestamp).Take(10).ToListAsync()
            };
            return vm;
        }
    }

    // ── Validation Service Implementation ─────────────────────────────────────
    public class ValidationService : IValidationService
    {
        private readonly ScaffoldDbContext _db;
        private readonly IFileStorageService _fileStorage;
        private readonly IAuditService _audit;
        private readonly ILogger<ValidationService> _log;

        public ValidationService(ScaffoldDbContext db, IFileStorageService fs,
            IAuditService audit, ILogger<ValidationService> log)
        {
            _db = db; _fileStorage = fs; _audit = audit; _log = log;
        }

        public async Task<IEnumerable<Package>> GetValidationQueueAsync() =>
            await _db.Packages
                .Where(p => p.Status == PackageStatus.Pending || p.Status == PackageStatus.UnderReview)
                .OrderBy(p => p.UploadedAt).ToListAsync();

        public async Task ApprovePackageAsync(int packageId, string validatorUsername,
            string notes, ValidationChecklist checklist)
        {
            var pkg = await _db.Packages.FindAsync(packageId)
                ?? throw new InvalidOperationException($"Package {packageId} not found.");

            // Security: only move from Incoming when validator explicitly approves
            var readyPath = await _fileStorage.MoveToReadyAsync(pkg.IncomingPath!, pkg.StoredFileName);

            pkg.Status = PackageStatus.Approved;
            pkg.ReadyPath = readyPath;
            pkg.ReviewedBy = validatorUsername;
            pkg.ReviewedAt = DateTime.UtcNow;
            pkg.ValidationNotes = notes;

            _db.ValidationActions.Add(new ValidationAction
            {
                PackageId = packageId,
                ValidatorUsername = validatorUsername,
                IsApproved = true,
                Notes = notes,
                ChecklistSignatureOk = checklist.SignatureOk ? "PASS" : "FAIL",
                ChecklistHashOk = checklist.HashOk ? "PASS" : "FAIL",
                ChecklistProductCodeOk = checklist.ProductCodeOk ? "PASS" : "FAIL",
                ChecklistMetadataOk = checklist.MetadataOk ? "PASS" : "FAIL"
            });

            await _db.SaveChangesAsync();

            await _audit.LogAsync(validatorUsername, "PACKAGE_APPROVED",
                $"Package approved. Notes: {notes}", packageId, pkg.OriginalFileName, pkg.Sha256Hash,
                severity: "INFO");

            _log.LogInformation("[VALIDATION] Package {Id} '{Name}' approved by {User}",
                packageId, pkg.OriginalFileName, validatorUsername);
        }

        public async Task RejectPackageAsync(int packageId, string validatorUsername, string notes)
        {
            var pkg = await _db.Packages.FindAsync(packageId)
                ?? throw new InvalidOperationException($"Package {packageId} not found.");

            var rejectedPath = await _fileStorage.MoveToRejectedAsync(
                pkg.IncomingPath!, pkg.StoredFileName, pkg.ProductName);

            pkg.Status = PackageStatus.Rejected;
            pkg.RejectedPath = rejectedPath;
            pkg.ReviewedBy = validatorUsername;
            pkg.ReviewedAt = DateTime.UtcNow;
            pkg.ValidationNotes = notes;

            _db.ValidationActions.Add(new ValidationAction
            {
                PackageId = packageId,
                ValidatorUsername = validatorUsername,
                IsApproved = false,
                Notes = notes
            });

            await _db.SaveChangesAsync();

            await _audit.LogAsync(validatorUsername, "PACKAGE_REJECTED",
                $"Package rejected. Notes: {notes}", packageId, pkg.OriginalFileName, pkg.Sha256Hash,
                severity: "WARN");

            _log.LogWarning("[VALIDATION] Package {Id} '{Name}' REJECTED by {User}. Reason: {Notes}",
                packageId, pkg.OriginalFileName, validatorUsername, notes);
        }

        public async Task<IEnumerable<ValidationAction>> GetValidationHistoryAsync(int packageId) =>
            await _db.ValidationActions
                .Where(v => v.PackageId == packageId)
                .OrderByDescending(v => v.ActionAt).ToListAsync();
    }

    // ── Audit Service Implementation ──────────────────────────────────────────
    public class AuditService : IAuditService
    {
        private readonly ScaffoldDbContext _db;
        private readonly IHttpContextAccessor _http;

        public AuditService(ScaffoldDbContext db, IHttpContextAccessor http)
        {
            _db = db; _http = http;
        }

        public async Task LogAsync(string userIdentity, string action, string? details = null,
            int? packageId = null, string? packageName = null, string? sha256 = null,
            string severity = "INFO", string? adGroups = null)
        {
            var entry = new AuditLog
            {
                UserIdentity = userIdentity,
                Action = action,
                Details = details,
                PackageId = packageId,
                PackageName = packageName,
                Sha256 = sha256,
                Severity = severity,
                AdGroups = adGroups,
                MachineName = Environment.MachineName,
                IpAddress = _http.HttpContext?.Connection.RemoteIpAddress?.ToString()
            };
            _db.AuditLogs.Add(entry);
            await _db.SaveChangesAsync();
        }

        public async Task<IEnumerable<AuditLog>> GetRecentLogsAsync(int count = 100) =>
            await _db.AuditLogs.OrderByDescending(a => a.Timestamp).Take(count).ToListAsync();

        public async Task<IEnumerable<AuditLog>> GetLogsByPackageAsync(int packageId) =>
            await _db.AuditLogs.Where(a => a.PackageId == packageId)
                .OrderByDescending(a => a.Timestamp).ToListAsync();

        public async Task<IEnumerable<AuditLog>> SearchLogsAsync(
            string? user, string? action, DateTime? from, DateTime? to)
        {
            var q = _db.AuditLogs.AsQueryable();
            if (!string.IsNullOrWhiteSpace(user))
                q = q.Where(a => a.UserIdentity.Contains(user));
            if (!string.IsNullOrWhiteSpace(action))
                q = q.Where(a => a.Action.Contains(action));
            if (from.HasValue)
                q = q.Where(a => a.Timestamp >= from.Value);
            if (to.HasValue)
                q = q.Where(a => a.Timestamp <= to.Value);
            return await q.OrderByDescending(a => a.Timestamp).Take(500).ToListAsync();
        }
    }

    // ── Deployment Service Implementation ─────────────────────────────────────
    public class DeploymentService : IDeploymentService
    {
        private readonly ScaffoldDbContext _db;
        private readonly IAuditService _audit;
        private readonly ILogger<DeploymentService> _log;

        public DeploymentService(ScaffoldDbContext db, IAuditService audit, ILogger<DeploymentService> log)
        {
            _db = db; _audit = audit; _log = log;
        }

        public async Task<IEnumerable<DeploymentHistory>> GetRecentDeploymentsAsync(int count = 50) =>
            await _db.DeploymentHistories
                .Include(d => d.Package)
                .OrderByDescending(d => d.TriggeredAt).Take(count).ToListAsync();

        public async Task<IEnumerable<DeploymentHistory>> GetDeploymentsByPackageAsync(int packageId) =>
            await _db.DeploymentHistories
                .Where(d => d.PackageId == packageId)
                .OrderByDescending(d => d.TriggeredAt).ToListAsync();

        public async Task QueueForDeploymentAsync(int packageId, string adminUsername)
        {
            // Security: only APPROVED packages may be queued — the engine itself validates further
            var pkg = await _db.Packages.FindAsync(packageId)
                ?? throw new InvalidOperationException($"Package {packageId} not found.");

            if (pkg.Status != PackageStatus.Approved)
                throw new InvalidOperationException("Only approved packages may be queued for deployment.");

            _db.DeploymentHistories.Add(new DeploymentHistory
            {
                PackageId = packageId,
                TriggeredBy = adminUsername,
                Result = DeploymentResult.Pending
            });

            pkg.Status = PackageStatus.Deploying;
            await _db.SaveChangesAsync();

            await _audit.LogAsync(adminUsername, "DEPLOYMENT_QUEUED",
                $"Package queued for engine deployment.", packageId, pkg.OriginalFileName, pkg.Sha256Hash);

            _log.LogInformation("[DEPLOY] Package {Id} queued for deployment by {User}", packageId, adminUsername);
        }

        public async Task RecordEngineResultAsync(int packageId, DeploymentResult result,
            string? engineOutput, string? failureReason)
        {
            var deployment = await _db.DeploymentHistories
                .Where(d => d.PackageId == packageId && d.Result == DeploymentResult.Pending)
                .OrderByDescending(d => d.TriggeredAt).FirstOrDefaultAsync();

            if (deployment != null)
            {
                deployment.Result = result;
                deployment.CompletedAt = DateTime.UtcNow;
                deployment.EngineOutput = engineOutput;
                deployment.FailureReason = failureReason;
            }

            var pkg = await _db.Packages.FindAsync(packageId);
            if (pkg != null)
                pkg.Status = result == DeploymentResult.Success || result == DeploymentResult.AlreadyCurrent
                    ? PackageStatus.Deployed : PackageStatus.Failed;

            await _db.SaveChangesAsync();
        }
    }

    // ── MSI Metadata Service ──────────────────────────────────────────────────
    public class MsiMetadataService : IMsiMetadataService
    {
        private readonly ILogger<MsiMetadataService> _log;

        public MsiMetadataService(ILogger<MsiMetadataService> log) { _log = log; }

        public async Task<MsiMetadata> ExtractMetadataAsync(string filePath)
        {
            // Uses WindowsInstaller COM via PowerShell subprocess.
            // Security: we NEVER execute the MSI — only query its property table.
            var meta = new MsiMetadata();
            try
            {
                var props = new[] { "ProductName", "ProductCode", "ProductVersion", "Manufacturer" };
                foreach (var prop in props)
                {
                    var psi = new System.Diagnostics.ProcessStartInfo("powershell.exe",
                        $"-NoProfile -NonInteractive -Command \"" +
                        $"$wi = New-Object -ComObject WindowsInstaller.Installer;" +
                        $"$db = $wi.OpenDatabase('{filePath.Replace("'", "''")}', 0);" +
                        $"$v = $db.OpenView(\\\"SELECT Value FROM Property WHERE Property='{prop}'\\\");" +
                        $"$v.Execute(); $r = $v.Fetch(); if ($r) {{ $r.StringData(1) }}\"")
                    {
                        RedirectStandardOutput = true,
                        UseShellExecute = false
                    };
                    using var proc = System.Diagnostics.Process.Start(psi);
                    var val = (await proc!.StandardOutput.ReadToEndAsync()).Trim();
                    proc.WaitForExit();
                    switch (prop)
                    {
                        case "ProductName": meta.ProductName = val; break;
                        case "ProductCode": meta.ProductCode = val; break;
                        case "ProductVersion": meta.ProductVersion = val; break;
                        case "Manufacturer": meta.Manufacturer = val; break;
                    }
                }
            }
            catch (Exception ex)
            {
                _log.LogWarning(ex, "[METADATA] Failed to extract MSI metadata from {Path}", filePath);
            }
            return meta;
        }

        public async Task<string> ComputeSha256Async(string filePath)
        {
            using var sha = SHA256.Create();
            await using var fs = File.OpenRead(filePath);
            var hash = await sha.ComputeHashAsync(fs);
            return Convert.ToHexString(hash);
        }

        public async Task<CertificateInfo> ExtractCertificateInfoAsync(string filePath)
        {
            var info = new CertificateInfo();
            try
            {
                var cert = new System.Security.Cryptography.X509Certificates
                    .X509Certificate2(filePath);
                info.Subject = cert.Subject;
                info.Issuer = cert.Issuer;
                info.Thumbprint = cert.Thumbprint;
                info.NotBefore = cert.NotBefore;
                info.NotAfter = cert.NotAfter;
                info.IsSigned = true;
            }
            catch
            {
                info.IsSigned = false;
            }
            return await Task.FromResult(info);
        }
    }

    // ── File Storage Service ──────────────────────────────────────────────────
    public class FileStorageService : IFileStorageService
    {
        private const string IncomingRoot = @"C:\Software\Packages\Incoming";
        private const string ReadyRoot = @"C:\Software\Packages\Ready";
        private const string RejectedRoot = @"C:\Software\Packages\Rejected";
        private const long MaxFileSizeBytes = 7 * 1024 * 1024; // 7 MB

        public bool IsValidMsiFile(IFormFile file)
        {
            // Security: validate by extension AND check PE/MSI magic bytes
            if (file.Length == 0 || file.Length > MaxFileSizeBytes) return false;
            if (!file.FileName.EndsWith(".msi", StringComparison.OrdinalIgnoreCase)) return false;

            // Read first 8 bytes — MSI (Compound Document) starts with D0 CF 11 E0 A1 B1 1A E1
            Span<byte> header = stackalloc byte[8];
            using var s = file.OpenReadStream();
            return s.Read(header) == 8
                && header[0] == 0xD0 && header[1] == 0xCF && header[2] == 0x11 && header[3] == 0xE0;
        }

        public string GenerateStoredFileName(string originalName)
        {
            // Security: strip all path components, sanitise characters, inject timestamp + GUID fragment
            var baseName = Path.GetFileNameWithoutExtension(originalName);
            var safe = Regex.Replace(baseName, @"[^a-zA-Z0-9_\-]", "_");
            safe = safe.Length > 64 ? safe[..64] : safe;
            var ts = DateTime.UtcNow.ToString("yyyyMMdd_HHmmssfff");
            var guid = Guid.NewGuid().ToString("N")[..16];
            return $"{safe}_{ts}_{guid}.msi";
        }

        public async Task<string> SaveIncomingAsync(IFormFile file, string safeBaseName)
        {
            Directory.CreateDirectory(IncomingRoot);
            var destPath = Path.Combine(IncomingRoot, safeBaseName);

            // Security: prevent path traversal by ensuring destination is inside IncomingRoot
            if (!Path.GetFullPath(destPath).StartsWith(Path.GetFullPath(IncomingRoot) + Path.DirectorySeparatorChar))
                throw new InvalidOperationException("Path traversal detected.");

            await using var dest = File.Create(destPath);
            await file.CopyToAsync(dest);
            return destPath;
        }

        public async Task<string> MoveToReadyAsync(string incomingPath, string storedFileName)
        {
            Directory.CreateDirectory(ReadyRoot);
            var dest = Path.Combine(ReadyRoot, storedFileName);
            File.Move(incomingPath, dest, overwrite: false);
            return await Task.FromResult(dest);
        }

        public async Task<string> MoveToRejectedAsync(string incomingPath, string storedFileName, string? appName = null)
        {
            var subDir = Path.Combine(RejectedRoot, string.IsNullOrWhiteSpace(appName) ? "Unknown" : appName);
            Directory.CreateDirectory(subDir);
            var dest = Path.Combine(subDir, storedFileName);
            File.Move(incomingPath, dest, overwrite: false);
            return await Task.FromResult(dest);
        }
    }
}
