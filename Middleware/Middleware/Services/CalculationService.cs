using Microsoft.AspNetCore.Identity;
using Middleware.DTO;

namespace Middleware.Services;

public class CalculationService: ICalculationService
{
    public List<TimeOnly> CalculatePossibleStartTimes
    (TimeOnly from, TimeOnly to, TimeSpan duration, TimeSpan granularTimeStep)
    {
        List<TimeOnly> possibleStartTimeList = new List<TimeOnly>();
        
        TimeOnly possibleStartTime = from;
        
        while (to - possibleStartTime >= duration)
        {
            possibleStartTimeList.Add(possibleStartTime);
            
            possibleStartTime = possibleStartTime.Add(granularTimeStep);
        }
        
        return possibleStartTimeList;
    }
    
    public List<TimeSlotWithDate> CalculatePossibleTimeSlotsOnDate
        (List<TimeSlotWithDate> freeTimeSlots, TimeSpan serviceDuration, TimeSpan granularTimeStep)
    {
        List<TimeSlotWithDate> timeSlots = new List<TimeSlotWithDate>();
        
        foreach (var freeTimeSlot in freeTimeSlots)
        {
            var starts = CalculatePossibleStartTimes
                (TimeOnly.FromDateTime(freeTimeSlot.Start), TimeOnly.FromDateTime(freeTimeSlot.End), serviceDuration, granularTimeStep);
            
            foreach (var start in starts)
            {
                timeSlots.Add(new TimeSlotWithDate(new TimeSlot(start, start.Add(serviceDuration)), DateOnly.FromDateTime(freeTimeSlot.Start)));
            }
        }
        return timeSlots;
    }

    public List<TimeSlotWithDate> CalculateClosestPossibleTimeSlots
    (List<TimeSlotWithDate> freeTimeSlots, TimeSlot timeInterval, TimeSpan duration, TimeSpan granularTimeStep)
    {
        List<TimeSlotWithDate> possibleTimeSlots = new List<TimeSlotWithDate>();
        
        List<TimeSlotWithDate> possibleIntervals = CalculatePossibleTimeSlotsOnDate(freeTimeSlots, duration, granularTimeStep);
        Console.WriteLine(possibleIntervals.ToString());
        //Сортировка чтобы timeinterval.Start <= freeInterval <= timeinterval.End
        foreach (TimeSlotWithDate slot in possibleIntervals)
        {
            if (TimeOnly.FromDateTime(slot.Start) >= timeInterval.Start && TimeOnly.FromDateTime(slot.End) <= timeInterval.End)
            {
                possibleTimeSlots.Add(slot);
            }
        }
        Console.WriteLine(possibleTimeSlots.ToString());
        return possibleTimeSlots;
    }

    public double CalculateMastersBusyWorkingHours(List<TimeSlotWithDate> bookedSlots)
    {
        double overallHours = 0f;

        foreach (var slot in bookedSlots)
        { 
            overallHours += (slot.End-slot.Start).TotalHours;
        }
        return overallHours;
    }

    public int CalculateMastersCompletedServices(List<TimeSlotWithDate> bookedSlots)
    {
        return bookedSlots.Count;
    }
    
    public List<TimeSegment> BuildDayTimeline(TimeSlotWithDate workTime, List<TimeSlotWithDate> busyTimeSlots, TimeSpan step)
    {

        List<TimeSlot> breakSlots = new();

        List<TimeSlot> absenceSlots = new(); // например отпуск

        // 1. bitmap
        var timeline = BuildTimeline(workTime, step);

        // 2. статусы
        ApplyAbsence(timeline, absenceSlots);
        ApplyBreaks(timeline, breakSlots);
        ApplyBusy(timeline, busyTimeSlots);
            //ApplyBuffer(timeline, busyTimeSlots, preBuffer, postBuffer);

        // 3. сжатие
        return CompressTimeline(timeline, workTime.End);
    }
    
    private List<(TimeOnly time, TimeStatus status)> BuildTimeline(
        TimeSlotWithDate workTime,
        TimeSpan step)
    {
        var timeline = new List<(TimeOnly, TimeStatus)>();

        var current = TimeOnly.FromDateTime(workTime.Start);

        while (current < TimeOnly.FromDateTime(workTime.End))
        {
            timeline.Add((current, TimeStatus.Free));
            current = current.Add(step);
        }

        return timeline;
    }
    
    private void ApplyAbsence(
        List<(TimeOnly time, TimeStatus status)> timeline,
        List<TimeSlot>? absenceSlots)
    {
        if (absenceSlots == null) return;

        foreach (var slot in absenceSlots)
        {
            for (int i = 0; i < timeline.Count; i++)
            {
                if (timeline[i].time >= slot.Start &&
                    timeline[i].time < slot.End)
                {
                    timeline[i] = (timeline[i].time, TimeStatus.Absence);
                }
            }
        }
    }
    
    private void ApplyBreaks(
        List<(TimeOnly time, TimeStatus status)> timeline,
        List<TimeSlot>? breakSlots)
    {
        if (breakSlots == null) return;

        foreach (var slot in breakSlots)
        {
            for (int i = 0; i < timeline.Count; i++)
            {
                if (timeline[i].time >= slot.Start &&
                    timeline[i].time < slot.End &&
                    timeline[i].status != TimeStatus.Absence)
                {
                    timeline[i] = (timeline[i].time, TimeStatus.Break);
                }
            }
        }
    }
    
    private void ApplyBusy(
        List<(TimeOnly time, TimeStatus status)> timeline,
        List<TimeSlotWithDate> busySlots)
    {
        foreach (var slot in busySlots)
        {
            for (int i = 0; i < timeline.Count; i++)
            {
                if (timeline[i].time >= TimeOnly.FromDateTime(slot.Start) &&
                    timeline[i].time < TimeOnly.FromDateTime(slot.End) && 
                    timeline[i].status != TimeStatus.Absence &&
                    timeline[i].status != TimeStatus.Break)
                {
                    timeline[i] = (timeline[i].time, TimeStatus.Busy);
                }
            }
        }
    }
    private void ApplyBuffer(
        List<(TimeOnly time, TimeStatus status)> timeline,
        List<TimeSlot> busySlots,
        TimeSpan preBuffer,
        TimeSpan postBuffer)
    {
        foreach (var slot in busySlots)
        {
            var bufferStart = slot.Start.Add(-preBuffer);
            var bufferEnd = slot.End.Add(postBuffer);

            for (int i = 0; i < timeline.Count; i++)
            {
                if (timeline[i].time >= bufferStart &&
                    timeline[i].time < bufferEnd &&
                    timeline[i].status == TimeStatus.Free)
                {
                    timeline[i] = (timeline[i].time, TimeStatus.Buffer);
                }
            }
        }
    }
    
    private List<TimeSegment> CompressTimeline(
        List<(TimeOnly time, TimeStatus status)> timeline,
        DateTime workEnd)
    {
        var result = new List<TimeSegment>();

        if (timeline.Count == 0)
            return result;

        var currentStatus = timeline[0].status;
        var segmentStart = timeline[0].time;

        for (int i = 1; i < timeline.Count; i++)
        {
            if (timeline[i].status != currentStatus)
            {
                result.Add(new TimeSegment
                {
                    Status = currentStatus,
                    Start = segmentStart,
                    End = timeline[i].time
                });

                currentStatus = timeline[i].status;
                segmentStart = timeline[i].time;
            }
        }

        // последний сегмент
        result.Add(new TimeSegment
        {
            Status = currentStatus,
            Start = segmentStart,
            End = TimeOnly.FromDateTime(workEnd)
        });

        return result;
    }

    public List<TimeSlot> CalculateBestTimeSlots(List<TimeSlotWithDate> freeTimeIntervals, TimeSpan serviceDuration, TimeSpan granularTimeStep)
    {
        List<TimeSlot> timeSlots = new List<TimeSlot>();
        freeTimeIntervals.Sort((a,b) => 
            (a.End - a.Start).TotalMinutes.CompareTo((b.End - b.Start).TotalMinutes));
        
        TimeSlotWithDate bestFreeTimeSlot = freeTimeIntervals.FirstOrDefault((x) => (x.End - x.Start).TotalMinutes >= serviceDuration.TotalMinutes);
        
        var starts = CalculatePossibleStartTimes(TimeOnly.FromDateTime(bestFreeTimeSlot.Start), TimeOnly.FromDateTime(bestFreeTimeSlot.End), serviceDuration, granularTimeStep);
        foreach (var start in starts)
        {
            timeSlots.Add(new TimeSlot(start, start.Add(serviceDuration)));
        }
        
        return timeSlots;
    }
}
