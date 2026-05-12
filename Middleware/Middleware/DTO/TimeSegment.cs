namespace Middleware.DTO;

public class TimeSegment
{
    public TimeStatus Status { get; set; }
    public TimeOnly Start { get; set; }
    public TimeOnly End { get; set; }
}