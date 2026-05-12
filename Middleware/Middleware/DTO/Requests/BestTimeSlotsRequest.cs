namespace Middleware.DTO.Requests;

public class BestTimeSlotsRequest
{
    public int MasterID { get; set; }
    public int ServiceID { get; set; }
    public DateOnly Date { get; set; }
    public TimeSpan GranularTimeStep { get; set; }
}