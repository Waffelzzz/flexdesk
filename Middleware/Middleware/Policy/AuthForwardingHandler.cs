using System.Net.Http.Headers;

namespace Middleware.Policy;

public class AuthForwardingHandler : DelegatingHandler
{
    private readonly IHttpContextAccessor _contextAccessor;

    public AuthForwardingHandler(IHttpContextAccessor contextAccessor)
    {
        _contextAccessor = contextAccessor;
    }

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        var token = _contextAccessor.HttpContext?
            .Request.Headers["Authorization"]
            .ToString();

        if (!string.IsNullOrEmpty(token) && token.StartsWith("Bearer "))
        {
            var jwt = token.Replace("Bearer ", "");

            request.Headers.Authorization =
                new AuthenticationHeaderValue("Bearer", jwt); // ✅ правильно
        }

        return await base.SendAsync(request, cancellationToken);
    }
}