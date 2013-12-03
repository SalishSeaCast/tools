function [startind,endind,lengthhigh] = find_high_wlev(wlev,tim,wlevthres,stormlength)

%find high water level events given a time vector (tim) and sea surface
%elevation
%
%function [startind,endind] = find_high_wlev(wlev,tim,wlevthres,stormlength)
% where 'wlev' is the vector of sea surface elevation at times 'tim'
% 'wlevthres' is the sea surface anomaly [m] above which eventsare defined 
% e.g. wlevthres = 0.40
% 'stormlength' is the minimum length of the storm [hrs]
% e.g. stormlength = 6

%define the threshold
I = find(wlev >= wlev);

%initialise
jj = 1;
ind = 1;
startind = zeros(1,100);
endind = zeros(1,100);

%plot the anomaly
figure; hold on
plot(tim,wlev,'.')
datetick

%find consecutive anomalies over the threshold
while jj <= length(wlev)
    %is the anomaly over the threshold?
    if wlev(jj) > wlevthres
        %is the next anomaly over the threshold? If so, how long is anomaly > threshold for?
        startind(ind) = jj;
        kk = jj+1;
        while wlev(kk) > wlevthres
            kk = kk + 1;
        end
        endind(ind) = kk-1;
        ind = ind+1;
        plot(tim(jj),wlev(jj),'*m')
        plot(tim(kk-1),wlev(kk-1),'*g')
        jj = kk + 1;
    else
        jj = jj + 1;
    end
end

%remove the zeros and any storms shorter than the defined storm length
lengthhigh = endind - startind;    %[hours]
I = lengthhigh <=stormlength;
endind(I) = [];
startind(I) = [];
lengthhigh = endind-startind;

%print out some information
 disp(['number of storms found = ',num2str(length(endind))])
 disp(['longest storm = ',num2str(max(lengthhigh)),' hours'])
 disp(['highest anomaly in records = ',num2str(max(wlev)),' m (',...
     datestr(tim(anomaly==max(anomaly))),')'])
     
%output some data to a text file
M = {datestr(tim(startind)), endind-startind};
n = length(M{1});
disp(n)
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
