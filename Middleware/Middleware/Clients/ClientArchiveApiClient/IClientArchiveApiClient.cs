namespace Middleware.Clients.ClientArchiveApiClient;

public interface IClientArchiveApiClient
{
    Task<string> ClientArchiveInsert(int clientId,int serviceMasterId, 
        int organizationId, DateTime startTime, DateTime endTime);

    Task<string> ClientArchiveDelete(int clientId);
}