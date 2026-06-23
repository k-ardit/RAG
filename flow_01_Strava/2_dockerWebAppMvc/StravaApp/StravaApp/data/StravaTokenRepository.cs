using Microsoft.Data.SqlClient;          // ✅ Microsoft.Data.SqlClient (plus System.Data.SqlClient)
using Microsoft.Extensions.Configuration; // ✅ IConfiguration (plus ConfigurationManager)
using StravaAuth.Models;
using System;
using System.Data;

namespace StravaAuth.Data
{
    public class StravaTokenRepository
    {
        private readonly string _connectionString;

        // IConfiguration injecté via le constructeur (injection de dépendances)
        public StravaTokenRepository(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("StravaDb");
        }

        public void SaveToken(StravaToken token)
        {
            string sql = @"
                MERGE StravaTokens AS cible
                USING (SELECT @AthleteId AS AthleteId) AS source
                    ON cible.AthleteId = source.AthleteId
                WHEN MATCHED THEN
                    UPDATE SET
                        AccessToken  = @AccessToken,
                        RefreshToken = @RefreshToken,
                        ExpiresAt    = @ExpiresAt,
                        Scope        = @Scope,
                        UpdatedAt    = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (IdEmploye, AthleteId, AccessToken, RefreshToken, ExpiresAt, Scope)
                    VALUES (@IdEmploye, @AthleteId, @AccessToken, @RefreshToken, @ExpiresAt, @Scope);";

            using SqlConnection conn = new SqlConnection(_connectionString);
            using SqlCommand cmd = new SqlCommand(sql, conn);

            cmd.Parameters.Add("@IdEmploye", SqlDbType.Int).Value = token.IdEmploye;
            cmd.Parameters.Add("@AthleteId", SqlDbType.BigInt).Value = token.AthleteId;
            cmd.Parameters.Add("@AccessToken", SqlDbType.NVarChar, 255).Value = token.AccessToken;
            cmd.Parameters.Add("@RefreshToken", SqlDbType.NVarChar, 255).Value = token.RefreshToken;
            cmd.Parameters.Add("@ExpiresAt", SqlDbType.BigInt).Value = token.ExpiresAt;
            cmd.Parameters.Add("@Scope", SqlDbType.NVarChar, 255).Value = (object)token.Scope ?? DBNull.Value;

            conn.Open();
            cmd.ExecuteNonQuery();
        }

        public StravaToken GetByAthleteId(long athleteId)
        {
            string sql = @"
                SELECT Id, AthleteId, AccessToken, RefreshToken, ExpiresAt, Scope, CreatedAt, UpdatedAt
                FROM StravaTokens
                WHERE AthleteId = @AthleteId";

            using SqlConnection conn = new SqlConnection(_connectionString);
            using SqlCommand cmd = new SqlCommand(sql, conn);

            cmd.Parameters.Add("@AthleteId", SqlDbType.BigInt).Value = athleteId;

            conn.Open();
            using SqlDataReader reader = cmd.ExecuteReader();

            if (!reader.Read())
                return null;

            return MapReader(reader);
        }

        public void UpdateTokens(long athleteId, string newAccessToken, string newRefreshToken, long newExpiresAt)
        {
            string sql = @"
                UPDATE StravaTokens
                SET AccessToken  = @AccessToken,
                    RefreshToken = @RefreshToken,
                    ExpiresAt    = @ExpiresAt,
                    UpdatedAt    = GETDATE()
                WHERE AthleteId = @AthleteId";

            using SqlConnection conn = new SqlConnection(_connectionString);
            using SqlCommand cmd = new SqlCommand(sql, conn);

            cmd.Parameters.Add("@AthleteId", SqlDbType.BigInt).Value = athleteId;
            cmd.Parameters.Add("@AccessToken", SqlDbType.NVarChar, 255).Value = newAccessToken;
            cmd.Parameters.Add("@RefreshToken", SqlDbType.NVarChar, 255).Value = newRefreshToken;
            cmd.Parameters.Add("@ExpiresAt", SqlDbType.BigInt).Value = newExpiresAt;

            conn.Open();
            cmd.ExecuteNonQuery();
        }

        public void DeleteByAthleteId(long athleteId)
        {
            string sql = "DELETE FROM StravaTokens WHERE AthleteId = @AthleteId";

            using SqlConnection conn = new SqlConnection(_connectionString);
            using SqlCommand cmd = new SqlCommand(sql, conn);

            cmd.Parameters.Add("@AthleteId", SqlDbType.BigInt).Value = athleteId;
            conn.Open();
            cmd.ExecuteNonQuery();
        }

        private StravaToken MapReader(SqlDataReader reader)
        {
            return new StravaToken
            {
                Id = (int)reader["Id"],
                AthleteId = (long)reader["AthleteId"],
                AccessToken = reader["AccessToken"].ToString(),
                RefreshToken = reader["RefreshToken"].ToString(),
                ExpiresAt = (long)reader["ExpiresAt"],
                Scope = reader["Scope"] == DBNull.Value ? null : reader["Scope"].ToString(),
                CreatedAt = (DateTime)reader["CreatedAt"],
                UpdatedAt = (DateTime)reader["UpdatedAt"]
            };
        }
    }
}
