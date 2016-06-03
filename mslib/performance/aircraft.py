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

TODO:
=====

* consider wind forecasts during climb and descent segments (2012Nov13, mr)
* estimate airport elevations from p_sfc forecast field (2012Nov13, mr)

"""

# standard library imports
import os
import logging
import copy
from datetime import datetime, timedelta
from abc import ABCMeta, abstractmethod, abstractproperty
import time as ptime

# related third party imports
import numpy as np
from geopy import distance

# local application imports
from mslib import thermolib

"""
EXCEPTION CLASSES
"""


class FlightError(Exception):
    """Exception class to handle errors occuring during flight performance
    computations.
    """
    pass


"""
AIRCRAFT STATE
"""


class AircraftState(object):
    """This class describes the state of an aircraft, including its position,
    altitude, time, consumed fuel etc. When computing the flight performance of
    a flight track, the Aircraft class assembles a list of these state
    objects. The list can be obtained by the caller for analysis after the
    computations have finished.
    """
    # Identification number of this state object (usually corresponds to the
    # current waypoint number).
    stateID = None
    # Position.
    lon = None
    lat = None
    alt_ft = None  # altitude in ft
    # Speed: True airspeed in knots and a string desribing the current flight
    # mode and speed (e.g. "LRC 488 kn").
    tas_kn = 0.
    speed_desc = ""
    # Fuel consumption and aircraft weight (all in lbs).
    fuel_since_last_state_lbs = 0.
    fuel_since_takeoff_lbs = 0.
    grossweight = None
    # Approximate remaining fuel and remaining range with default cruise mode.
    remaining_fuel_lbs = None
    remaining_range_default_cruise_nm = None
    # Time (as datetime and timedelta objects).
    time_utc = None
    timedelta_since_last_state = timedelta(0)
    timedelta_since_takeoff = timedelta(0)
    # Distance.
    distance_since_last_state_nm = 0.
    distance_since_takeoff_nm = 0.
    # Status variables.
    in_flight = False
    has_landed = False


"""
AIRCRAFT
"""


class Aircraft(object):
    """Abstract superclass for all aircraft classes.
    """
    __metaclass__ = ABCMeta

    # These public attributes need to be overwritten in derived class.
    aircraftName = "Abstract Aircraft"
    maximumTakeoffWeight_lbs = -1
    fuelCapacity_lbs = -1
    maximumCruiseAltitude_ft = -1
    defaultCruiseAltitude_ft = -1
    availableCruiseModes = ["None"]
    defaultCruiseMode = "None"
    availableConfigurations = ["None"]
    defaultConfiguration = "None"
    availablePerformanceTableInterpretations \
        = ["conservative", "interpolation"]
    availableErrorHandlingModes \
        = ["strict", "warning", "permissive"]

    # Protected attributes.
    _configuration = "None"
    _performanceTableInterpretation = "conservative"
    _errorHandling = "strict"
    _ac_state_list = []

    def selectConfiguration(self, config):
        """Select an aircraft configuration from one of the configurations in
        "availableConfigurations".
        """
        if config in self.availableConfigurations:
            self._configuration = config
        else:
            raise ValueError("unknown configuration: %s" % config)

    def setPerformanceTableInterpretation(self, interpretation):
        """Set the performance table interpretation to one of "conservative" and
        "interpolation". "conservative" does not interpolate between lookup
        table values, instead always uses the worse values.
        """
        if interpretation in self.availablePerformanceTableInterpretations:
            self._performanceTableInterpretation = interpretation
        else:
            raise ValueError("unknown interpretation mode: %s" % interpretation)

    def setErrorHandling(self, handling):
        """Set the error handling (e.g. when the distance between two waypoints
        is too short for a specified climb) to one of the modes in
        "availableErrorHandlingModes".
        """
        if handling in self.availableErrorHandlingModes:
            self._errorHandling = handling
        else:
            raise ValueError("unknown error handling mode: %s" % handling)

    @abstractmethod
    def climbPerformance(self, altitude, deltatemp, grossweight,
                         use_next_lower_altitude=False):
        """This abstract method needs to be implemented in a derived class.
        
        Climb performance of the aircraft. Returns time [min], distance [nm] and
        fuel [lbs] required for a climb from sea level to the specified
        altitude.

        Arguments:
        altitude    -- altitude in ft to climb to
        deltatemp   -- temperature deviation off ISA conditions in K
        grossweight -- total weight of the aircraft in lbs
        use_next_lower_altitude
                    -- if performance table interpretation has been set to 
                       "conservative", setting this arg to True will result
                       in the performance values of the next lower altitude
                       level listed in the performance table being returned
                       (default is True, so that the values of the next
                       higher level are returned).
        """
        pass

    @abstractmethod
    def cruisePerformance(self, cruisemode, altitude, deltatemp, grossweight):
        """This abstract method needs to be implemented in a derived class.
        
        Cruise performance of the aircraft. Returns true airspeed [knots] and
        fuelflow [lbs/hr] required for a cruise at the specified altitude.

        Arguments:
        cruisemode  -- one of the values in "availableCruiseModes"
        See climbPerformance().
        """
        pass

    @abstractmethod
    def descentPerformance(self, altitude, deltatemp, grossweight,
                           use_next_lower_altitude=False):
        """This abstract method needs to be implemented in a derived class.
        
        Descent performance of the aircraft. Returns time [min], distance [nm]
        and fuel [lbs] required for a climb from sea level to the specified
        altitude.

        Arguments: See climbPerformance().
        """
        pass

    def fly(self, flight_description, nwp_data=None, eps=1e-08):
        """Performs the performance computation. "flight_description" needs to be
        a list of "flight commands" that take the form

        flight_description = [
            ["takeoff_weight", 75000],
            ["takeoff_time", "2012-10-21T12:00:00Z"],
            ["takeoff_location", 11, 48], # elevation determined from psfc
            ["temperature_ISA_deviation", 10],
            ["climb_descent_to", 13, 48, 21000],
            ["cruise_to", 15, 48, "LRC"], # FL remains unchanged
            ["climb_descent_to", 13, 48, 11000],
            ["land_at", 11, 48],
        ]

        The flight performance is computed with an "aircraft state machine" that
        is updated with every command in "flight_description". Error handling
        depends in the mode set with setErrorHandling().

        "nwp_data" is an optional dictionary containing weather forecast data
        interpolated to a 2D curtain along the flight route. This means that all
        waypoints listed in the "flight_description" need to be contained in the
        NWP data curtains. If "nwp_data" is None, the performance computation is
        carried out with a zero-wind-assumption. "nwp_data" is assumed to have
        the following structure:

        nwp_data[time][variable] = 1D/2D numpy array

        where "time" is a datetime object and "variable" must include "lon",
        "lat" (both 1D arrays) and "air_pressure", "air_temperature",
        "eastward_wind" and "northward_wind" (2D curtains).

        NOTE: Currently wind information is only considered for cruise segments!
        """
        # Status object of the aircraft.
        ac_state = AircraftState()
        delta_temp_ISA = 0.

        # Initialize a list of AircraftState objects that will be filled "during
        # the flight".
        self._ac_state_list = []

        # Compute the minimum aircraft weight (for fuel checks below).
        min_weight_lbs = self.maximumTakeoffWeight_lbs - self.fuelCapacity_lbs

        # Index pointer that points to the current position in the "nwp_data"
        # curtains. This variable is only needed if "nwp_data" is not None.
        nwp_index = 0

        # If "nwp_data" is defined copy the lon/lat arrays (from the first
        # timestep, they should be the same for all timesteps), as they will be
        # used frequently.
        nwp_lon = nwp_data[nwp_data.keys()[0]]["lon"] if nwp_data else None
        nwp_lat = nwp_data[nwp_data.keys()[0]]["lat"] if nwp_data else None

        # Similarly, get a copy of the available timesteps. Convert the list
        # into a numpy array to be able to use the searchsorted() function
        # below.
        nwp_available_times = np.array(nwp_data.keys()) if nwp_data else np.array([])
        nwp_available_times.sort()

        # Process all flight commands in flight_description.
        for item in flight_description:

            print "processing command %s." % item

            command = item[0]

            # takeoff_weight
            # ==================================================================
            if command == "takeoff_weight":
                if ac_state.grossweight is None:
                    ac_state.grossweight = item[1]
                else:
                    self._flyWarn("takeoff weight has already been defined.")

            # takeoff_time
            # ==================================================================
            elif command == "takeoff_time":
                if ac_state.time_utc is None:
                    ac_state.time_utc = datetime.strptime(item[1],
                                                          "%Y-%m-%dT%H:%M:%SZ")
                else:
                    self._flyWarn("takeoff time has already been defined.")

            # takeoff_location
            # ==================================================================
            elif command == "takeoff_location":
                if ac_state.lon is None:
                    ac_state.lon = item[1]
                    ac_state.lat = item[2]
                    # TODO: takeoff elevation
                    ac_state.alt_ft = 0
                    ac_state.stateID = 0
                else:
                    self._flyWarn("takeoff location has already been defined.")

            # temperature_ISA_deviation
            # ==================================================================
            elif command == "temperature_ISA_deviation":
                delta_temp_ISA = item[1]

            # climb_descent_to, land_at
            # ==================================================================
            elif command == "climb_descent_to" or command == "land_at":
                if ac_state.lon is None:
                    self._flyWarn("no position has been defined before.")
                    continue

                segment_info = "concerning the segment between waypoints %i " \
                               "(%.2f/%.2f) and %i (%.2f/%.2f) -- " % \
                               (ac_state.stateID, ac_state.lat, ac_state.lon,
                                ac_state.stateID + 1, item[2], item[1])

                # If the aircraft hasn't started yet, save the state just before
                # takeoff.
                if not ac_state.in_flight:
                    self._ac_state_list.append(copy.deepcopy(ac_state))

                # If NWP data is available update the temperature deviation from
                # ISA conditions (wind is not considered for climb/descent).
                if nwp_data:
                    delta_temp_ISA, tail_wind_kn = self._metConditionsAtCurrentPos(
                        nwp_data, nwp_available_times, nwp_lon, nwp_lat,
                        nwp_index, ac_state.time_utc, ac_state.alt_ft)

                ac_state.stateID += 1
                ac_state.in_flight = True  # aircraft is in the air

                current_elevation_ft = ac_state.alt_ft
                if command == "climb_descent_to":
                    target_elevation_ft = item[3]
                    # The aircraft first climbs/descents, additionally required
                    # cruise parts are performed on the target altitude.
                    cruise_elevation_ft = target_elevation_ft
                else:  # (command == "land_at")
                    # TODO: landing elevation
                    target_elevation_ft = 0
                    # The aircraft first performs additional cruise segments,
                    # then descents to the target airport.
                    cruise_elevation_ft = current_elevation_ft

                if target_elevation_ft == current_elevation_ft:
                    self._flyWarn(
                        segment_info +
                        "requested elevation is equal to last elevation, "
                        "please use 'cruise_to' instead.")
                    continue

                if target_elevation_ft > current_elevation_ft:
                    # Climb.
                    action = "climb"
                    # If the performance table interpretation mode is
                    # "conservative", the "use_next_lower_altitude" keyword will
                    # make sure that not the same values are retrieved from the
                    # table for both elevations (cf. notes 06Nov2012).
                    time1, dist1, fuel1 = self.climbPerformance(
                        current_elevation_ft, delta_temp_ISA, ac_state.grossweight,
                        use_next_lower_altitude=True)
                    time2, dist2, fuel2 = self.climbPerformance(
                        target_elevation_ft, delta_temp_ISA, ac_state.grossweight,
                        use_next_lower_altitude=False)
                else:
                    # Descent.
                    action = "descent"
                    # NOTE: For conservative mode, altitude levels are selected
                    # such that descent time is UNDERESTIMATED (from next lower
                    # level of current altitude to next upper level of target
                    # altitude). This way, more cruise time is added, which
                    # results in a longer total time and higher fuel consumption
                    # of this segment.
                    time1, dist1, fuel1 = self.descentPerformance(
                        target_elevation_ft, delta_temp_ISA, ac_state.grossweight,
                        use_next_lower_altitude=False)
                    time2, dist2, fuel2 = self.descentPerformance(
                        current_elevation_ft, delta_temp_ISA, ac_state.grossweight,
                        use_next_lower_altitude=True)

                # print time1, dist1, fuel1
                # print time2, dist2, fuel2

                time = time2 - time1  # time in minutes
                dist = dist2 - dist1
                fuel = fuel2 - fuel1

                print "%s requires %.2f min, a distance of %.2f nm and %.2f lbs fuel." % \
                      (action, time, dist, fuel)

                # Update flight time and aircraft weight for climb/descent.
                ac_state.time_utc += timedelta(seconds=60 * time)
                ac_state.grossweight -= fuel
                ac_state.timedelta_since_last_state = timedelta(seconds=60 * time)
                ac_state.timedelta_since_takeoff += timedelta(seconds=60 * time)
                ac_state.fuel_since_last_state_lbs = fuel
                ac_state.fuel_since_takeoff_lbs += fuel

                ac_state.speed_desc = action

                # Compute the greatcircle distance between waypoints in nautical
                # miles.
                segment_distance_nm = distance.distance(
                    (ac_state.lat, ac_state.lon), (item[2], item[1])).nm
                print "given segment distance is %f nm." % segment_distance_nm

                if dist > segment_distance_nm:
                    self._flyWarn(
                        segment_info +
                        "to reach the requested altitude of %i ft a "
                        "distance of %.2f nm is required, however, "
                        "the distance between the two waypoints "
                        "is only %.2f nm." %
                        (target_elevation_ft, dist, segment_distance_nm))
                else:
                    remaining_distance_nm = segment_distance_nm - dist

                    tas, fuelflow = self.cruisePerformance(
                        self.defaultCruiseMode, target_elevation_ft,
                        delta_temp_ISA, ac_state.grossweight)

                    time_h = remaining_distance_nm / tas  # tas in kn
                    fuel = fuelflow * time_h  # fuelflow in lbs/h

                    # Update flight time and aircraft weight for cruise.
                    ac_state.time_utc += timedelta(seconds=3600 * time_h)
                    ac_state.grossweight -= fuel
                    ac_state.timedelta_since_last_state += timedelta(seconds=3600 * time_h)
                    ac_state.timedelta_since_takeoff += timedelta(seconds=3600 * time_h)
                    ac_state.fuel_since_last_state_lbs += fuel
                    ac_state.fuel_since_takeoff_lbs += fuel

                    ac_state.speed_desc += " + " + self.defaultCruiseMode

                    print "additional cruise of %.2f min (%s) requires %.2f lbs fuel." % \
                          (time_h * 60, self.defaultCruiseMode, fuel)

                ac_state.lon = item[1]
                ac_state.lat = item[2]
                ac_state.alt_ft = target_elevation_ft
                ac_state.distance_since_last_state_nm += segment_distance_nm
                ac_state.distance_since_takeoff_nm += segment_distance_nm
                if command == "land_at":
                    ac_state.has_landed = True
                    ac_state.in_flight = False

                # If "nwp_data" is defined advance the index pointer to the
                # current position.
                if nwp_data:
                    nwp_index += 1  # advance at least one point
                    # while (ac_state.lon != nwp_lon[nwp_index]) \
                    #         and (ac_state.lat != nwp_lat[nwp_index]):
                    while abs(ac_state.lon - nwp_lon[nwp_index]) > eps \
                            and abs(ac_state.lat - nwp_lat[nwp_index]) > eps:
                        nwp_index += 1
                        if nwp_index >= len(nwp_lon):
                            self._flyWarn(
                                segment_info +
                                "cannot find the point %.2f/%.2f in the "
                                "NWP curtain." % (ac_state.lon, ac_state.lat))

            # cruise_to
            # ==================================================================
            elif command == "cruise_to":
                if ac_state.lon is None:
                    self._flyWarn("no position has been defined before.")
                    continue

                # Compute the greatcircle distance between waypoints in nautical
                # miles.
                segment_distance_nm = distance.distance(
                    (ac_state.lat, ac_state.lon), (item[2], item[1])).nm
                print "given segment distance is %f nm." % segment_distance_nm

                if nwp_data is None:
                    # No meteorological forecast data is available. Use ground
                    # speed = true airspeed and the given delta_temp_ISA.
                    tas, fuelflow = self.cruisePerformance(
                        item[3], ac_state.alt_ft, delta_temp_ISA, ac_state.grossweight)

                    time_h = segment_distance_nm / tas  # tas in kn
                    fuel = fuelflow * time_h  # fuelflow in lbs/h

                else:
                    # Meteorological data is available. Loop over all
                    # sub-segments in the data curtain to get a best possible
                    # estimation of the influence of wind and temperature on the
                    # performance.

                    next_wp_lon = item[1]
                    next_wp_lat = item[2]

                    time_h = 0.
                    fuel = 0.

                    _time_utc = copy.deepcopy(ac_state.time_utc)

                    while True:
                        # Compute the temperature deviation from ISA conditions
                        # and the wind speed in flight direction at the current
                        # aircraft position and time (i.e. the position at the
                        # beginning of the current sub-segment).
                        delta_temp_ISA, tail_wind_kn = self._metConditionsAtCurrentPos(
                            nwp_data, nwp_available_times, nwp_lon, nwp_lat,
                            nwp_index, _time_utc, ac_state.alt_ft)

                        # True airspeed and fuelflow for current temperature
                        # conditions.
                        tas, fuelflow = self.cruisePerformance(
                            item[3], ac_state.alt_ft, delta_temp_ISA, ac_state.grossweight)

                        # Compute the length of the current sub-segment ..
                        sub_segment_distance_nm = distance.distance(
                            (nwp_lat[nwp_index], nwp_lon[nwp_index]),
                            (nwp_lat[nwp_index + 1], nwp_lon[nwp_index + 1])).nm

                        # .. and from TAS and tail wind the groundspeed.
                        groundspeed_kn = tas + tail_wind_kn  # tas in kn
                        sub_time_h = sub_segment_distance_nm / groundspeed_kn
                        time_h += sub_time_h
                        fuel += fuelflow * sub_time_h  # fuelflow in lbs/h

                        # Update time "pointer" for forecast interpolation.
                        _time_utc += timedelta(seconds=3600 * sub_time_h)

                        # Increment the pointer into the sub-segment points. If
                        # the target position of this flight segment has been
                        # reached, stop the loop.
                        nwp_index += 1

                        if nwp_index >= len(nwp_lon) - 1:
                            self._flyWarn("cannot find the point %.2f/%.2f in the "
                                          "NWP curtain." % (next_wp_lon, next_wp_lat))
                            break

                        # print abs(nwp_lon[nwp_index] - next_wp_lon), abs(nwp_lat[nwp_index] - next_wp_lat)
                        # if (nwp_lon[nwp_index] == next_wp_lon) \
                        #         and (nwp_lat[nwp_index] == next_wp_lat): break
                        if abs(nwp_lon[nwp_index] - next_wp_lon) < eps \
                                and abs(nwp_lat[nwp_index] - next_wp_lat) < eps: break

                # Update flight time and aircraft weight.
                ac_state.stateID += 1
                ac_state.time_utc += timedelta(seconds=3600 * time_h)
                ac_state.grossweight -= fuel
                ac_state.timedelta_since_last_state = timedelta(seconds=3600 * time_h)
                ac_state.timedelta_since_takeoff += timedelta(seconds=3600 * time_h)
                ac_state.fuel_since_last_state_lbs = fuel
                ac_state.fuel_since_takeoff_lbs += fuel

                # print "cruise with true airspeed of %.2f kn (ground speed %.2f "\
                #     "kn) takes %.2f min (%s) and requires %.2f lbs fuel." % \
                #     (tas, groundspeed_kn, time_h*60, self.defaultCruiseMode, fuel)
                print "cruise takes %.2f min (%s) and requires %.2f lbs fuel." % \
                      (time_h * 60, self.defaultCruiseMode, fuel)

                ac_state.lon = item[1]
                ac_state.lat = item[2]
                ac_state.distance_since_last_state_nm = segment_distance_nm
                ac_state.distance_since_takeoff_nm += segment_distance_nm

                ac_state.speed_desc = item[3]

            # ==================================================================

            if command in ["cruise_to", "climb_descent_to", "land_at"]:
                # Update remaining fuel ..
                ac_state.remaining_fuel_lbs = ac_state.grossweight - min_weight_lbs
                # .. and remaining distance ..
                tas, fuelflow = self.cruisePerformance(
                    self.defaultCruiseMode, 25000,
                    delta_temp_ISA, ac_state.grossweight)
                # .. remaining flight hours with current fuel flow ..
                time_h = ac_state.remaining_fuel_lbs / fuelflow
                # .. lead to an approximate remaining distance (without wind) ..
                ac_state.remaining_range_default_cruise_nm = tas * time_h

                # Save the current aircraft status.
                self._ac_state_list.append(copy.deepcopy(ac_state))

            # Print current aircraft status.
            print "aircraft status   -- TIME: %s WEIGHT: %.2f POSITION: " \
                  "(%.2f/%.2f at %.2f ft) MAX. REMAINING FUEL/RANGE@FL250: %.2f lbs / %.2f nm" % \
                  (ac_state.time_utc.strftime("%Y-%m-%dT%H:%M:%SZ") if ac_state.time_utc else "",
                   ac_state.grossweight if ac_state.grossweight else 0.,
                   ac_state.lat if ac_state.lat is not None else -999.,
                   ac_state.lon if ac_state.lon is not None else -999.,
                   ac_state.alt_ft if ac_state.alt_ft is not None else -999.,
                   ac_state.remaining_fuel_lbs if ac_state.remaining_fuel_lbs is not None else -999.,
                   ac_state.remaining_range_default_cruise_nm
                   if ac_state.remaining_range_default_cruise_nm is not None else -999.)
            print "atmosphere status -- TEMPERATURE: %.2f K off ISA\n" % \
                  (delta_temp_ISA)

            # Stop this loop if the maximum available fuel has been used up.
            if ac_state.remaining_fuel_lbs is not None and ac_state.remaining_fuel_lbs <= 0.:
                self._flyWarn(
                    "no fuel left at waypoint %i, current aircraft weight "
                    "(%.2f lbs) has fallen below minimum aircraft "
                    "weight of %.2f lbs." %
                    (ac_state.stateID, ac_state.grossweight, min_weight_lbs))

            # Stop this loop if the aircraft has touched down at the target
            # airport.
            if ac_state.has_landed:
                print "aircraft has reached target airport, stopping " \
                      "performance computation."
                break

    def _flyWarn(self, issue):
        """Issue a warning/error for the performance computation.
        """
        print "WARNING: %s" % issue
        if self._errorHandling == "strict":
            print "-- Stopping performance computation."
            raise FlightError(issue)
        else:
            print "-- Skipping this flight command."

    def getLastAircraftStateList(self):
        """Returns the list of aircraft states of the last performance
        computation.
        """
        return self._ac_state_list

    def initialCourseBetweenPoints(self, lon1, lat1, lon2, lat2,
                                   in_degrees=True, eps=1e-08):
        """Computes the initial course, tc1 (at point 1), when flying from point
        1 to point 2 along a great circle.

        Formula taken from Ed Williams' "Aviation Formulary V1.46":
                        http://williams.best.vwh.net/avform.htm#Crs
        """
        # If the point coordinates are given in degrees, convert to radians.
        if in_degrees:
            lon1 = lon1 * np.pi / 180.
            lat1 = lat1 * np.pi / 180.
            lon2 = lon2 * np.pi / 180.
            lat2 = lat2 * np.pi / 180.

        # The formula from the web page assumes that western longitudes are
        # positive, here we use western longitudes as negative numbers.
        lon1 = -lon1
        lon2 = -lon2

        # The formula fails if the initial point is a pole. We can special case
        # this with:
        if np.cos(lat1) < eps:
            if lat1 > 0:
                tc1 = np.pi
            else:
                tc1 = 2 * np.pi

        # For starting points other than the poles:
        else:
            tc1 = np.mod(
                np.arctan2(np.sin(lon1 - lon2) * np.cos(lat2),
                           np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lon1 - lon2)),
                2 * np.pi
            )

        if in_degrees:
            tc1 = tc1 / np.pi * 180.

        return tc1

    def _metConditionsAtCurrentPos(self, nwp_data, nwp_available_times,
                                   nwp_lon, nwp_lat,
                                   nwp_index, time_utc, alt_ft):
        """Computes the temperature deviation from ISA conditions and the
        tailwind for the segment [nwp_index .. nwp_index+1] at time_utc and
        alt_ft.
        """
        # If "nwp_data" is defined compute the temperature deviation from ISA
        # conditions and the wind speed in flight direction at the current
        # aircraft position and time (i.e. the position at the beginning of the
        # current segment).
        if nwp_data:

            if nwp_index >= len(nwp_lon) - 2:
                self._flyWarn(
                    "unexpected end of forecast data curtain -- this should "
                    "not happen if NWP data and flight description have "
                    "been generated by the performance control -- "
                    "please send a bug report to the developer")

            # Determine the two timesteps that enclose the current time.
            i = nwp_available_times.searchsorted(time_utc)
            if nwp_available_times[i] > time_utc:
                i = max(i - 1, 0)
            time_before = nwp_available_times[i]
            time_after = nwp_available_times[min(i + 1, len(nwp_available_times) - 1)]

            # Compute the ln(p) column at the current position for both
            # timesteps. Determine whether the data is stored in ascending or
            # descending order (np.interp requires them to be stored in
            # ascending order).
            ln_p_before = np.log(nwp_data[time_before]["air_pressure"][:, nwp_index])
            ln_p_after = np.log(nwp_data[time_after]["air_pressure"][:, nwp_index])
            v_order = 1 if ln_p_before[0] < ln_p_before[-1] else -1
            ln_p_before = ln_p_before[::v_order]
            ln_p_after = ln_p_after[::v_order]

            # Get the pressure of the current aircraft altitude.
            ac_ln_p = np.log(thermolib.flightlevel2pressure(alt_ft / 100.))

            # Get the temperature column at the current position for the two
            # timesteps, then interpolate linearly to the aircraft pressure.
            T_before = nwp_data[time_before]["air_temperature"][::v_order, nwp_index]
            T_after = nwp_data[time_after]["air_temperature"][::v_order, nwp_index]
            ac_T_before = np.interp(ac_ln_p, ln_p_before, T_before)
            ac_T_after = np.interp(ac_ln_p, ln_p_after, T_after)

            # The same with eastward and northward wind.
            U_before = nwp_data[time_before]["eastward_wind"][::v_order, nwp_index]
            U_after = nwp_data[time_after]["eastward_wind"][::v_order, nwp_index]
            ac_U_before = np.interp(ac_ln_p, ln_p_before, U_before)
            ac_U_after = np.interp(ac_ln_p, ln_p_after, U_after)
            V_before = nwp_data[time_before]["northward_wind"][::v_order, nwp_index]
            V_after = nwp_data[time_after]["northward_wind"][::v_order, nwp_index]
            ac_V_before = np.interp(ac_ln_p, ln_p_before, V_before)
            ac_V_after = np.interp(ac_ln_p, ln_p_after, V_after)

            # Convert the times into second since epoch to interpolate linearly
            # in time.
            timestamp_before = ptime.mktime(time_before.timetuple())
            timestamp_after = ptime.mktime(time_after.timetuple())
            ac_timestamp = ptime.mktime(time_utc.timetuple())

            # Interpolate in time.
            ac_T = np.interp(ac_timestamp, [timestamp_before, timestamp_after],
                             [ac_T_before, ac_T_after])
            ac_U = np.interp(ac_timestamp, [timestamp_before, timestamp_after],
                             [ac_U_before, ac_U_after])
            ac_V = np.interp(ac_timestamp, [timestamp_before, timestamp_after],
                             [ac_V_before, ac_V_after])

            print "\tmeteorological conditions at current position " \
                  "(%.2f/%.2f, %.2f ft = %.2f hPa) at %s: T = %.2f K, " \
                  "U = %.2f m/s, V = %.2f m/s" % \
                  (nwp_lon[nwp_index], nwp_lat[nwp_index],
                   alt_ft, np.exp(ac_ln_p) / 100.,
                   time_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   ac_T, ac_U, ac_V)

            # Compute temperature deviation from ISA.
            isa_T = thermolib.isa_temperature(alt_ft / 100.)
            delta_temp_ISA = ac_T - isa_T
            print "\ttemperature deviation from ISA conditions: %.2f K" % delta_temp_ISA

            # Compute the aircraft's heading in degrees, as well es the wind
            # direction, wind speed and the angle between aircraft heading and
            # wind direction. To compute the aircraft heading, use the
            # coordinates from nwp_lon/lat.
            ac_heading = self.initialCourseBetweenPoints(nwp_lon[nwp_index],
                                                         nwp_lat[nwp_index],
                                                         nwp_lon[nwp_index + 1],
                                                         nwp_lat[nwp_index + 1])
            wind_direction = (np.arctan2(ac_U, ac_V) * 180. / np.pi) % 360.
            wind_speed = np.sqrt(ac_U ** 2 + ac_V ** 2)
            angle_ac_wind = ac_heading - wind_direction

            # From these values the tail wind can be computed with a cosine.
            tail_wind_ms = wind_speed * np.cos(angle_ac_wind / 180. * np.pi)
            tail_wind_kn = tail_wind_ms * 3.6 / 1.852
            print "\taircraft heading is %.2f degrees, wind direction is " \
                  "%.2f degrees, wind speed is %.2f m/s, tail wind is " \
                  "%.2f m/s = %.2f kn" % \
                  (ac_heading, wind_direction, wind_speed, tail_wind_ms, tail_wind_kn)

            return delta_temp_ISA, tail_wind_kn

        else:
            # No NWP data defined?
            return 0., 0.
