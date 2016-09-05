function [] = mw_gsw_SA_from_SP(filename, SPfile, pfile, longfile, latfile)
  startup()
  SP = dlmread(SPfile, ',');
  p = dlmread(pfile, ',');
  long = dlmread(longfile, ',');
  lat = dlmread(latfile, ',');
y = gsw_SA_from_SP(SP, p, long, lat);
  dlmwrite(filename, y, ',')
