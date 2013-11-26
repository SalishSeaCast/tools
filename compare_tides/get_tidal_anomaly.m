function [pred,wlev,anomaly,tim] = get_tidal_anomaly(csvfilename, startyear)

% Take the csv file of measured water level and calculate sea surface
% anomaly using predicted tide level from t_tide
% e.g. [pred,wlev,anomaly] = get_tidal_anomaly('wlev_timeseries.csv', 2003);
%
% KLS November 2013

%Read in the measured water level data from Point Atkinson
%meas = csvread(csvfilename,8,1);
fid = fopen('wlev_timeseries.csv');
meas = textscan(fid,'%f/%f/%f %f:%f,%f,','HeaderLines',8);
fclose(fid);
time = datenum(meas{1},meas{2},meas{3},meas{4},meas{5},0);
wlev = meas{6};

%Start date of measured water level record
start_date = time(1);
end_date = time(end);

%NEED TO DEAL WITH MISSING DATES
tim = start_date:1/24:end_date;
test = padarray(time,[(length(tim)-length(time)) 0],'post');

newtime = zeros(length(tim),2);
%counter in measured time
counter = 1;
%tt is counter in created time
for tt = 1:length(tim)
    I = time(counter) == tim(tt);
    if I
        newtime(tt,1) = time(counter);
        newtime(tt,2) = wlev(counter);
        counter = counter + 1;
    else
        newtime(tt,1) = tim(tt);
        newtime(tt,2) = NaN;
    end
end

time = newtime(:,1);
wlev = newtime(:,2);

%Perform tidal analysis to get tidestruc
[tidestruc,~] = t_tide(wlev,'start time',start_date,'latitude',49);

%Get predicted tide for same period
tim = start_date:1/24:end_date;
pred = t_predic(tim,tidestruc,'latitude',49);

%Adjust for datums (MSL is 3.1m CD at Point Atkinson... or is it?? CHECK!!!)
pred = pred + 3.1;

%Calculate sea level anomaly
anomaly = wlev - pred';

%Smooth the anomaly
averaging_period = 11;   %[hours]
interval = round((averaging_period-1)/2);
test = zeros(length(anomaly),1);
for kk = 1:length(anomaly)
    if kk <= interval
        test(kk) = mean(anomaly(kk:kk+interval));
    elseif kk > length(anomaly)-interval
        test(kk) = mean(anomaly(kk-interval:kk));
    else
        test(kk) = mean(anomaly(kk-interval:kk+interval));
    end
end

%Plot it
figure
plot(tim,wlev,'b',tim,pred,'m',tim,anomaly,'r.')
legend('measured','predicted','anomaly','Location','EastOutside')
xlabel('time')
ylabel('water level elevation (m CD)')
datetick('x','mm/yyyy')


