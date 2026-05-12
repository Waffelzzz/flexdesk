namespace Middleware.DTO.Requests;

public class DayTimelineRequest
{
    public int MasterId { get; set; }
    public DateOnly Date { get; set; }
    public TimeSpan GranularTimeStep { get; set; } = TimeSpan.FromMinutes(5);

    public TimeSpan PreBuffer { get; set; } = TimeSpan.Zero;
    public TimeSpan PostBuffer { get; set; } = TimeSpan.Zero;
}