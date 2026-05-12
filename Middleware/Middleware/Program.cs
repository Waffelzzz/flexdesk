
using System.Text.Json;
using Middleware.Clients;
using Middleware.Policy;
using Middleware.Services;
using Microsoft.OpenApi.Models;
using Middleware.Clients.ClientArchiveApiClient;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHttpContextAccessor();
builder.Services.AddTransient<AuthForwardingHandler>();

builder.Services.AddControllers();
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;;
    });



builder.Services.AddScoped<ICalculationService, CalculationService>();
builder.Services.AddHttpClient<IBookingApiClient, BookingApiClient>(client =>
{
    client.BaseAddress = new Uri("http://desk-api:8000");
}).AddHttpMessageHandler<AuthForwardingHandler>();


builder.Services.AddHttpClient<IMasterApiClient, MasterApiClient>(client =>
{
    client.BaseAddress = new Uri("http://desk-api:8000");
}).AddHttpMessageHandler<AuthForwardingHandler>();

builder.Services.AddHttpClient<IMasterArchiveApiClient, MasterArchiveApiClient>(client =>
{
    client.BaseAddress = new Uri("http://desk-api:8000");
}).AddHttpMessageHandler<AuthForwardingHandler>();

builder.Services.AddHttpClient<IClientArchiveApiClient, ClientArchiveApiClient>(client =>
{
    client.BaseAddress = new Uri("http://desk-api:8000");
}).AddHttpMessageHandler<AuthForwardingHandler>();



builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    var xmlFile = $"{System.Reflection.Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xmlFile);
    c.IncludeXmlComments(xmlPath);
    
    c.AddSecurityDefinition("oauth2", new OpenApiSecurityScheme
    {
        Type = SecuritySchemeType.OAuth2,
        Flows = new OpenApiOAuthFlows
        {
            Password = new OpenApiOAuthFlow
            {
                TokenUrl = new Uri("http://localhost:8000/v1/auth/login"),
                Scopes = new Dictionary<string, string>()
            }
        }
    });
    
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "oauth2"
                }
            },
            Array.Empty<string>()
        }
    });
});

builder.Services
    .AddReverseProxy()
    .LoadFromMemory(
        new[]
        {
            new Yarp.ReverseProxy.Configuration.RouteConfig
            {
                RouteId = "v1-route",
                ClusterId = "backend",
                Match = new Yarp.ReverseProxy.Configuration.RouteMatch
                {
                    Path = "/v1/{**catch-all}"
                }
            }
        },
        new[]
        {
            new Yarp.ReverseProxy.Configuration.ClusterConfig
            {
                ClusterId = "backend",
                Destinations = new Dictionary<string, Yarp.ReverseProxy.Configuration.DestinationConfig>
                {
                    {
                        "d1", new Yarp.ReverseProxy.Configuration.DestinationConfig
                        {
                            Address = "http://desk-api:8000"
                        }
                    }
                }
            }
        }
    );
builder.Services.AddCors(options =>
{
    options.AddPolicy("Policy", policy =>
    {
        policy.WithOrigins("http://localhost:5173")
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});




var app = builder.Build();
app.UseCors("Policy");
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapReverseProxy();

app.UseHttpsRedirection();
app.MapControllers();
app.Run();