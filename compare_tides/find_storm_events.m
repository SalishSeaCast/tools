function [startind,endind,lengthstorm] = find_storm_events(anomaly,tim,anomthres,stormlength)

%find storm surge events given a time vector (tim) and sea surface anomaly
%function [startind,endind] = find_storm_events(anomaly,tim,anomthres,stormlength)
% where 'anomaly' is the vector of sea surface anomalies at times 'tim'
% 'anomthres' is the sea surface anomaly [m] above which storms are defined 
% e.g. anomthres = 0.40
% 'stormlength' is the minimum length of the storm [hrs]
% e.g. stormlength = 6

%define the threshold
I = find(anomaly >= anomthres);

%initialise
jj = 1;
ind = 1;
startind = zeros(1,100);
endind = zeros(1,100);

%plot the anomaly
figure; hold on
plot(tim,anomaly,'.')
datetick

%find consecutive anomalies over the threshold
while jj <= length(anomaly)
    %is the anomaly over the threshold?
    if anomaly(jj) > anomthres
        %is the next anomaly over the threshold? If so, how long is anomaly > threshold for?
        startind(ind) = jj;
        kk = jj+1;
        while anomaly(kk) > anomthres
            kk = kk + 1;
        end
        endind(ind) = kk-1;
        ind = ind+1;
        plot(tim(jj),anomaly(jj),'*m')
        plot(tim(kk-1),anomaly(kk-1),'*g')
        jj = kk + 1;
    else
        jj = jj + 1;
    end
end

%remove the zeros and any storms shorter than the defined storm length
lengthstorm = endind - startind;    %[hours]
I = lengthstorm <=stormlength;
endind(I) = [];
startind(I) = [];
lengthstorm = endind-startind;

%print out some information
disp(['number of storms found = ',num2str(length(endind))])
disp(['longest storm = ',num2str(max(lengthstorm)),' hours (',...
    datestr(tim(startind(lengthstorm==max(lengthstorm)))),')'])
disp(['highest anomaly in records = ',num2str(max(anomaly)),' m (',...
    datestr(tim(anomaly==max(anomaly))),')'])
    
%output some data to a text file
M = {datestr(tim(startind)), endind-startind};
n = length(M{1});
%create a new file
filename = 'storms.txt';
fid = fopen(filename, 'w');
%add some headers
fprintf(fid, 'Start date \t \t \t \t Duration (hrs) \n');
for row=1:n
    fprintf(fid, '%s \t', M{1,1}(row,:));
    fprintf(fid,' %d\n', M{1,2}(:,row));
end
fclose(fid);
