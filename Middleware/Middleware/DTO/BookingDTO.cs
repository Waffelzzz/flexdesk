
using System.Text.Json.Serialization;
namespace Middleware.DTO;


#region Slot Generate

public class SlotGenerateRequest
{
    public int MasterId { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }
}

public class SlotGenerateResponse
{
    public int MasterId { get; set; }
    public int OrganizationId { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public int SlotsCreated { get; set; }
    public string Message { get; set; } = string.Empty;
}

#endregion

#region Slot

public class SlotResponse
{
    public int BookingId { get; set; }
    public int MasterId { get; set; }
    public DateTime BookingDt { get; set; }
    public string Status { get; set; } = string.Empty;
}

public class SlotFreeRequest
{
    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }
}

public class SlotInterval
{
    [JsonPropertyName("from")]
    public DateTime From { get; set; }

    public DateTime To { get; set; }
}

public class SlotFreeResponse
{
    public int MasterId { get; set; }
    public int? OrganizationId { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }
    public List<SlotResponse> Slots { get; set; } = new();
    public int Total { get; set; }
}

#endregion

#region Generate For All

public class GenerateSlotsForAllRequest
{
    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }
}

public class GenerateSlotsForAllResponse
{
    public int OrganizationId { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public int TotalMasters { get; set; }
    public int SlotsCreated { get; set; }
    public List<string>? Errors { get; set; }
    public string Message { get; set; } = string.Empty;
}

public class MasterSlotError
{
    public int MasterId { get; set; }
    public string Error { get; set; } = string.Empty;
}

#endregion

#region Generate For Masters

public class GenerateSlotsForMastersRequest
{
    public List<int> MasterIds { get; set; } = new();
    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }
}

#endregion

#region Booking

public class BookingCreateRequest
{
    [JsonPropertyName("service_master_id")]
    public int ServiceMasterId { get; set; }
    [JsonPropertyName("client_id")]
    public int ClientId { get; set; }
    [JsonPropertyName("booking_dt")]
    public DateTime BookingDt { get; set; }
    [JsonPropertyName("duration_minutes")]
    public int DurationMinutes { get; set; }
}

public class BookedSlotInfo
{
    [JsonPropertyName("booking_id")]
    public int BookingId { get; set; }
    [JsonPropertyName("booking_dt")]
    public DateTime BookingDt { get; set; }
}

public class BookingResponse
{
    [JsonPropertyName("booking_id")]
    public int BookingId { get; set; }
    [JsonPropertyName("client_id")]
    public int ClientId { get; set; }
    [JsonPropertyName("service_master_id")]
    public int ServiceMasterId { get; set; }
    [JsonPropertyName("master_id")]
    public int MasterId { get; set; }
    [JsonPropertyName("booking_dt")]
    public DateTime BookingDt { get; set; }
    [JsonPropertyName("duration_minutes")]
    public int DurationMinutes { get; set; }
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;
    [JsonPropertyName("organization_id")]
    public int OrganizationId { get; set; }
    [JsonPropertyName("booked_slots")]
    public List<BookedSlotInfo> BookedSlots { get; set; } = new();
}

public class BookingCancelResponse
{
    [JsonPropertyName("master_id")]
    int MasterId { get; set; }
    [JsonPropertyName("client_id")]
    int ClientId { get; set; }
    [JsonPropertyName("booking_dt")]
    DateTime BookingDt { get; set; }
    [JsonPropertyName("released_slots")]
    int releasedSlots { get; set; }
    [JsonPropertyName("status")]
    string Status { get; set; } = string.Empty;
}

#endregion

#region Booked Intervals

public class BookedSlotInterval
{
    [JsonPropertyName("from")]
    public DateTime From { get; set; }

    [JsonPropertyName("to")]
    public DateTime To { get; set; }
}

public class BookedSlotsIntervalsResponse
{
    [JsonPropertyName("master_id")]
    public int MasterId { get; set; }

    [JsonPropertyName("organization_id")]
    public int? OrganizationId { get; set; }

    [JsonPropertyName("start_date")]
    public DateTime StartDate { get; set; }

    [JsonPropertyName("end_date")]
    public DateTime EndDate { get; set; }

    [JsonPropertyName("intervals")]
    public List<BookedSlotInterval> Intervals { get; set; } = new();

    [JsonPropertyName("total_intervals")]
    public int TotalIntervals { get; set; }

    [JsonPropertyName("total_minutes")]
    public int TotalMinutes { get; set; }
}
#endregion