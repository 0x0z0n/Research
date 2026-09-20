using Microsoft.EntityFrameworkCore;
using ScaffoldPortal.Models;

namespace ScaffoldPortal.Data
{
    public class ScaffoldDbContext : DbContext
    {
        public ScaffoldDbContext(DbContextOptions<ScaffoldDbContext> options) : base(options) { }

        public DbSet<Package> Packages => Set<Package>();
        public DbSet<ValidationAction> ValidationActions => Set<ValidationAction>();
        public DbSet<DeploymentHistory> DeploymentHistories => Set<DeploymentHistory>();
        public DbSet<AuditLog> AuditLogs => Set<AuditLog>();
        public DbSet<RepositoryApp> RepositoryApps => Set<RepositoryApp>();

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Package indexes for common queries
            modelBuilder.Entity<Package>()
                .HasIndex(p => p.Status);
            modelBuilder.Entity<Package>()
                .HasIndex(p => p.UploadedBy);
            modelBuilder.Entity<Package>()
                .HasIndex(p => p.Sha256Hash);
            modelBuilder.Entity<Package>()
                .HasIndex(p => p.ProductCode);

            // AuditLog indexes
            modelBuilder.Entity<AuditLog>()
                .HasIndex(a => a.Timestamp);
            modelBuilder.Entity<AuditLog>()
                .HasIndex(a => a.UserIdentity);
            modelBuilder.Entity<AuditLog>()
                .HasIndex(a => a.PackageId);

            // DeploymentHistory indexes
            modelBuilder.Entity<DeploymentHistory>()
                .HasIndex(d => d.TriggeredAt);
            modelBuilder.Entity<DeploymentHistory>()
                .HasIndex(d => d.Result);

            // Seed repository apps matching deploy.json entries
            modelBuilder.Entity<RepositoryApp>().HasData(
                new RepositoryApp
                {
                    Id = 1,
                    AppName = "7-Zip",
                    ProductCode = "{23170F69-40C1-2702-2601-000001000000}",
                    TrustedSubject = "CN=Package_Developers",
                    TrustedIssuerKeyword = "scaffold-DC-CA",
                    InstallDir = @"C:\Program Files\7-Zip",
                    VerifyFile = "7z.exe",
                    DisplayNameMatch = "7-Zip",
                    IsActive = true,
                    CreatedAt = new DateTime(2026, 1, 1),
                    CreatedBy = "SCAFFOLD\\Administrator"
                },
                new RepositoryApp
                {
                    Id = 2,
                    AppName = "PuTTY",
                    ProductCode = "{ED41CD4E-33BB-400C-AB20-B09388DC83EF}",
                    TrustedSubject = "CN=Package_Developers",
                    TrustedIssuerKeyword = "scaffold-DC-CA",
                    InstallDir = @"C:\Program Files\PuTTY",
                    VerifyFile = "plink.exe",
                    VerifyCommand = "-V",
                    DisplayNameMatch = "PuTTY",
                    IsActive = true,
                    CreatedAt = new DateTime(2026, 1, 1),
                    CreatedBy = "SCAFFOLD\\Administrator"
                }
            );
        }
    }
}
