using System.Text;
using CamPro.Web.Data;
using CamPro.Web.Models;
using CamPro.Web.Options;

var builder = WebApplication.CreateBuilder(args);
builder.Services.Configure<DatabaseOptions>(builder.Configuration.GetSection(DatabaseOptions.SectionName));
builder.Services.AddSingleton<MySqlConnectionFactory>();
builder.Services.AddSingleton<DatabaseInitializer>();
builder.Services.AddScoped<StoreRepository>();
builder.Services.AddDistributedMemoryCache();
builder.Services.AddSession(options =>
{
    options.Cookie.Name = ".CamPro.Session";
    options.Cookie.HttpOnly = true;
    options.Cookie.IsEssential = true;
    options.Cookie.SameSite = SameSiteMode.Lax;
    options.IdleTimeout = TimeSpan.FromMinutes(30);
});
builder.Services.ConfigureHttpJsonOptions(options =>
    options.SerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase);

var app = builder.Build();
var demoMode = builder.Configuration.GetValue<bool>("CamPro:DemoMode");
app.UseExceptionHandler(errorApp => errorApp.Run(async context =>
{
    context.Response.StatusCode = StatusCodes.Status500InternalServerError;
    await Results.Problem("Có lỗi khi xử lý dữ liệu. Hãy kiểm tra MySQL trong XAMPP.", statusCode: 500).ExecuteAsync(context);
}));
app.UseDefaultFiles();
app.UseStaticFiles();
app.UseSession();

if (!demoMode) await app.Services.GetRequiredService<DatabaseInitializer>().InitializeAsync(app.Lifetime.ApplicationStopping); else app.Logger.LogWarning("CAMPRO demo mode: MySQL disabled.");

var api = app.MapGroup("/api");
api.MapGet("/health", async (StoreRepository repository, CancellationToken ct) => demoMode ? Results.Ok(new { status = "ok", mode = "demo", serverTime = DateTimeOffset.Now }) : (await repository.PingAsync(ct) ? Results.Ok(new { status = "ok", database = "campro_csharp", serverTime = DateTimeOffset.Now }) : Results.Problem("Không kết nối được MySQL.")));

api.MapGet("/state", async (HttpContext context, StoreRepository repository, CancellationToken ct) =>
{
    var userIdText = context.Session.GetString("userId");
    return Results.Ok(await repository.GetStateAsync(long.TryParse(userIdText, out var id) ? id : null, ct));
});

api.MapPost("/state/sync", async (HttpContext context, StoreState state, StoreRepository repository, CancellationToken ct) =>
{
    var userIdText = context.Session.GetString("userId");
    await repository.SyncAsync(state, long.TryParse(userIdText, out var id) ? id : null, ct);
    return Results.Ok(new { saved = true, savedAt = DateTimeOffset.Now });
});

api.MapPost("/auth/login", async (HttpContext context, LoginRequest request, StoreRepository repository, CancellationToken ct) =>
{
    var user = demoMode ? ((request.Email.Trim().ToLowerInvariant(), request.Password) switch { ("admin@campro.vn", "Admin@123") => new CustomerDto { Id=1, Name="Quản trị CAMPRO", Email="admin@campro.vn", Active=true, Role="admin" }, ("minhanh@example.com", "123456") => new CustomerDto { Id=2, Name="Nguyễn Minh Anh", Email="minhanh@example.com", Active=true, Role="customer" }, _ => null }) : await repository.LoginAsync(request.Email, request.Password, ct);
    if (user is null) return Results.BadRequest(new { message = "Email hoặc mật khẩu không đúng, hoặc tài khoản đã bị khóa." });
    context.Session.SetString("userId", user.Id.ToString());
    context.Session.SetString("role", user.Role);
    return Results.Ok(user);
});

api.MapPost("/auth/register", async (HttpContext context, RegisterRequest request, StoreRepository repository, CancellationToken ct) =>
{
    var result = await repository.RegisterAsync(request, ct);
    if (result.User is null) return Results.BadRequest(new { message = result.Error });
    context.Session.SetString("userId", result.User.Id.ToString());
    context.Session.SetString("role", result.User.Role);
    return Results.Ok(result.User);
});

api.MapPost("/auth/logout", (HttpContext context) =>
{
    context.Session.Clear();
    return Results.Ok(new { loggedOut = true });
});

api.MapPost("/auth/change-password", async (HttpContext context, ChangePasswordRequest request, StoreRepository repository, CancellationToken ct) =>
{
    if (!long.TryParse(context.Session.GetString("userId"), out var id)) return Results.Unauthorized();
    return await repository.ChangePasswordAsync(id, request.CurrentPassword, request.NewPassword, ct)
        ? Results.Ok(new { changed = true })
        : Results.BadRequest(new { message = "Mật khẩu hiện tại không đúng hoặc mật khẩu mới chưa hợp lệ." });
});

api.MapGet("/admin/report.csv", async (HttpContext context, StoreRepository repository, CancellationToken ct) =>
{
    if (!string.Equals(context.Session.GetString("role"), "admin", StringComparison.Ordinal)) return Results.Unauthorized();
    var state = await repository.GetStateAsync(null, ct);
    var csv = new StringBuilder("\uFEFFMã đơn,Khách hàng,Ngày đặt,Trạng thái,Tổng tiền\r\n");
    foreach (var order in state.Orders)
    {
        static string Cell(object? value) => $"\"{Convert.ToString(value)?.Replace("\"", "\"\"")}\"";
        csv.AppendJoin(',', Cell(order.Id), Cell(order.Customer), Cell(order.Date), Cell(order.Status), Cell(order.Total)).Append("\r\n");
    }
    return Results.File(Encoding.UTF8.GetBytes(csv.ToString()), "text/csv; charset=utf-8", "CAMPRO-doanh-thu.csv");
});

app.MapFallbackToFile("index.html");
app.Run();

public partial class Program;
