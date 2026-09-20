using ScaffoldPortal.Models;
using ScaffoldPortal.ViewModels;

namespace ScaffoldPortal.Services
{
    // ── Package Service ───────────────────────────────────────────────────────
    public interface IPackageService
    {
        Task<IEnumerable<Package>> GetAllPackagesAsync();
        Task<IEnumerable<Package>> GetPackagesByStatusAsync(PackageStatus status);
        Task<IEnumerable<Package>> GetPackagesByUploaderAsync(string username);
        Task<Package?> GetPackageByIdAsync(int id);
        Task<Package> CreatePackageAsync(Package package);
        Task UpdatePackageAsync(Package package);
        Task<DashboardViewModel> GetDashboardDataAsync();
    }

    // ── Validation Service ────────────────────────────────────────────────────
    public interface IValidationService
    {
        Task<IEnumerable<Package>> GetValidationQueueAsync();
        Task ApprovePackageAsync(int packageId, string validatorUsername, string notes, ValidationChecklist checklist);
        Task RejectPackageAsync(int packageId, string validatorUsername, string notes);
        Task<IEnumerable<ValidationAction>> GetValidationHistoryAsync(int packageId);
    }

    // ── Audit Service ─────────────────────────────────────────────────────────
    public interface IAuditService
    {
        Task LogAsync(string userIdentity, string action, string? details = null,
            int? packageId = null, string? packageName = null, string? sha256 = null,
            string severity = "INFO", string? adGroups = null);
        Task<IEnumerable<AuditLog>> GetRecentLogsAsync(int count = 100);
        Task<IEnumerable<AuditLog>> GetLogsByPackageAsync(int packageId);
        Task<IEnumerable<AuditLog>> SearchLogsAsync(string? user, string? action, DateTime? from, DateTime? to);
    }

    // ── Deployment Service ────────────────────────────────────────────────────
    public interface IDeploymentService
    {
        Task<IEnumerable<DeploymentHistory>> GetRecentDeploymentsAsync(int count = 50);
        Task<IEnumerable<DeploymentHistory>> GetDeploymentsByPackageAsync(int packageId);
        Task QueueForDeploymentAsync(int packageId, string adminUsername);
        Task RecordEngineResultAsync(int packageId, DeploymentResult result, string? engineOutput, string? failureReason);
    }

    // ── MSI Metadata Service ──────────────────────────────────────────────────
    public interface IMsiMetadataService
    {
        Task<MsiMetadata> ExtractMetadataAsync(string filePath);
        Task<string> ComputeSha256Async(string filePath);
        Task<CertificateInfo> ExtractCertificateInfoAsync(string filePath);
    }

    // ── File Storage Service ──────────────────────────────────────────────────
    public interface IFileStorageService
    {
        Task<string> SaveIncomingAsync(IFormFile file, string safeBaseName);
        Task<string> MoveToReadyAsync(string incomingPath, string storedFileName);
        Task<string> MoveToRejectedAsync(string incomingPath, string storedFileName, string? appName = null);
        bool IsValidMsiFile(IFormFile file);
        string GenerateStoredFileName(string originalName);
    }
}

namespace ScaffoldPortal.ViewModels
{
    public class ValidationChecklist
    {
        public bool SignatureOk { get; set; }
        public bool HashOk { get; set; }
        public bool ProductCodeOk { get; set; }
        public bool MetadataOk { get; set; }
    }

    public class MsiMetadata
    {
        public string? ProductName { get; set; }
        public string? ProductCode { get; set; }
        public string? ProductVersion { get; set; }
        public string? Manufacturer { get; set; }
    }

    public class CertificateInfo
    {
        public string? Subject { get; set; }
        public string? Issuer { get; set; }
        public string? Thumbprint { get; set; }
        public DateTime? NotBefore { get; set; }
        public DateTime? NotAfter { get; set; }
        public bool IsSigned { get; set; }
    }

    public class DashboardViewModel
    {
        public int PendingCount { get; set; }
        public int UnderReviewCount { get; set; }
        public int ApprovedCount { get; set; }
        public int RejectedCount { get; set; }
        public int DeployedCount { get; set; }
        public int FailedCount { get; set; }
        public IEnumerable<ScaffoldPortal.Models.Package> RecentPackages { get; set; } = [];
        public IEnumerable<ScaffoldPortal.Models.DeploymentHistory> RecentDeployments { get; set; } = [];
        public IEnumerable<ScaffoldPortal.Models.AuditLog> RecentAuditLogs { get; set; } = [];
    }
}
