namespace ScaffoldPortal.Middleware
{
    /// <summary>
    /// Logs every authenticated HTTP request to the application log.
    /// Helps correlate web activity with audit records.
    /// Security: captures identity, path, and method — NOT request bodies.
    /// </summary>
    public class AuditRequestMiddleware
    {
        private readonly RequestDelegate _next;
        private readonly ILogger<AuditRequestMiddleware> _log;

        public AuditRequestMiddleware(RequestDelegate next, ILogger<AuditRequestMiddleware> log)
        {
            _next = next; _log = log;
        }

        public async Task InvokeAsync(HttpContext ctx)
        {
            if (ctx.User.Identity?.IsAuthenticated == true)
            {
                var user = ctx.User.Identity.Name ?? "unknown";
                var path = ctx.Request.Path.Value ?? "";
                var method = ctx.Request.Method;

                // Only log mutating or sensitive paths to avoid noise
                if (method != "GET" || path.Contains("/Package/") || path.Contains("/Validation/"))
                {
                    _log.LogInformation("[REQUEST] User={User} Method={Method} Path={Path} IP={IP}",
                        user, method, path,
                        ctx.Connection.RemoteIpAddress?.ToString() ?? "unknown");
                }
            }

            await _next(ctx);
        }
    }
}
