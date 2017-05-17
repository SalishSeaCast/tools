function [] = mw_gsw_CT_from_pt(filename, SAfile, PTfile)
  startup()
  SA = dlmread(SAfile,',');
  pt = dlmread(PTfile, ',');
  y = gsw_CT_from_pt(SA, pt);
  dlmwrite(filename, y, ',')
