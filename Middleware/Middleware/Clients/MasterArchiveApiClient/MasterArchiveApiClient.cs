using System.Text;
using System.Text.Json;
using Middleware.DTO;

namespace Middleware.Clients.ClientArchiveApiClient;

public class MasterArchiveApiClient: IMasterArchiveApiClient
{
    private readonly HttpClient _http;
    private readonly IHttpContextAccessor _httpContextAccessor;
    
    public MasterArchiveApiClient(HttpClient http, IHttpContextAccessor httpContextAccessor)
    {
        _http = http;
        _httpContextAccessor = httpContextAccessor;
    }
    
    public async Task<string> MasterArchiveInsert(int masterId, 
        int organizationId, DateTime date, decimal releasedHours, int releasedAmount,
        int cheatsHours, int bookingCount)
    {
        var json = JsonSerializer.Serialize(new
        {
            work_day = date.ToString("yyyy-MM-dd"),
            organization_id = organizationId,
            released_hours = releasedHours,
            released_amount = releasedAmount,
            cheats_hours = cheatsHours,
            booking_count = bookingCount
        });
        
        Console.WriteLine(json);
        
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _http.PostAsync(
            $"/v1/master-archive/masters/{masterId}",
            content);

        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"MasterArchive API error: {response.StatusCode} - {error}");
        }
        
        
        return await response.Content.ReadAsStringAsync();
    }

    
}