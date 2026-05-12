using Middleware.DTO;

namespace Middleware.Clients;

public interface IMasterApiClient
{
    Task<List<int>> GetMastersIds(int organizationId);
    Task<TimeSlotWithDate> GetMastersWorkDay(int masterId, DateOnly date);
    Task<TimeSpan> GetMasterServiceDuration(int masterId, int serviceId);
    Task<int> GetMasterServicePriceId(int masterId, int serviceMasterId);
}