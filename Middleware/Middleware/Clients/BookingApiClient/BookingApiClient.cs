
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Middleware.DTO;

namespace Middleware.Clients;

public class BookingApiClient : IBookingApiClient
{
    private readonly HttpClient _http;
    private readonly IHttpContextAccessor _httpContextAccessor;
    
    public BookingApiClient(HttpClient http, IHttpContextAccessor httpContextAccessor)
    {
        _http = http;
        _httpContextAccessor = httpContextAccessor;
    }
    
    
    public async Task<List<TimeSlotWithDate>> GetFreeSlots(int masterId, DateOnly date)
    {
        return await GetFreeSlots(masterId, date, date);   
    }
    

    public async Task<List<TimeSlotWithDate>> GetFreeSlots(int masterId, DateOnly startDate, DateOnly endDate)
    {
        var json = JsonSerializer.Serialize(new
        {
            start_date = startDate.ToString("yyyy-MM-dd"),
            end_date = endDate.ToString("yyyy-MM-dd")
        });
        
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _http.PostAsync(
            $"/v1/booking/masters/{masterId}/free-slots-intervals",
            content);
        
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Booking API error: {response.StatusCode} - {error}");
        }
        var raw = await response.Content.ReadAsStringAsync();
        
        var data = await response.Content.ReadFromJsonAsync<BookedSlotsIntervalsResponse>();
        
        List<TimeSlotWithDate> slots = new List<TimeSlotWithDate>();
        foreach (var slot in data.Intervals)
        {
            slots.Add(new TimeSlotWithDate(slot.From, slot.To));
        }
        return slots;
    }

    public async Task<List<TimeSlotWithDate>> GetBookedSlots(int masterId, DateOnly startDate, DateOnly endDate)
    {
        var json = JsonSerializer.Serialize(new
        {
            start_date = startDate.ToString("yyyy-MM-dd"),
            end_date = endDate.ToString("yyyy-MM-dd")
        });
        
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _http.PostAsync(
            $"/v1/booking/masters/{masterId}/booked-slots-intervals",
            content);
        
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Booking API error: {response.StatusCode} - {error}");
        }
        var raw = await response.Content.ReadAsStringAsync();
        
        var data = await response.Content.ReadFromJsonAsync<BookedSlotsIntervalsResponse>();
        
        List<TimeSlotWithDate> slots = new List<TimeSlotWithDate>();
        foreach (var slot in data.Intervals)
        {
            slots.Add(new TimeSlotWithDate(slot.From, slot.To));
        }
        return slots;
    }

    public async Task<BookingResponse> BookSlot(BookingCreateRequest request)
    {
        var json = JsonSerializer.Serialize(request);
        
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _http.PostAsync(
            $"/v1/booking/book",
            content);
        
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Booking API error: {response.StatusCode} - {error}");
        }
        
        var data = await response.Content.ReadFromJsonAsync<BookingResponse>();
        
        return data;
    }
    public async Task<BookingCancelResponse> CancelBookSlot(int clientId, int masterId, DateTime bookingDate)
    {
        var json = JsonSerializer.Serialize(new
        {
            client_id = clientId,
            booking_dt = bookingDate.ToString("yyyy-MM-dd HH:mm:ss"),
        });
        
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _http.PostAsync(
            $"/v1/booking/masters/{masterId}/cancel-booking",
            content);
        
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync();
            throw new Exception($"Booking API error: {response.StatusCode} - {error}");
        }
        
        var data = await response.Content.ReadFromJsonAsync<BookingCancelResponse>();
        
        return data;
    }
}