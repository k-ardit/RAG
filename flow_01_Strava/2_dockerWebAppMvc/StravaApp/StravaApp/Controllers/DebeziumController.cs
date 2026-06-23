using Microsoft.AspNetCore.Mvc;
using System.Text.Json.Nodes;

[ApiController]
[Route("api/debezium")]
public class DebeziumController : ControllerBase
{
    private readonly ILogger<DebeziumController> _logger;

    public DebeziumController(ILogger<DebeziumController> logger)
    {
        _logger = logger;
    }

    [HttpPost("events")]
    public async Task<IActionResult> ReceiveEvent()
    {
        using StreamReader reader = new StreamReader(Request.Body);
        string body = await reader.ReadToEndAsync();

        // ✅ Logger le body brut pour voir la structure exacte
        _logger.LogInformation("[Debezium] Body brut : {Body}", body);

        try
        {
            JsonNode evt = JsonNode.Parse(body);
            string op = (string)evt["payload"]?["op"];
            string table = (string)evt["payload"]?["source"]?["table"];
            _logger.LogInformation("[Debezium] {Table} → {Op}", table, op);
        }
        catch (Exception ex)
        {
            _logger.LogError("[Debezium] Erreur parsing : {Error}", ex.Message);
        }

        return Ok();
    }
}