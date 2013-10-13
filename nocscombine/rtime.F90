       function rtime(tbase)
c
c f90 function using the standard f90 date_and_time function
c to return the elapsed runtime in seconds.
c
c Normal operation is to return the elapsed runtime in seconds
c since the first call.
c The following exceptions apply:
c 1. If tbase is not equal to 0.0 on the first call then it
c    is used as the reference start time.
c 2. If tbase = 0.0 on the first call then the actual time in
c    seconds is returned
c
c The actual value of tbase is irrelevant on all subsequent calls
c
       real hours,minutes,seconds,start_time,now,tbase
       integer day,lday
       data start_time/-87401.0/
       save start_time, lday
       character*10 date, time
       call date_and_time(date,time)
       read(time,'(f10.3)') now
       read(date(7:8),'(i2)') day
       hours = int(now*0.0001)
       minutes = int(now*0.01) - 100*hours
       seconds = amod(now,100.)
c
       if(start_time.lt.-86400.0) then
c
c Decide behaviour on first call
c
        lday = day
        start_time = hours*3600. + minutes*60 + seconds
        if(tbase.eq.0.0) then
         rtime = start_time
        else
         rtime = start_time - tbase
         start_time = tbase
        endif
        start_time = -1. * start_time
       else
c
c Standard behaviour on all subsequent calls
c
        now = hours*3600. + minutes*60 + seconds
        if(day.ne.lday) then
          start_time = start_time + 86400.
          lday = day
        endif
        rtime = now + start_time
       endif
       return
       end
