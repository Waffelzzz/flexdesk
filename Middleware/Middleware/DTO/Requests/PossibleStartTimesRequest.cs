using System.ComponentModel.DataAnnotations;

namespace Middleware.DTO.Requests;

/// <summary>
/// Аргументы /possible-start-times
/// </summary>
public class PossibleStartTimesRequest
{
    /// <summary>Временной промежуток в котором нужно искать свободное место для услуги</summary>
    public TimeSlot timeInterval { get; set; }

    /// <summary>
    /// Длительность слота (формат 00:30:00)
    /// </summary>
    [Range(typeof(TimeSpan), "00:01:00", "24:00:00")]
    public TimeSpan Duration { get; set; }

    /// <summary>
    /// Шаг по времени (формат 00:30:00)
    /// </summary>
    public TimeSpan GranularTimeStep { get; set; }
}