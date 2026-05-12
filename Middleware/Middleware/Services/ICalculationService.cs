using Middleware.DTO;

namespace Middleware.Services;

public interface ICalculationService
{
    List<TimeOnly> CalculatePossibleStartTimes(TimeOnly from, TimeOnly to, TimeSpan duration, TimeSpan granularTimeStep);

    List<TimeSlotWithDate> CalculatePossibleTimeSlotsOnDate
    (List<TimeSlotWithDate> freeTimeSlots, TimeSpan serviceDuration, TimeSpan granularTimeStep);

    List<TimeSlotWithDate> CalculateClosestPossibleTimeSlots
        (List<TimeSlotWithDate> freeTimeSlots, TimeSlot timeInterval, TimeSpan duration, TimeSpan granularTimeStep);

    public double CalculateMastersBusyWorkingHours(List<TimeSlotWithDate> bookedSlots);
    int CalculateMastersCompletedServices(List<TimeSlotWithDate> workingDays);

    List<TimeSegment> BuildDayTimeline(TimeSlotWithDate workTime, List<TimeSlotWithDate> busyTimeSlots, TimeSpan step);

    List<TimeSlot> CalculateBestTimeSlots(List<TimeSlotWithDate> freeTimeIntervals, TimeSpan serviceDuration,
        TimeSpan granularTimeStep);
}