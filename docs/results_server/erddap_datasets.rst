*********************************
ERDDAP :file:`datasets.xml` Setup
*********************************

:file:`/opt/tomcat/content/erddap/datasets.xml`

Charles had to create a :kbd:`erddap` user and change group of :file:`/opt/tomcat/content/erddap/*` to it and make that dir and files below it group-writable.

:file:`/results/erddaplogs/` also had to have :kbd:`erddap` as its group and be made group-writable.

also erddapcache and erddapflags


Generate Section for :file:`datasets.xml`
=========================================

:file:`/opt/tomcat/webapps/erddap/WEB-INF/GenerateDatasetsXml.sh`
run from :file:`/opt/tomcat/webapps/erddap/WEB-INF/` with

.. code-block:: bash

    bash GenerateDatasetsXml.sh

Initial test:

.. code-block:: none

    Which EDDType (default="EDDGridFromDap")
    ? EDDGridFromNcFiles

    Parent directory (default="")
    ? /results/SalishSea/nowcast/

    File name regex (e.g., ".*\.nc") (default="")
    ? .*PointAtkinson.nc$

    Full file name of one file (default="")
    ? /results/SalishSea/nowcast/13jan16/PointAtkinson.nc

    ReloadEveryNMinutes (e.g., 10080) (default="")
    ? 60

generates:

.. code-block:: xml

    <!--
     DISCLAIMER:
       The chunk of datasets.xml made by GenerageDatasetsXml isn't perfect.
       YOU MUST READ AND EDIT THE XML BEFORE USING IT IN A PUBLIC ERDDAP.
       GenerateDatasetsXml relies on a lot of rules-of-thumb which aren't always
       correct.  *YOU* ARE RESPONSIBLE FOR ENSURING THE CORRECTNESS OF THE XML
       THAT YOU ADD TO ERDDAP'S datasets.xml FILE.

     DIRECTIONS:
     * Read about this type of dataset in
       http://coastwatch.pfeg.noaa.gov/erddap/download/setupDatasetsXml.html .
     * Read http://coastwatch.pfeg.noaa.gov/erddap/download/setupDatasetsXml.html#addAttributes
       so that you understand about sourceAttributes and addAttributes.
     * Note: Global sourceAttributes and variable sourceAttributes are listed
       below as comments, for informational purposes only.
       ERDDAP combines sourceAttributes and addAttributes (which have
       precedence) to make the combinedAttributes that are shown to the user.
       (And other attributes are automatically added to longitude, latitude,
       altitude, depth, and time variables).
     * If you don't like a sourceAttribute, override it by adding an
       addAttribute with the same name but a different value
       (or no value, if you want to remove it).
     * All of the addAttributes are computer-generated suggestions. Edit them!
       If you don't like an addAttribute, change it.
     * If you want to add other addAttributes, add them.
     * If you want to change a destinationName, change it.
       But don't change sourceNames.
     * You can change the order of the dataVariables or remove any of them.
    !!! The source for nowcast_816c_7201_0e9b has nGridVariables=4,
    but this dataset will only serve 1 because the others use different dimensions.
    -->

    <dataset type="EDDGridFromNcFiles" datasetID="nowcast_816c_7201_0e9b" active="true">
        <reloadEveryNMinutes>60</reloadEveryNMinutes>
        <updateEveryNMillis>10000</updateEveryNMillis>
        <fileDir>/results/SalishSea/nowcast/</fileDir>
        <recursive>true</recursive>
        <fileNameRegex>.*PointAtkinson.nc$</fileNameRegex>
        <metadataFrom>last</metadataFrom>
        <matchAxisNDigits>20</matchAxisNDigits>
        <fileTableInMemory>false</fileTableInMemory>
        <accessibleViaFiles>false</accessibleViaFiles>
        <!-- sourceAttributes>
            <att name="Conventions">CF-1.1</att>
            <att name="file_name">PointAtkinson.nc</att>
            <att name="production">An IPSL model</att>
            <att name="TimeStamp">2016-JAN-13 10:04:24 GMT-0800</att>
        </sourceAttributes -->
        <addAttributes>
            <att name="cdm_data_type">Grid</att>
            <att name="Conventions">CF-1.6, COARDS, ACDD-1.3</att>
            <att name="infoUrl">???</att>
            <att name="institution">???</att>
            <att name="keywords">data, height, level, local, sea, sea level, sea surface height, sossheig, source, surface, time_counter</att>
            <att name="license">[standard]</att>
            <att name="standard_name_vocabulary">CF Standard Name Table v29</att>
            <att name="summary">Data from a local source.</att>
            <att name="title">Data from a local source.</att>
        </addAttributes>
        <axisVariable>
            <sourceName>time_counter</sourceName>
            <destinationName>time</destinationName>
            <!-- sourceAttributes>
                <att name="_ChunkSize" type="int">1</att>
                <att name="axis">T</att>
                <att name="bounds">time_counter_bnds</att>
                <att name="calendar">gregorian</att>
                <att name="long_name">Time axis</att>
                <att name="standard_name">time</att>
                <att name="time_origin"> 2014-SEP-10 00:00:00</att>
                <att name="title">Time</att>
                <att name="units">seconds since 2014-09-10 00:00:00</att>
            </sourceAttributes -->
            <addAttributes>
                <att name="_ChunkSize">null</att>
                <att name="bounds">null</att>
                <att name="ioos_category">Statistics</att>
            </addAttributes>
        </axisVariable>
        <axisVariable>
            <sourceName>y</sourceName>
            <destinationName>y</destinationName>
            <!-- sourceAttributes>
            </sourceAttributes -->
            <addAttributes>
                <att name="ioos_category">Location</att>
                <att name="long_name">Y</att>
            </addAttributes>
        </axisVariable>
        <axisVariable>
            <sourceName>x</sourceName>
            <destinationName>x</destinationName>
            <!-- sourceAttributes>
            </sourceAttributes -->
            <addAttributes>
                <att name="ioos_category">Location</att>
                <att name="long_name">X</att>
            </addAttributes>
        </axisVariable>
        <dataVariable>
            <sourceName>sossheig</sourceName>
            <destinationName>sossheig</destinationName>
            <dataType>float</dataType>
            <!-- sourceAttributes>
                <att name="_ChunkSize" type="intList">1 1 1</att>
                <att name="_FillValue" type="float">9.96921E36</att>
                <att name="coordinates">time_counter nav_lat nav_lon</att>
                <att name="interval_operation" type="float">10.0</att>
                <att name="interval_write" type="float">900.0</att>
                <att name="long_name">sea surface height</att>
                <att name="online_operation">ave(X)</att>
                <att name="standard_name">sea surface height</att>
                <att name="units">m</att>
            </sourceAttributes -->
            <addAttributes>
                <att name="_ChunkSize">null</att>
                <att name="coordinates">null</att>
                <att name="ioos_category">Sea Level</att>
            </addAttributes>
        </dataVariable>
    </dataset>


regex for hourly results: :kbd:`.*SalishSea_1h_\d{8}_\d{8}_grid_[TUVW]\.nc$`


Dataset Attributes
==================

Changes:

* :kbd:`datasetID` to :kbd:`ubcSSnPointAtkinsonSSH15m`

  * :kbd:`ubc` means UBC
  * :kbd:`SS` means Salish Sea NEMO Model
  * :kbd:`n` means nowcast (:kbd:`f` for forecast, :kbd:`f2` for forecast2, :kbd:`ng` for nowcast-green)
  * :kbd:`PointAtkinson` means Point Atkinson
  * :kbd:`SSH` means Sea Surface Height
  * :kbd:`15m` means 15 minute averaged values

* :kbd:`institution` to :kbd:`UBC EOAS`

  * an acronym, <20 characters

* :kbd:`title` to :kbd:`Nowcast, Point Atkinson, Sea Surface Height, 15min`

  * should be <80 characters, only the 1st 40 of which will be displayed in the list of datasets table

* :kbd:`infoUrl` to http://salishsea-meopar-tools.readthedocs.org/en/latest/results_server/index.html#salish-sea-model-results

* :kbd:`license` to::

     The Salish Sea MEOPAR NEMO model results are copyright 2013-2016 by the Salish Sea MEOPAR Project Contributors and The University of British Columbia.

     They are licensed under the Apache License, Version 2.0. http://www.apache.org/licenses/LICENSE-2.0


Additions:

* acknowledgement:

  * .. code-block:: xml

      <att name="acknowledgment">MEOPAR, ONC, Compute Canada</att>

* :kbd:`<att name="creator_name">Salish Sea MEOPAR Project Contributors</att>`
* :kbd:`<att name="creator_email">sallen@eos.ubc.ca</att>`
* :kbd:`<att name="creator_url">http://salishsea-meopar-docs.readthedocs.org/</att>`
* :kbd:`<att name="drawLandMask">over</att>` (not really relevant for this single location dataset)
* :kbd:`<att name="project">Salish Sea MEOPAR NEMO Model</att>`
* :kbd:`<att name="coverage_content_type">modelResult</att>`
* :kbd:`summary`::

    Nowcast, Point Atkinson, Sea Surface Height, 15min.

    Sea surface height values averaged over 15 minute intervals from Salish Sea NEMO model nowcast runs. The values are calculated at the model grid point closest to the Point Atkinson tide gauge station on the north side of English Bay, near Vancouver, British Columbia.


* :kbd:`<att name="institution_fullname">Earth, Ocean &amp; Atmospheric Sciences, University of British Columbia</att>`


Axis Variables
==============

* :kbd:`time_counter` - no changes
* :kbd:`y` - replace with:

  .. code-block:: xml

      <axisVariable>
          <sourceName>nav_lon</sourceName>
          <destinationName>longitude</destinationName>
      </axisVariable>

* :kbd:`x` - replace with:

  .. code-block:: xml

      <axisVariable>
          <sourceName>nav_lat</sourceName>
          <destinationName>latitude</destinationName>
      </axisVariable>


Data Variables
==============

* sossheig:

  * :kbd:`destinationName` to :kbd:`ssh`


Verify Dataset Loading
======================

:file:`/opt/tomcat/webapps/erddap/WEB-INF/DasDds.sh`
run from :file:`/opt/tomcat/webapps/erddap/WEB-INF/` with

.. code-block:: bash

    bash DasDds.sh

Initial test:

.. code-block:: none

    Which datasetID (default="")?
    ubcSSnPointAtkinsonSSH15m

After no errors,
and sane looking :kbd:`.das` and :kbd:`.dds` output,
preemptively load the dataset by putting a file with its :kbd:`datasetID` value in :file:`/results/erddapflags/`; e.g.

.. code-block:: bash

    touch /results/erddapflag/ubcSSnPointAtkinsonSSH15m

That causes ERDDAP to load the dataset immediately,
and delete the flag file when it is done.
