=============================
mss - KML Overlay Dock Widget
=============================


KML Overlay Docking Widget
==========================

The TopView has a docking widget that allows the visualization of KML files on top of the map.

This feature supports all *essential* elements of KML relevant to MSS' usage namely:

* Placemarks (*present in Folder/ Document or otherwise*)
* Style (LineStyle & PolyStyle)
* Geometries defined in KML such as :  
   - Point
   - LineString
   - LinearRing
   - Polygon (*Inner and Outer Rings*)
   - MultiGeometries (*MultiPoint, MultiLineString, MultiPolygon*)
   - Geometry Collection (*combination of various types of MultiGeometries*)


The KML Support has been enhanced to parse all legal KML Files without crashing, and a clear visualization 
on the map, with the relevant geometries and styles.

The KML Interface now supports display of multiple KML Files simultaneously, with easy to use Buttons such 
as 'Add KML Files', 'Remove File' and 'Remove All' for the user's benefit.

A Check/ Uncheck feature allows users to display/hide individual plots on the map, at the User's leisure.

A **KML Customize Option** improves the User Experience by allowing user to customize the colour & linewidth
of each of the KML Files displayed, realtime. This allows for better understanding of the map and the plots.
(*The Customize Option can be accessed for each file, by double clicking on the name of that file in the list.*)

The 'Merge KML Files' Button allows users to combine all the displayed plotted files, to be *combined* into a 
single KML File 'output.kml', which will be present in the last working directory of the user.


*Have to head out somewhere? Important KML Files open?*
Close the software with ease of mind. Next time you open your software, all your work will be present, right where
you left it! KML Overlay supports **Saving Open files** so that you can jump back in, anytime!


Test Samples
------------

Curious to test out some KML Files? We have a sample collection ready just for this!

Example KML Files are located at : 

* Displays LineString
:download: `docs/samples/kml/line.kml <samples/kml/line.kml>`

* Displays Point & Polygon
:download: `docs/samples/kml/folder.kml <samples/kml/folder.kml>`

* Displays Polygon
:download: `docs/samples/kml/color.kml <samples/kml/color.kml>`

* Displays Style (*The green blob with the Airport*)
:download: `docs/samples/kml/style.kml <samples/kml/style.kml>`

* Displays Area in South America (*Points, LineStrings, Polygons*)
:download: `docs/samples/kml/features.kml <samples/kml/features.kml>`

* Displays the World Map (*MultiPolygon*)
:download: `docs/samples/kml/World_Map.kml <samples/kml/World_Map.kml>`

* Displays Square Fractal plot in North America (*Polygon Rings*)
:download: `docs/samples/kml/polygon_inner.kml <samples/kml/polygon_inner.kml>`

* Displays Fork like pattern in Ireland (*MultiLineStrings*)
:download: `docs/samples/kml/Multilinestrings.kml <samples/kml/Multilinestrings.kml>`

* Displays Geometry Collection in Adelaide, Australia
:download: `docs/samples/kml/geometry_collection.kml <samples/kml/geometry_collection.kml>`



