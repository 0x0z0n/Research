using Microsoft.AspNetCore.Authentication.Negotiate;
using Microsoft.EntityFrameworkCore;
using ScaffoldPortal.Data;
using ScaffoldPortal.Services;
using ScaffoldPortal.Middleware;
using Serilog;
using Serilog.Events;

// ── Bootstrap Serilog early so startup errors are captured ──────────────────
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .WriteTo.Console()
    .WriteTo.File(
        path: @"C:\Software\Logs\Validator\ScaffoldPortal_.log",
        rollingInterval: RollingInterval.Day,
        outputTemplate: "[{Timestamp:yyyy-MM-dd HH:mm:ss.fff}] [{Level:u7}] [{SourceContext}] {Message:lj}{NewLine}{Exception}")
    .CreateBootstrapLogger();

try
{
    Log.Information("[PORTAL] Scaffold MSI Deployment Portal starting.");

    var builder = WebApplication.CreateBuilder(args);

    // ── Serilog full configuration (reads appsettings) ───────────────────────
    builder.Host.UseSerilog((ctx, services, cfg) => cfg
        .ReadFrom.Configuration(ctx.Configuration)
        .ReadFrom.Services(services)
        .Enrich.FromLogContext()
        .Enrich.WithMachineName());

    // ── Entity Framework / SQL Server ────────────────────────────────────────
    builder.Services.AddDbContext<ScaffoldDbContext>(options =>
        options.UseSqlServer(
            builder.Configuration.GetConnectionString("DefaultConnection"),
            sql => sql.EnableRetryOnFailure(3)));

    // ── Windows Authentication (Kerberos / NTLM) ─────────────────────────────
    // Security: Negotiate is the preferred scheme for Windows domain environments.
    // Falls back to NTLM when Kerberos tickets are unavailable.
    builder.Services.AddAuthentication(NegotiateDefaults.AuthenticationScheme)
        .AddNegotiate();

    // ── Authorization Policies mapped to AD groups ────────────────────────────
    builder.Services.AddAuthorization(options =>
    {
        options.AddPolicy("PackageDeveloper", policy =>
            policy.RequireRole(@"SCAFFOLD\Package_Developers"));

        options.AddPolicy("PackageValidator", policy =>
            policy.RequireRole(@"SCAFFOLD\Package_Validators"));

        options.AddPolicy("DeploymentAdmin", policy =>
            policy.RequireRole(@"SCAFFOLD\Deployment_Admins"));

        // Validators and Admins can both access validation queue
        options.AddPolicy("ValidatorOrAdmin", policy =>
            policy.RequireRole(
                @"SCAFFOLD\Package_Validators",
                @"SCAFFOLD\Deployment_Admins"));

        // Any authenticated domain user can view dashboard
        options.FallbackPolicy = options.DefaultPolicy;
    });

    // ── MVC with anti-forgery ─────────────────────────────────────────────────
    builder.Services.AddControllersWithViews(options =>
    {
        // Security: require anti-forgery token on all POST actions globally
        options.Filters.Add(new Microsoft.AspNetCore.Mvc.AutoValidateAntiforgeryTokenAttribute());
    });

    // ── Application Services ──────────────────────────────────────────────────
    builder.Services.AddScoped<IPackageService, PackageService>();
    builder.Services.AddScoped<IValidationService, ValidationService>();
    builder.Services.AddScoped<IAuditService, AuditService>();
    builder.Services.AddScoped<IDeploymentService, DeploymentService>();
    builder.Services.AddScoped<IMsiMetadataService, MsiMetadataService>();
    builder.Services.AddScoped<IFileStorageService, FileStorageService>();

    // ── HTTP context accessor for audit logging ───────────────────────────────
    builder.Services.AddHttpContextAccessor();

    // ── Response compression for dashboard data ───────────────────────────────
    builder.Services.AddResponseCompression();

    var app = builder.Build();

    // ── Middleware pipeline ───────────────────────────────────────────────────
    if (!app.Environment.IsDevelopment())
    {
        app.UseExceptionHandler("/Home/Error");
        app.UseHsts();
    }

    app.UseHttpsRedirection();
    app.UseStaticFiles();
    app.UseSerilogRequestLogging();
    app.UseRouting();

    // Security: Authentication must precede Authorization
    app.UseAuthentication();
    app.UseAuthorization();

    // Custom middleware: logs authenticated user on every request for audit trail
    app.UseMiddleware<AuditRequestMiddleware>();

    app.MapControllerRoute(
        name: "default",
        pattern: "{controller=Home}/{action=Index}/{id?}");

    // ── Ensure DB and seed lookup data on first run ───────────────────────────
//    using (var scope = app.Services.CreateScope())
//    {
//        var db = scope.ServiceProvider.GetRequiredService<ScaffoldDbContext>();
//        db.Database.EnsureCreated();
//    }

    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "[PORTAL] Scaffold Portal terminated unexpectedly.");
}
finally
{
    Log.CloseAndFlush();
}
