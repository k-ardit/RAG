//using System;
//using System.Collections.Generic;
//using System.Linq;
//using System.Web;

//namespace Strava2.Models
//{
//    public class StravaToken
//    {
//    }
//}


using System;

namespace StravaAuth.Models
{
    public class StravaToken
    {
        public int Id { get; set; }
        public int IdEmploye { get; set; }
        public long AthleteId { get; set; }
        public string AccessToken { get; set; }
        public string RefreshToken { get; set; }
        public long ExpiresAt { get; set; }
        public string Scope { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }

        public DateTime ExpiresAtUtc => DateTimeOffset.FromUnixTimeSeconds(ExpiresAt).UtcDateTime;
        public bool IsExpired => DateTimeOffset.UtcNow.ToUnixTimeSeconds() >= ExpiresAt - 60;
    }
}
