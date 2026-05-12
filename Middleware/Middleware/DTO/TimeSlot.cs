namespace Middleware.DTO;

public class TimeSlot
{
    /// <summary>Начало временного окна (формат: 2026-03-15T10:00:00Z)</summary>
    public TimeOnly Start { get; set; }
    /// <summary>Конец временного окна (формат: 2026-03-15T11:00:00Z)</summary>
    public TimeOnly End { get; set; }

    public TimeSlot(TimeOnly start, TimeOnly end)
    {
        Start = start;
        End = end;
    }
}