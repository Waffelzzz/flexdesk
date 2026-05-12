using System.Runtime.InteropServices.ComTypes;
using Middleware.DTO;

namespace Middleware.Clients;

public class MasterApiClient: IMasterApiClient
{
    private readonly HttpClient _http;
    private readonly IHttpContextAccessor _httpContextAccessor;
    
    public MasterApiClient(HttpClient http, IHttpContextAccessor httpContextAccessor)
    {
        _http = http;
        _httpContextAccessor = httpContextAccessor;
    }
    
    public async Task<List<int>> GetMastersIds(int organizationId)
    {
        var response = await _http.GetAsync(
            $"/v1/masters/of_org/{organizationId}");

        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Booking API error: {response.StatusCode} - {error}");
        }

        var data = await response.Content.ReadFromJsonAsync<List<MasterOut>>();
        
        List<int> masterIds = new List<int>();
        foreach (var master in data) masterIds.Add(master.MasterId);
        return masterIds;
    }

    public async Task<TimeSlotWithDate> GetMastersWorkDay(int masterId, DateOnly date)
    {
        var response = await _http.GetAsync(
            $"/v1/masters/{masterId}/workday/{date.ToString("yyyy-MM-dd")}");

        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Booking API error: {response.StatusCode} - {error}");
        }

        var data = await response.Content.ReadFromJsonAsync<MasterWorkDayOut>();

        TimeSlotWithDate workDay = new TimeSlotWithDate(new TimeSlot(data.Slots[0].TimeFrom, data.Slots[data.Slots.Count-1].TimeTo), data.Date);
        
        return workDay;
    }

    
    public async Task<TimeSpan> GetMasterServiceDuration(int masterId, int serviceId)
    {
        List<ServiceMasterOut> data = await GetMasterService(masterId);
        
        TimeSpan duration = new TimeSpan();
        int? intDuration = data.Find((x) => x.ServiceId == serviceId).Duration;
        
        duration = TimeSpan.FromSeconds((double)intDuration);
        
        return duration;
    }

    public async Task<int> GetMasterServicePriceId(int masterId, int serviceMasterId)
    {
        List<ServiceMasterOut> data = await GetMasterService(masterId);
        int? Price = data.Find((x) => x.ServiceMasterId == serviceMasterId).Price;
        return (int)Price;
    }
    
    private async Task<List<ServiceMasterOut>> GetMasterService(int masterId)
    {
        var response = await _http.GetAsync(
            $"/v1/masters/{masterId}/service");

        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Booking API error: {response.StatusCode} - {error}");
        }

        var data = await response.Content.ReadFromJsonAsync<List<ServiceMasterOut>>();
        
        return data;
    }
    
}