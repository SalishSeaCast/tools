function [] = mw_gsw_CT_from_t(filename, SA, t, p)
  startup()
  y = gsw_CT_from_t(SA, t, p)
  dlmwrite(filename, y, ',')
