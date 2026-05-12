namespace Middleware.DTO.Requests;
/// <summary>
/// Аргументы /possible-time-slots
/// </summary>
public class PossibleTimeSlotsRequest
{
    /// <summary>Id мастера</summary>
    public int MasterId { get; set; }

    /// <summary>Id услуги</summary>
    public int ServiceId { get; set; }

    /// <summary>Нужная дата</summary>
    public DateOnly Date { get; set; }

    /// <summary>Шаг по времени</summary>
    public TimeSpan GranularTimeStep { get; set; }
}