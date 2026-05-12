using Middleware.DTO;

namespace Middleware.Clients;

public interface IBookingApiClient
{
    Task<List<TimeSlotWithDate>> GetFreeSlots(int masterId, DateOnly date);

    Task<List<TimeSlotWithDate>> GetFreeSlots(int masterId, DateOnly startDate, DateOnly endDate);

    Task<List<TimeSlotWithDate>> GetBookedSlots(int masterId, DateOnly startDate, DateOnly endDate);
    
    Task<BookingResponse> BookSlot(BookingCreateRequest request);
    
    Task<BookingCancelResponse> CancelBookSlot(int clientId, int masterId, DateTime bookingDate);
}