namespace Middleware.DTO;

public class TimeSegmentDTO
{
    public string Status { get; set; }
    public TimeOnly Start { get; set; }
    public TimeOnly End { get; set; }
}