"""
********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2012 Marc Rautenhaus

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

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports

# related third party imports

# local application imports
from dlraircraft import HALO, Falcon


################################################################################
###                            Aircraft "pool"                               ###
################################################################################

available_aircraft = {}

try:
    halo = HALO()
    available_aircraft[halo.aircraftName] = halo
except:
    pass

try:
    falcon = Falcon()
    available_aircraft[falcon.aircraftName] = falcon
except:
    pass

# NOTE:
# Add your aircraft object here to make it accessible from the user interface.


################################################################################
###                              Example code                                ###
################################################################################

sample_flight_description = [
    ["takeoff_weight", 75000],
    ["takeoff_time", "2012-10-21T12:00:00Z"],
    ["takeoff_location", 11, 48], # elevation determined from psfc
    ["temperature_ISA_deviation", 10],
    ["climb_descent_to", 13, 48, 21000],
    ["cruise_to", 15, 50, "LRC"], # FL remains unchanged
    ["climb_descent_to", 13, 49, 11000],
    ["land_at", 11, 48],
    ]

#halo.fly(sample_flight_description)
#falcon.fly(sample_flight_description)
