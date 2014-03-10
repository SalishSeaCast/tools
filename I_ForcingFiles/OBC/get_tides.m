function [pred,wlev,anomaly,tim, tideharm] = get_tides(csvfilename, location)

% Take the csv file of measured water level and calculate sea surface
% anomaly using predicted tide level from t_xtide
% e.g. [pred,wlev,anomaly] = get_tides('wlev_timeseries.csv', 'tofino(2)');
% location is the location for t_xtide predictions. This should correspond
% to the location of the measured water level.
% The dates are set by the date in the csvfilename


% KLS November 2013
% Feb 2014: This has been adapted to use the t_xtide package. NKS
% This fcuntion will save the harmonics data and the predictions in separate files. 

%Read in the measured water level data the location
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

% use t_xtide to get the predictions
[tidestruc] = t_xtide(location,tim,'format','full','units','meters');
tideharm=t_xtide(location,'format','info','units','meters');
    
pred = tidestruc.yout;

%Calculate sea level anomaly
anomaly = wlev - pred';

%Plot it
figure;
subplot(2,1,1)
plot(tim,wlev,'b',tim,pred,'m')
title('Predicted tides (xtide) and measuared water levels at Tofino')
legend('measured','predicted','Location','Best')
xlabel('time (PST)')
ylabel('water level elevation (m CD)')
datetick('x','mm/yyyy')
subplot(2,1,2)
plot(tim,anomaly,'r')
xlabel('time (PST)'); ylim([-1,1]);
ylabel('water level anomaly (meas-pred) (m)')
datetick('x','mm/yyyy')


%save the data - frist harmonics
freqs = tideharm.freq; a = tideharm.A; kappa=tideharm.kappa;
n=length(kappa);
filename = [location  '_xtide_harms.csv'];
fid = fopen(filename, 'w');
%add some headers
fprintf(fid, 'Constiuent \t Amplitude (m) \t Phase  \n');
for row=1:n
    fprintf(fid, '%s \t', freqs(row,:));
    fprintf(fid,' %f\t', a(row));
    fprintf(fid,' %f\n', kappa(row));
end
fclose(fid)

%second save predictions
M = datestr(tim);
n = length(tim);
filename = [location  '_xtide_prediction_' datestr(start_date) '_' datestr(end_date) '.csv'];
fid = fopen(filename, 'w');
%add some headers
fprintf(fid, 'Time_Local \t wlev_pred \n');
for row=1:n
    fprintf(fid, '%s \t', M(row,:));
    fprintf(fid,' %f\n', pred(row));
end
fclose(fid)
