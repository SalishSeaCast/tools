function [pred,wlev,anomaly,tim] = get_tidal_anomaly(csvfilename)

% Take the csv file of measured water level and calculate sea surface
% anomaly using predicted tide level from t_tide
% e.g. [pred,wlev,anomaly] = get_tidal_anomaly('wlev_timeseries.csv', 2003);
%
% KLS November 2013

%Read in the measured water level data from Point Atkinson
fid = fopen(csvfilename);
meas = textscan(fid,'%f/%f/%f %f:%f,%f,','HeaderLines',8);
fclose(fid);

%Calculate dates from columns of data
time = datenum(meas{1},meas{2},meas{3},meas{4},meas{5},0);
wlev = meas{6};

%Start date of measured water level record
start_date = time(1);
end_date = time(end);

%measured data may not have entry for every date in the range
tim = start_date:1/24:end_date;
newmeas = zeros(length(tim),2);

%counter in measured time
counter = 1;
%tt is counter in created time
for tt = 1:length(tim)
    if time(counter) == tim(tt)
        newmeas(tt,1:2) = [time(counter), wlev(counter)];
        counter = counter + 1;
    else
        newmeas(tt,1:2) = [tim(tt), NaN];
    end
end

wlev = newmeas(:,2);

clear time newmeas meas

%t_tide should be run for 1 year of data at a time
[startyear,~,~,~,~,~] = datevec(tim(1));
[endyear,~,~,~,~,~] = datevec(tim(end-1));
%[allyears,~,~,~,~,~] = datevec(tim);
pred = zeros(length(tim),1);
predcounter = 1;

for yr = startyear:endyear
    disp(yr)
    I = tim >= datenum(yr,1,1) & tim < datenum(yr+1,1,1);
    start_date = tim(I);
    disp(datestr(start_date(1,1)))
    %Perform tidal analysis to get tidestruc
    [tidestruc,~] = t_tide(wlev(I),'start time',start_date(1,1),'latitude',49);
    
    %Get predicted tide for same period
    pred(predcounter:predcounter+length(start_date)-1) = t_predic(tim(I),tidestruc,'latitude',49);
    predcounter = predcounter+length(start_date);
    disp(predcounter)
end

%Adjust for datums (MSL is 3.1m CD at Point Atkinson... or is it?? CHECK!!!)
pred = pred + 3.1;

%Calculate sea level anomaly
anomaly = wlev - pred;

%Plot it
figure
plot(tim,wlev,'b',tim,pred,'m',tim,anomaly,'r.')
legend('measured','predicted','anomaly','Location','EastOutside')
xlabel('time')
ylabel('water level elevation (m CD)')
datetick('x','mm/yyyy')


