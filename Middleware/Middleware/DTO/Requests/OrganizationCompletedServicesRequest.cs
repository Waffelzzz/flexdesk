namespace Middleware.DTO.Requests;

public class OrganizationCompletedServicesRequest
{
    /// <summary>Id Организации</summary>
    public int OrganizationId { get; set; }
    /// <summary>Дата с которой начинать отчет часов</summary>
    public DateOnly StartDate { get; set; }
    /// <summary>Дата на которой закончится отчет</summary>
    public DateOnly EndDate { get; set; }
}