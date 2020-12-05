# About


The Mission Support System (MSS) is a software that is written by
scientists in the field of atmospheric science. The purpose is to have a
tool that simplifies the process for planning a scientific flight in
which parameters of the atmosphere are measured. The research aircrafts
typically carry a comprehensive scientific payload comprised of data
aquisition instruments by different companies and research institutions.
The measurement of relevant parameters, for example the chemical
composition of trace gases, temperature or aerosol particle
characteristics, are needed to improve the scientific understanding of
the processes in the atmosphere. This is of significant importance for
the understanding for example of climate change or the recovery of the
ozone hole.

Typically, scientific research flights are conducted to answer different
scientific questions. Forecasts of relevant parameters by a model
simulation for a specific location give hints where to fly, to answer
the scientific questions by measurements. A lot of other conditions
apply to research flights, that concern flight altitude and range,
ambient temperature, flight permissions in different flight information
regions and aircraft traffic routes.

> ![image](../mss_theme/img/wise12_overview.png)

MSS helps to optimize the scientific outcome of the research flights by
displaying the planned flight route and the corresponding model
parameters in the same platform for many discussed options. It does
therefore reduce somehow the amount of flight hours that is needed to
answer a scientific question and thus saves in the end taxpayers money.
In detail, this software helps to review a big amount of meteorological
and model data by viewing the forecasted parameters of interest along
possible regions of a proposed flight path. Data and possible flight
paths can be displayed on a horizontal view (map projection) or on a
vertical view (along the proposed flight path). Flight paths can be
constructed and modified on these views. Exchange through a waypoint
table is also possible.

MSS is a client/server application written in the language **Python**.
This is used to create flight plans and discuss these with pilots of
research aircraft. The flight path is designed by local and remote
scientists based on meteorologic forecast data on the QT5 MSS gui
application. A [publication by Rautenhaus et
al.](http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012.pdf)
summarizes the principle of this software. On the EuroPython conference
a [overview
talk](https://pyvideo.org/europython-2017/mss-software-for-planning-research-aircraft-missions.html)
about MSS was held.

The MSS software includes a template for a Webmap server providing own
model data, but it can also connect to several Open Web Service (OWS)
data providers. The architecture of the software package enables its use
in countries with a poor internet connection. For our atmospheric
measurements, one often has to go to remote regions that lack high speed
internet.

MSS is developed and used mainly by scientists of various institutions
involved in scientific aircraft based missions, including universities
and the German research institutions DLR, KIT, and Forschungszentrum
Jülich. Improving the software will improve the quality of the research
flights and will also enable its use for other scientific areas, e.g.
planning of ship routes.

> -   [Getting started](https://github.com/Open-MSS/MSS/wiki/Getting-Started)
> -   [Contact](https://github.com/Open-MSS/MSS/wiki/Contact)

