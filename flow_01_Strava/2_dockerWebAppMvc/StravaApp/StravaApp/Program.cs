using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Serilog;
using StravaAuth.Data;
using Serilog;

Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .WriteTo.Console()                          // aussi visible dans docker logs
    .WriteTo.File(
        path: "/app/logs/strava-.log",
        rollingInterval: RollingInterval.Day,   // un fichier par jour
        retainedFileCountLimit: 7               // garde 7 jours de logs
    )
    .CreateLogger();

var builder = WebApplication.CreateBuilder(args);

builder.Host.UseSerilog();

// Enregistrement des services
builder.Services.AddControllersWithViews();
builder.Services.AddHttpClient();                          // HttpClient via factory
builder.Services.AddScoped<StravaTokenRepository>();       // Repository injecté
builder.Services.AddSession();                             // Session activée

var app = builder.Build();

if (!app.Environment.IsDevelopment())
    app.UseExceptionHandler("/Home/Error");

app.UseStaticFiles();
app.UseRouting();
app.UseSession();                                          // Session middleware

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();