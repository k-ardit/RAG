using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using StravaAuth.Data;
using StravaAuth.Models;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

namespace StravaAuth.Controllers
{
    public class HomeController : Controller
    {
        private readonly string _clientId;
        private readonly string _clientSecret;
        private readonly StravaTokenRepository _repo;
        private readonly HttpClient _httpClient;

        // Injection de d�pendances via le constructeur
        public HomeController(IConfiguration configuration, StravaTokenRepository repo, IHttpClientFactory httpClientFactory)
        {
            _clientId = configuration["Strava:ClientId"];
            _clientSecret = configuration["Strava:ClientSecret"];
            _repo = repo;
            _httpClient = httpClientFactory.CreateClient();
        }

        public IActionResult Index()
        {
            return View();
        }

        // Callback OAuth Strava
        public async Task<IActionResult> Callback(string code, string state, string error)
        {
            if (!string.IsNullOrEmpty(error))
                return RedirectToAction("Index");

            if (string.IsNullOrEmpty(code))
                return BadRequest();

            if (!int.TryParse(state, out int idEmploye))
                return BadRequest("Parametre state (IdEmploye) manquant ou invalide.");

            JsonNode tokenData = await PostToStravaTokenAsync(new Dictionary<string, string>
            {
                ["client_id"] = _clientId,
                ["client_secret"] = _clientSecret,
                ["code"] = code,
                ["grant_type"] = "authorization_code"
            });

            if (tokenData == null)
                return Content("Erreur lors de l'echange du code.");

            _repo.SaveToken(new StravaToken
            {
                IdEmploye = idEmploye,
                AthleteId = (long)tokenData["athlete"]["id"],
                AccessToken = (string)tokenData["access_token"],
                RefreshToken = (string)tokenData["refresh_token"],
                ExpiresAt = (long)tokenData["expires_at"],
                Scope = Request.Query["scope"]
            });

            // Session ASP.NET Core
            HttpContext.Session.SetString("athlete_id", tokenData["athlete"]["id"].ToString());

            return RedirectToAction("Index");
        }

        // Rafraichit le token si expire
        public async Task<IActionResult> RefreshToken()
        {
            string athleteIdStr = HttpContext.Session.GetString("athlete_id");

            if (string.IsNullOrEmpty(athleteIdStr))
                return RedirectToAction("Callback");

            long athleteId = long.Parse(athleteIdStr);
            StravaToken token = _repo.GetByAthleteId(athleteId);

            if (token == null)
                return RedirectToAction("Callback");

            if (!token.IsExpired)
                return RedirectToAction("Index");

            JsonNode tokenData = await PostToStravaTokenAsync(new Dictionary<string, string>
            {
                ["client_id"] = _clientId,
                ["client_secret"] = _clientSecret,
                ["refresh_token"] = token.RefreshToken,
                ["grant_type"] = "refresh_token"
            });

            if (tokenData == null)
                return Content("Erreur lors du rafra�chissement.");

            _repo.UpdateTokens(
                athleteId,
                newAccessToken: (string)tokenData["access_token"],
                newRefreshToken: (string)tokenData["refresh_token"],
                newExpiresAt: (long)tokenData["expires_at"]
            );

            return RedirectToAction("Index");
        }

        // HttpClient async (plus HttpWebRequest synchrone)
        private async Task<JsonNode> PostToStravaTokenAsync(Dictionary<string, string> parameters)
        {
            using FormUrlEncodedContent content = new FormUrlEncodedContent(parameters);

            HttpResponseMessage response = await _httpClient.PostAsync(
                "https://www.strava.com/oauth/token", content);

            string json = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                System.Diagnostics.Debug.WriteLine($"Erreur Strava : {json}");
                return null;
            }

            return JsonNode.Parse(json);
        }
    }
}
