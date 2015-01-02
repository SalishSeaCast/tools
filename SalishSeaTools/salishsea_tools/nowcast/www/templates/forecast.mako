************************************************************************
${fcst_date.strftime('%A, %d %B %Y')} -- Salish Sea Storm Surge Forecast
************************************************************************

Disclaimer
==========

This site presents output from a research project.
Results are not expected to be a robust prediction of the storm surge.


Plots
=====

.. raw:: html
    <%
        run_dmy = run_date.strftime('%d%b%y').lower()
    %>
    %for svg_file in svg_file_roots:
    <object class="standard-plot" type="image/svg+xml"
      data="../_static/nemo/results_figures/forecast/${run_dmy}/${svg_file}_${run_dmy}.svg">
    </object>
    <hr>
    %endfor

Summary blurb

[1] Soontiens et al., 2014,  In prep.


Data Sources
============

The forcing data used to drive the Salish Sea model is obtained from several sources:

To Come
