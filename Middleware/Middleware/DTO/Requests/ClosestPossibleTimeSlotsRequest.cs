using System.ComponentModel.DataAnnotations;

namespace Middleware.DTO.Requests;

public class ClosestPossibleTimeSlotsRequest
{
    /// <summary>Id мастера</summary>
    public int MasterId { get; set; }

    /// <summary>Id услуги</summary>
    public int ServiceId { get; set; }
    
    /// <summary>Временной промежуток в котором нужно искать свободное место для услуги</summary>
    public TimeSlot timeSlot { get; set; }
    
    /// <summary>Дата с которой начинать поиск</summary>
    public DateOnly StartDate { get; set; }
    /// <summary>Дата на которой закончится поиск</summary>
    public DateOnly EndDate { get; set; }
    /// <summary>Временной буфер до начало услуги</summary>
    public TimeSpan PreBuffer { get; set; }
    /// <summary>Временной буфер после завершения услуги</summary>
    public TimeSpan PostBuffer { get; set; }
    /// <summary>Шаг по времени</summary>
    public TimeSpan GranularTimeStep { get; set; }
    
}