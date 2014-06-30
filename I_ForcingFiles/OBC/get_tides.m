function [pred,wlev,anomaly,tim] = get_tides(csvfilename, location)

% Take the csv file of measured water level and calculate sea surface
% anomaly using predicted tide level from t_tide
% e.g. [pred,wlev,anomaly] = get_tides('wlev_timeseries.csv', 'tofino(2)');
% location is the location for t_tide predictions. This should correspond
% to the location of the measured water level.
% The dates are set by the date in the csvfilename
% This function can be used in generation of the anomaly forcing files.


% KLS November 2013
% Feb 2014: This has been adapted to use the t_tide package. NKS
% This fucntion will save the harmonics data and the predictions in separate files. 

%Read in the measured water level data the location
fid = fopen(csvfilename);
meas = textscan(fid,'%f/%f/%f %f:%f,%f,','HeaderLines',8);
lat = csvread(csvfilename,2,1,[2,1,2,1]);
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

%Use t_tide to determine harmonic constituents. Needs to be at least one
%year time series (366 days)
[tidestruc,~] = t_tide(wlev,'start time',start_date(1,1),'latitude',lat);
    
%Get predicted tide for same period
pred = t_predic(tim,tidestruc,'latitude',lat);

%%% Determine latitude somehow from file

%Add mean to the predicted water levels. 
pred = pred +nanmean(wlev);

%Calculate sea level anomaly
anomaly = wlev - pred';

%Plot it
figure;
subplot(2,1,1)
plot(tim,wlev,'b',tim,pred,'m')
tit_str = ['Predicted tides (t tide) and measuared water levels at ' location];
title(tit_str)
legend('measured','predicted','Location','Best')
xlabel('time (PST)')
ylabel('water level elevation (m CD)')
datetick('x','mm/yyyy')
subplot(2,1,2)
plot(tim,anomaly,'r')
xlabel('time (PST)'); ylim([-1,1]);
ylabel('water level anomaly (meas-pred) (m)')
datetick('x','mm/yyyy')

%Edit this part to save harmonics somehow.
%save the data - frist harmonics
freqs = tidestruc.freq; a = tidestruc.tidecon(:,1); kappa=tidestruc.tidecon(:,3);
name=tidestruc.name; amp_err = tidestruc.tidecon(:,2); pha_err = tidestruc.tidecon(:,4);
n=length(kappa);
filename = [location  '_ttide_harms.csv'];
fid = fopen(filename, 'w');
%add some headers
fprintf(fid, 'Constituent \t frequency \t  Amplitude (m) \t amp_err \t Phase (PST) \t pha_err \n');
for row=1:n
    fprintf(fid, '%s \t', name(row,:));
    fprintf(fid, '%f \t', freqs(row));
    fprintf(fid,' %f\t', a(row));
    fprintf(fid,' %f\t', amp_err(row));
    fprintf(fid,' %f\t', kappa(row));
    fprintf(fid,' %f\n', pha_err(row));
end
fclose(fid);

%second save predictions
M = datestr(tim);
n = length(tim);
filename = [location  '_ttide_prediction_' datestr(start_date) '_' datestr(end_date) '.csv'];
fid = fopen(filename, 'w');
%add some headers
fprintf(fid, 'Time_Local \t wlev_pred \n');
for row=1:n
    fprintf(fid, '%s \t', M(row,:));
    fprintf(fid,' %f\n', pred(row));
end
fclose(fid);
