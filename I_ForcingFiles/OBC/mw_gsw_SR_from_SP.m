function [] = mw_gsw_SR_from_SP(filename, SPfile)
  startup()
  SP = dlmread(SPfile, ',');
  y = gsw_SR_from_SP(SP);
  dlmwrite(filename, y, ',')
