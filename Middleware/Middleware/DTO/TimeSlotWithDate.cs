namespace Middleware.DTO;

public class TimeSlotWithDate
{
    /// <summary>Начало временного окна (формат: 2026-03-15T10:00:00Z)</summary>
    public DateTime Start { get; set; }
    /// <summary>Конец временного окна (формат: 2026-03-15T11:00:00Z)</summary>
    public DateTime End { get; set; }

    public TimeSlotWithDate(DateTime start, DateTime end)
    {
        Start = start;
        End = end;
    }
    
    public TimeSlotWithDate(TimeSlot timeSlot, DateOnly date)
    {
        Start = date.ToDateTime(timeSlot.Start);
        End = date.ToDateTime(timeSlot.End);
    }
}