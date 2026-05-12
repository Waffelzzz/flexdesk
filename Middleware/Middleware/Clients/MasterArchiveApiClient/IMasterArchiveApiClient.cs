namespace Middleware.Clients.ClientArchiveApiClient;

public interface IMasterArchiveApiClient
{
    Task<string> MasterArchiveInsert(int masterId, 
        int organizationId, DateTime date,decimal releasedHours, int releasedAmount,
        int cheatsHours, int bookingCount);
    
}