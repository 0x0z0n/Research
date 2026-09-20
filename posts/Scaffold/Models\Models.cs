using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ScaffoldPortal.Models
{
    // ── Package status lifecycle ──────────────────────────────────────────────
    public enum PackageStatus
    {
        Pending = 0,
        UnderReview = 1,
        Approved = 2,
        Rejected = 3,
        Deploying = 4,
        Deployed = 5,
        Archived = 6,
        Failed = 7
    }

    public enum DeploymentResult
    {
        Pending = 0,
        Success = 1,
        Skipped = 2,
        Failed = 3,
        AlreadyCurrent = 4
    }

    // ── Package ───────────────────────────────────────────────────────────────
    public class Package
    {
        [Key]
        public int Id { get; set; }

        [Required, MaxLength(260)]
        public string OriginalFileName { get; set; } = default!;

        /// <summary>
        /// Stored filename on disk — includes timestamp + random GUID segment to prevent collisions and path traversal.
        /// Format: {safename}_{yyyyMMdd}_{HHmmssfff}_{guid16}.msi
        /// </summary>
        [Required, MaxLength(300)]
        public string StoredFileName { get; set; } = default!;

        [MaxLength(260)]
        public string? IncomingPath { get; set; }

        [MaxLength(260)]
        public string? ReadyPath { get; set; }

        [MaxLength(260)]
        public string? RejectedPath { get; set; }

        [MaxLength(260)]
        public string? ArchivePath { get; set; }

        // MSI Metadata
        [MaxLength(256)]
        public string? ProductName { get; set; }

        [MaxLength(38)]
        public string? ProductCode { get; set; }   // {XXXXXXXX-...}

        [MaxLength(32)]
        public string? ProductVersion { get; set; }

        [MaxLength(256)]
        public string? Manufacturer { get; set; }

        // Cryptographic identity
        [MaxLength(64)]
        public string? Sha256Hash { get; set; }

        public long FileSizeBytes { get; set; }

        // Certificate info (extracted from Authenticode)
        [MaxLength(512)]
        public string? CertSubject { get; set; }

        [MaxLength(512)]
        public string? CertIssuer { get; set; }

        [MaxLength(40)]
        public string? CertThumbprint { get; set; }

        public DateTime? CertNotBefore { get; set; }
        public DateTime? CertNotAfter { get; set; }
        public bool? IsSigned { get; set; }

        // Workflow state
        public PackageStatus Status { get; set; } = PackageStatus.Pending;

        [Required, MaxLength(128)]
        public string UploadedBy { get; set; } = default!;   // SAMAccountName

        [MaxLength(128)]
        public string? UploadedByDisplayName { get; set; }

        public DateTime UploadedAt { get; set; } = DateTime.UtcNow;

        [MaxLength(128)]
        public string? ReviewedBy { get; set; }

        public DateTime? ReviewedAt { get; set; }

        [MaxLength(1000)]
        public string? ValidationNotes { get; set; }

        // Navigation
        public ICollection<ValidationAction> ValidationActions { get; set; } = new List<ValidationAction>();
        public ICollection<DeploymentHistory> Deployments { get; set; } = new List<DeploymentHistory>();
        public ICollection<AuditLog> AuditLogs { get; set; } = new List<AuditLog>();
    }

    // ── Validation Action ─────────────────────────────────────────────────────
    public class ValidationAction
    {
        [Key]
        public int Id { get; set; }

        [ForeignKey(nameof(Package))]
        public int PackageId { get; set; }
        public Package Package { get; set; } = default!;

        [Required, MaxLength(128)]
        public string ValidatorUsername { get; set; } = default!;

        [MaxLength(128)]
        public string? ValidatorDisplayName { get; set; }

        public bool IsApproved { get; set; }

        [MaxLength(2000)]
        public string? Notes { get; set; }

        public DateTime ActionAt { get; set; } = DateTime.UtcNow;

        [MaxLength(64)]
        public string? ChecklistSignatureOk { get; set; }

        [MaxLength(64)]
        public string? ChecklistHashOk { get; set; }

        [MaxLength(64)]
        public string? ChecklistProductCodeOk { get; set; }

        [MaxLength(64)]
        public string? ChecklistMetadataOk { get; set; }
    }

    // ── Deployment History ────────────────────────────────────────────────────
    public class DeploymentHistory
    {
        [Key]
        public int Id { get; set; }

        [ForeignKey(nameof(Package))]
        public int PackageId { get; set; }
        public Package Package { get; set; } = default!;

        [MaxLength(128)]
        public string? TriggeredBy { get; set; }    // Admin who queued; SYSTEM if engine-initiated

        public DateTime TriggeredAt { get; set; } = DateTime.UtcNow;

        public DateTime? CompletedAt { get; set; }

        public DeploymentResult Result { get; set; } = DeploymentResult.Pending;

        [MaxLength(256)]
        public string? TargetMachine { get; set; }

        [MaxLength(64)]
        public string? InstalledVersion { get; set; }

        [MaxLength(64)]
        public string? PreviousVersion { get; set; }

        [MaxLength(2000)]
        public string? EngineOutput { get; set; }

        [MaxLength(500)]
        public string? FailureReason { get; set; }

        public bool HashChecked { get; set; }
        public bool SignatureValid { get; set; }
    }

    // ── Audit Log ─────────────────────────────────────────────────────────────
    public class AuditLog
    {
        [Key]
        public int Id { get; set; }

        public DateTime Timestamp { get; set; } = DateTime.UtcNow;

        [Required, MaxLength(128)]
        public string UserIdentity { get; set; } = default!;

        [MaxLength(256)]
        public string? AdGroups { get; set; }    // comma-separated roles at time of action

        [Required, MaxLength(128)]
        public string Action { get; set; } = default!;

        [MaxLength(128)]
        public string? EntityType { get; set; }

        public int? EntityId { get; set; }

        [ForeignKey(nameof(Package))]
        public int? PackageId { get; set; }
        public Package? Package { get; set; }

        [MaxLength(260)]
        public string? PackageName { get; set; }

        [MaxLength(64)]
        public string? Sha256 { get; set; }

        [MaxLength(128)]
        public string? MachineName { get; set; }

        [MaxLength(45)]
        public string? IpAddress { get; set; }

        [MaxLength(500)]
        public string? Details { get; set; }

        [MaxLength(16)]
        public string Severity { get; set; } = "INFO";    // INFO | WARN | CRITICAL
    }

    // ── Repository App (mirrors deploy.json entries) ──────────────────────────
    public class RepositoryApp
    {
        [Key]
        public int Id { get; set; }

        [Required, MaxLength(128)]
        public string AppName { get; set; } = default!;

        [MaxLength(38)]
        public string? ProductCode { get; set; }

        [MaxLength(512)]
        public string? TrustedSubject { get; set; }

        [MaxLength(256)]
        public string? TrustedIssuerKeyword { get; set; }

        [MaxLength(260)]
        public string? InstallDir { get; set; }

        [MaxLength(260)]
        public string? VerifyFile { get; set; }

        [MaxLength(256)]
        public string? VerifyCommand { get; set; }

        [MaxLength(256)]
        public string? DisplayNameMatch { get; set; }

        public bool IsActive { get; set; } = true;

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime? UpdatedAt { get; set; }

        [MaxLength(128)]
        public string? CreatedBy { get; set; }
    }
}
