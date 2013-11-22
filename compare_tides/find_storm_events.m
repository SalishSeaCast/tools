function [startind,endind] = find_storm_events(anomaly,tim)

%find storm surge events given a time vector (tim) and sea surface anomaly

%define the threshold
threshold = 0.20;
I = find(anomaly >= threshold);
plot(tim(I),anomaly(I),'.')
hold on
datetick

%initialise
jj = 1;
ind = 1;
startind = zeros(1,100);
endind = zeros(1,100);

while jj <= length(anomaly)
    %is the anomaly over the threshold?
    if anomaly(jj) > threshold
        %is the next anomaly over the threshold? If so, how long is anomaly > threshold for?
        startind(ind) = jj;
        kk = jj+1;
        while anomaly(kk) > threshold
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
        
I = startind == 0;
startind(I) = [];
I = endind == 0;
endind(I) = [];
lengthstorm = endind - startind;    %[hours]
        