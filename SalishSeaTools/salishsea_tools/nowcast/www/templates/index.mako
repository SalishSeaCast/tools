***********************************
Salish Sea NEMO Model Daily Results
***********************************

${calendar_grid(last_month_cols, this_month_cols, prelim_fcst_dates, fcst_dates, nowcast_dates)}


<%def name="calendar_grid(last_month_cols, this_month_cols, prelim_fcst_dates, fcst_dates, nowcast_dates)">
.. raw:: html

    <div class="row">
      <div class="col-md-8 col-md-offset-1">
        <table class="table table-striped">
          <tr>
            <td></td>
            %if last_month_cols != 0:
              ${month_heading(last_month_cols, prelim_fcst_dates, 0)}
            %endif
            ${month_heading(this_month_cols, prelim_fcst_dates, -1)}
          </tr>
          <tr>
            <th>Sea Surface Height &amp; Weather</th>
          </tr>
          ${grid_row("Preliminary Forecast", prelim_fcst_dates, "forecast2", "publish")}
          ${grid_row("Forecast", fcst_dates, "forecast", "publish")}
          ${grid_row("Nowcast", nowcast_dates, "nowcast", "publish")}

          <tr>
            <th>Tracers &amp; Currents</th>
          </tr>
          ${grid_row("Nowcast", nowcast_dates, "nowcast", "research")}
        </table>
      </div>
    </div>
</%def>


<%def name="month_heading(month_cols, dates, index)">
  <th class="text-center" colspan="${month_cols}">
    %if month_cols < 3:
      ${dates[index].format('MMM')}
    %else:
      ${dates[index].format('MMMM')}
    %endif
  </th>
</%def>


<%def name="grid_row(title, dates, run_type, page_type)">
  <tr>
    <td class="text-right">${title}</td>
    %for d in dates:
      <td class="text-center">
        <a href="${run_type}/${page_type}_${d.format("DDMMMYY").lower()}.html">
          ${d.format("D")}
        </a>
      </td>
    %endfor
  </tr>
</%def>
