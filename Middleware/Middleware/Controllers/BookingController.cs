using Microsoft.AspNetCore.Mvc;
using Middleware.Clients;
using Middleware.Clients.ClientArchiveApiClient;
using Middleware.DTO;

namespace Middleware.Controllers;

[ApiController]
[Route("middleware/booking")]
public class BookingController
{
    private readonly IMasterApiClient _masterApiClient;
    private readonly IBookingApiClient _bookingApiClient;
    private readonly IClientArchiveApiClient _clientArchiveApiClient;
    private readonly IMasterArchiveApiClient _masterArchiveApiClient;
    public BookingController
        (IClientArchiveApiClient clientArchiveApiClient, 
        IMasterArchiveApiClient masterArchiveApiClient,
        IBookingApiClient bookingApiClient,
        IMasterApiClient masterApiClient)
    {
        _clientArchiveApiClient = clientArchiveApiClient;
        _masterArchiveApiClient = masterArchiveApiClient;
        _bookingApiClient = bookingApiClient;
        _masterApiClient = masterApiClient;
    }

    [HttpPost("book")]
    public async Task<BookingResponse> Book([FromBody] BookingCreateRequest request)
    {
        BookingResponse res = null;
        var clientArchiveSaved = false;

        try
        {
            res = await _bookingApiClient.BookSlot(request);
            
            await _clientArchiveApiClient.ClientArchiveInsert(
                request.ClientId,
                res.ServiceMasterId,
                res.OrganizationId,
                res.BookingDt,
                res.BookingDt.AddMinutes(res.DurationMinutes));

            clientArchiveSaved = true;

            int servicePrice = await _masterApiClient.GetMasterServicePriceId(res.MasterId,
                res.ServiceMasterId);
            
            Console.WriteLine($"DurationMinutes {res.DurationMinutes}");
            await _masterArchiveApiClient.MasterArchiveInsert(
                res.MasterId,
                res.OrganizationId,
                res.BookingDt,
                decimal.Round(res.DurationMinutes/60m, 2),
                servicePrice,
                0,
                1
                );
            
            return res;
        }
        catch (Exception)
        {
            if (clientArchiveSaved)
            {
                await _clientArchiveApiClient.ClientArchiveDelete(request.ClientId);
            }
            
            if (res != null)
            {
                await _bookingApiClient.CancelBookSlot(
                    request.ClientId,
                    res.MasterId,
                    res.BookingDt);
            }

            throw;
        }
    }
}