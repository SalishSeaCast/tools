function [] = mw_gsw_p_from_z(outfile, zfile, latfile)
  startup()
  z = dlmread(zfile,',');
  lat = dlmread(latfile, ',');
  y = gsw_p_from_z(z, lat);
  dlmwrite(outfile, y, ',')
