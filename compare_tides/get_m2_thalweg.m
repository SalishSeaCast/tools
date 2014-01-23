%Get Foreman model along thalweg

%points from Nancy's thalweg calculator
load('/ocean/klesouef/meopar/tools/compare_tides/thalweg-lonlat.txt')
long = thalweg_lonlat(:,1);
lat = thalweg_lonlat(:,2);
numpoints = length(lat);


%get the grid data (extract node numbers and node locations)
load /ocean/rich/more/tpack/model/xMBdyLargeDomain 
Nodenum=x(:,1); 
Xp=x(:,2);  % X,Y
Yp=x(:,3);
Long=x(:,2)/10/cosd(49)-124.5; % Convert back to lat/long
Lat=x(:,3)/10+48;
iflag=x(:,4); % 0=water, 1=land boundary, 2=island boundary, 5=water bdy, 6=coast bdy
Dep=x(:,5);  % Depth at node.


%get the amp and pha data
% M2 tide
fid=fopen('/ocean/rich/more/tpack/ampfdat/m2_amph_svi_r2.dat');
A=fread(fid,Inf,'uchar');
fclose(fid);
Anum=sscanf(char(A),'%f');
M2.Zamp   =Anum(	   1:12573);
M2.Zpha   =Anum(12573  +[1:12573]);
num = length(M2.Zamp);

m2amp = zeros(length(long),1);
m2pha = zeros(length(lat),1);
for k = 1:length(lat)
    disp(k)
    [m2amp(k,1),m2pha(k,1)]=get_foreman_consts(long(k,1),lat(k,1),M2,num,Lat,Long);
end

output = [m2amp m2pha];
save foreman_m2_thalweg.txt output -ASCII
