using System.Text;
using System.Text.Json;
using Middleware.DTO;

namespace Middleware.Clients.ClientArchiveApiClient;

public class ClientArchiveApiClient: IClientArchiveApiClient
{
    private readonly HttpClient _http;
    private readonly IHttpContextAccessor _httpContextAccessor;
    
    public ClientArchiveApiClient(HttpClient http, IHttpContextAccessor httpContextAccessor)
    {
        _http = http;
        _httpContextAccessor = httpContextAccessor;
    }
    
    public async Task<string> ClientArchiveInsert(int clientId, int serviceMasterId,
        int organizationId, DateTime startTime, DateTime endTime)
    {
        var json = JsonSerializer.Serialize(new
        {
            service_master_id = serviceMasterId,
            visit_start_dt = startTime.ToString("yyyy-MM-dd HH:mm:ss"),
            visit_end_dt = endTime.ToString("yyyy-MM-dd HH:mm:ss"),
            organization_id = organizationId,
        });
        
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _http.PostAsync(
            $"/v1/client-archive/{clientId}/insert",
            content);

        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"ClientArchive API error: {response.StatusCode} - {error}");
        }
        
        
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> ClientArchiveDelete(int clientId)
    {
        var response = await _http.DeleteAsync($"/v1/client-archive/{clientId}/delete");
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"ClientArchive API error: {response.StatusCode} - {error}");
        }
        return await response.Content.ReadAsStringAsync();
    }
}