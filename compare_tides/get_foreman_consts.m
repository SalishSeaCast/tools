function [amp,pha]=get_foreman_consts(long,lat,harm,num,Lat,Long)

% function [amp,phase]=get_foreman_consts(long,lat)
%
% Function to extract amplitude and phase lag from Mike Foreman's 
% tidal model of Vancouver Island
% 
% Note: long must be in degrees EAST (i.e. -123.5)

% Kate Le Souef, January 2014, based on vitideh.m function by Richard Dewey

warning off MATLAB:divideByZero

%First find the 3 closest nodes near this long/lat
d=ones(num,1)*NaN;
% next block of code just find closest nodes given a node index, then just NN=1; I=index;
for i=1:num 
    d(i)=gcdist(lat,long,Lat(i),Long(i)); 
end
[D,I]=sort(d);
NN=3; % how many close nodes (3-5)
I=I(1:NN); % these are the NN clostest nodes.
D=D(1:NN);
idwa=sum(D.^-1);
tidecon = zeros(1,2,3);
ampavg=0; phaavg=0;

for i=1:NN,
    j=I(i);
    disp(j)
    disp(Lat(j))
    disp(Long(j))
    tidecon(:,:,i)=[harm.Zamp(j),harm.Zpha(j)];
    ampavg = ampavg + tidecon(1,1,i)/D(i);
    phaavg = phaavg + tidecon(1,2,i)/D(i);
end

amp=ampavg/idwa;
pha=phaavg/idwa;
