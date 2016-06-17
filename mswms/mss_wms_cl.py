#!/usr/bin/env python
"""Command line interface to the MSS Web Map Service. Allows the user to
   generate plots from the command line.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

   When using this software, please acknowledge its use by citing the
   reference documentation in any publication, presentation, report,
   etc. you create:

   Rautenhaus, M., Bauer, G., and Doernbrack, A.: A web service based tool
   to plan atmospheric research flights, Geosci. Model Dev., 5, 55-71,
   doi:10.5194/gmd-5-55-2012, 2012.

********************************************************************************

The program is a simple wrapper around the WSGI module in mss_wms_wsgi.py. It
allows the user to specify the parameters otherwise passed in the URL query
through the command line. Python's 'optparse' module is used to parse the
command line parameters. From these, a 'fake' URL is assembled that is passed
to the WSGI module.

In addition to the web version, the user can specify multiple times and
vertical levels at once, so that, for instance, all forecast valid times
and all vertical levels of a product can be produced with one program
call.

This file is a part of the Mission Support Web Map Service (MSWMS).

USAGE:
======

 Call './mss_wms_cl.py -h' for help.

 Examples:

./mss_wms_cl.py -c EPSG:4326 -i 2011-03-16T00:00:00Z --timeloop=0,243,3
                -l ecmwf_EUR_LL015.PLGeopWind -b 0,30,30,60 -e 250,850
                -o geop -d /path/to/MSS/products/figures

produces plots of all timesteps of the 2011-03-16T00:00:00Z analysis in
a cylindrical projection with corner coordinates 0,30,30,60 for the vertical
levels 250 and 850 hPa. The resulting images will be named geop_lll_ttt.png
(lll for level and ttt for timestep) and be placed in /path/to/MSS/products/figures.


./mss_wms_cl.py -c VERT:LOGP -i 2011-03-16T00:00:00Z -v 2011-03-16T12:00:00Z
                -p 48,11,56,11 -l ecmwf_EUR_LL015.VS_V01 -b 101,1050,10,200
                -o vert1 -d /path/to/mss/figures

produces a vertical section of the horizontal wind between 48N11E and 56N11E,
valid at 2011-03-16T12:00:00Z from the anaylsis at 2011-03-16T00:00:00Z. The
vertical axis of the plot ranges from 1050 hPa to 200 hPa, 101 interpolation
points are used, and 10 labels are places along the x-axis.

Please use the -h option to see all parameters available.


AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
from datetime import datetime, timedelta

import logging
import optparse
import os
import mss_wms_settings
# relatedthird party imports
import numpy as np

# local application imports
from mswms import mss_wms_wsgi
from mslib import mss_config

"""
Main Program
"""

if __name__ == "__main__":

    print "*********************************************************************"
    print "      DLR/IPA Mission Support System WMS Command Line Interface"
    print "*********************************************************************\n"

    # Set up a command line parser.
    parser = optparse.OptionParser()

    # Specify the command line options.
    parser.add_option("-c", "--crs", dest="crs",
                      help="Coordinate reference system of the plot "
                           "to generate. Must be either an EPSG code (for "
                           "codes registered with the system see "
                           "mss_wms_settings.py) or VERT:LOGP for vertical "
                           "sections.", metavar="CRS")
    parser.add_option("-l", "--layer", dest="layer",
                      help="Layer instance to be plotted. Must be the name "
                           "of a layer registered with the WMS.", metavar="LAYER")
    parser.add_option("-s", "--style", dest="style",
                      help="Style of the layer to be plotted, if "
                           "the layer provides styles. ", metavar="STYLE")
    parser.add_option("-i", "--inittime", dest="inittime",
                      help="Initialisation time of the forecast to be used. "
                           "Must be of the format 2011-01-01T00:00:00Z.",
                      metavar="TIME")
    parser.add_option("-v", "--validtime", dest="validtime",
                      help="Valid time of the requested plot. "
                           "Must be of the format 2011-01-01T00:00:00Z.",
                      metavar="TIME")
    parser.add_option("-x", "--width", dest="width",
                      help="Width of the image file to be generated in "
                           "pixels.", metavar="WIDTH")
    parser.add_option("-y", "--height", dest="height",
                      help="Height of the image file to be generated in "
                           "pixels.", metavar="WIDTH")
    parser.add_option("-f", "--frame", action="store_true",
                      dest="frame", default=True,
                      help="Plot figure title and legend outside the data plot.")
    parser.add_option("-t", "--transparent", action="store_true",
                      dest="transparent", default=False,
                      help="Produce a transparent image file.")
    parser.add_option("-b", "--bbox", dest="bbox",
                      help="Bounding box of the figure. For maps this has "
                           "to be a comma separated list of the four corner "
                           "coordinates of the map (LON1,LAT1,LON2,LAT2 where 1 "
                           "and 2 specifiy the lower left and the upper right "
                           "corner of the plot), for vertical sections the "
                           "bounding box sepcifies the four values "
                           "(NINT,PBOT,NLAB,PTOP where NINT and NLAB specify the "
                           "number of interpolation points to be used along the "
                           "vertical section path and the number of labels to be "
                           "to be plotted along the x-axis, and PBOT and PTOP "
                           "specify the botton and top pressure of the section).",
                      metavar="BBOX")
    parser.add_option("-e", "--elevation", dest="elevation",
                      help="(maps only) Specifies the vertical level of the "
                           "dataset to be used. Depending on the layer, the units"
                           "are hPa, model level, potential temperature or "
                           "potential vorticity.\nNOTE that you can also specify "
                           "a comma separated list of vertical levels here, all of "
                           "which will be plotted (e.g. 700,850,925)",
                      metavar="ELEVATION")
    parser.add_option("-p", "--path", dest="path",
                      help="(vertical sections only) Coordinates of the "
                           "points that specify the path along which the vertical "
                           "section shall be plotted. Must be a comma separated "
                           "list LAT1,LON1,LAT2,LON2,... with arbitrarily many "
                           "points. The individual points are connected with "
                           "great circles.", metavar="LAT1,LON1,LAT2,LON2,...")
    parser.add_option("--timeloop", dest="timeloop",
                      help="Loop over valid time to generate a sequence of "
                           "images. Must be a list of three values FROM,TO,STEP "
                           "that specify the forecast steps to be used (starting "
                           "at the intitialisation time). For instance, to "
                           "generate plots of all forecast steps from the analysis "
                           "to forecast step 72 in 3 hour intervals, use the "
                           "parameter 0,72,3. Valid times that are not available "
                           "in the dataset will be ignored.", metavar="FROM,TO,STEP")
    parser.add_option("-o", "--output", dest="output", default="mss",
                      help="Filename prefix of the output file. Vertical "
                           "level or cross-section path and time step will be "
                           "appended.", metavar="PREFIX")
    parser.add_option("-d", "--directory", dest="directory", default="./",
                      help="Output directory. The generated plots will be"
                           "written to a subdirectory specifying the "
                           "initialisation. time.", metavar="DIRECTORY")

    # Get command line arguments.
    (options, args) = parser.parse_args()

    # Initialise a WMS object from mss_wms_wsgi.py.
    print "\nInitialising WMS engine...\n"

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(funcName)19s || %(message)s",
                        datefmt="%H:%M:%S")

    # Initialise the WSGI application.
    wsgi = mss_wms_wsgi.MSS_WMSResponse(mss_config.nwpaccess, address="COMMAND_LINE")

    # Register horizontal section layers.
    for layer, datasets in mss_wms_settings.register_horizontal_layers:
        wsgi.register_hsec_layer(datasets, layer)

    # Register vertical section styles.
    for layer, datasets in mss_wms_settings.register_vertical_layers:
        wsgi.register_vsec_layer(datasets, layer)

    # Check if multiple vertical levels are requested.
    if options.elevation:
        levellist = [int(s) for s in options.elevation.split(",")]
    else:
        levellist = [None]

    # Check if multiple times are requested.
    if options.timeloop:
        timesteps = np.arange(*[int(s) for s in options.timeloop.split(",")])
    else:
        timesteps = [None]

    # Loop over timesteps and vertical levels and produce the plots.
    for timestep in timesteps:
        for level in levellist:

            # Assemble a "fake" query that can be passed to the WSGI object.
            # This query is essentially the same as what would be passed
            # through the URL if we were to make this request from a browser.
            query = "layers=%s" % options.layer
            query += "&styles=%s" % options.style if options.style is not None else ""
            query += "&srs=%s" % options.crs
            query += "&bbox=%s" % options.bbox
            query += "&dim_init_time=%s" % options.inittime
            if timestep is None:
                query += "&time=%s" % options.validtime
            else:
                itime = datetime.strptime(options.inittime, "%Y-%m-%dT%H:%M:%SZ")
                vtime = itime + timedelta(hours=int(timestep))
                query += "&time=%s" % vtime.strftime("%Y-%m-%dT%H:%M:%SZ")

            query += "&format=image/png"
            query += "&request=GetMap"
            query += "&bgcolor=0xFFFFFF"
            query += "&version=1.1.1"
            query += "&exceptions=application/vnd.ogc.se_xml"
            if level:
                query += "&elevation=%i" % level
            if options.height:
                query += "&height=%s" % options.height
            if options.width:
                query += "&width=%s" % options.width
            if options.path:
                query += "&path=%s" % options.path
            query += "&transparent=%s" % ("TRUE" if options.transparent else "FALSE")
            query += "&frame=%s" % ("ON" if options.frame else "OFF")

            # Create a "fake" WSGI environment variable and pass is to the WSGI
            # object. Calling the WSGI will produce the image. (Note that a
            # lambda funtion doing nothing is passed as the start_response
            # function. This is done as we don't require the HTTP headers
            # here).
            wsgi_environ = {"PATH_INFO": "/mss_wms", "QUERY_STRING": query}

            print "Passing query to WMS engine.."
            result = wsgi(wsgi_environ, lambda a, b: None)[0]
            print "\nRetrieved result from WMS engine."

            # If the WSGI object returns a unicode string, this means that
            # an XML document with a service exception has been returned.
            # Display the error message to the user and proceed with
            # the next loop element.
            if type(result) is unicode:
                print "A WMS error occured. The error message is:"
                i = result.find("<ServiceExceptionReport")
                print result[i:]
                print "Use the '-h' option to get help.\n"

            # If no error message was returned, we can assemble the filename
            # store the retireved image file.
            else:
                filename = options.output

                # Add vertical level to the filename, if applicable.
                if level:
                    filename += "_%s" % level

                # Add timestep to the filename.
                itime = datetime.strptime(options.inittime, "%Y-%m-%dT%H:%M:%SZ")
                if timestep is None:
                    vtime = datetime.strptime(options.validtime, "%Y-%m-%dT%H:%M:%SZ")
                    td = vtime - itime
                    timestep = int(td.seconds / 3600 + td.days * 24)
                filename += "_%03i.png" % timestep

                # Join with the directory. Create a subdirectory indicating
                # the initialisation time, if necessary.
                directory = os.path.join(options.directory, itime.strftime("%Y%m%d%H%M"))
                if not os.path.exists(directory):
                    os.mkdir(directory)
                filename = os.path.join(directory, filename)

                # Write the image to disk.
                print "Writing result to file %s." % filename
                f = open(filename, "w")
                f.write(result)
                f.close()
