namespace Middleware.DTO;
using System.Text.Json.Serialization;

public class MasterOut
{
    [JsonPropertyName("master_id")]
    public int MasterId { get; set; }

    [JsonPropertyName("organization_id")]
    public int OrganizationId { get; set; }

    [JsonPropertyName("account_id")]
    public int AccountId { get; set; }

    [JsonPropertyName("specialization")]
    public string? Specialization { get; set; }

    [JsonPropertyName("grade")]
    public string? Grade { get; set; }

    [JsonPropertyName("account")]
    public UserOut? Account { get; set; }
}

public class UserOut
{
    [JsonPropertyName("account_id")]
    public int AccountId { get; set; }

    [JsonPropertyName("login")]
    public string Login { get; set; } = string.Empty;

    [JsonPropertyName("first_name")]
    public string? FirstName { get; set; }

    [JsonPropertyName("last_name")]
    public string? LastName { get; set; }

    [JsonPropertyName("middle_name")]
    public string? MiddleName { get; set; }

    [JsonPropertyName("phone")]
    public string? Phone { get; set; }

    [JsonPropertyName("is_enable")]
    public bool IsEnable { get; set; }

    [JsonPropertyName("comments")]
    public string? Comments { get; set; }
}

public class WorkTimeSlot
{
    [JsonPropertyName("time_from")]
    public TimeOnly TimeFrom { get; set; }

    [JsonPropertyName("time_to")]
    public TimeOnly TimeTo { get; set; }
}
public class MasterWorkDayOut
{
    [JsonPropertyName("master_id")]
    public int MasterId { get; set; }

    [JsonPropertyName("date")]
    public DateOnly Date { get; set; }

    [JsonPropertyName("slots")]
    public List<WorkTimeSlot> Slots { get; set; } = new();

    [JsonPropertyName("is_working_day")]
    public bool IsWorkingDay { get; set; } = true;
}

public class ServiceMasterOut
{
    [JsonPropertyName("service_master_id")]
    public int ServiceMasterId { get; set; }

    [JsonPropertyName("service_id")]
    public int ServiceId { get; set; }

    [JsonPropertyName("master_id")]
    public int MasterId { get; set; }

    [JsonPropertyName("price")]
    public int? Price { get; set; }

    [JsonPropertyName("price_grp")]
    public int? PriceGrp { get; set; }

    [JsonPropertyName("day_start")]
    public DateOnly? DayStart { get; set; }

    [JsonPropertyName("day_finish")]
    public DateOnly? DayFinish { get; set; }

    [JsonPropertyName("is_enable")]
    public bool? IsEnable { get; set; } = true;

    [JsonPropertyName("duration")]
    public int? Duration { get; set; }

    [JsonPropertyName("organization_id")]
    public int OrganizationId { get; set; }
}