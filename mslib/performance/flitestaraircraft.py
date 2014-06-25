"""
********************************************************************************

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
import logging
import re

# related third party imports
import numpy as np

# local application imports
from aircraft import Aircraft


################################################################################
###                          FLITESTAR AIRCRAFT                              ###
################################################################################

class FliteStarExportedAircraft(Aircraft):
    """Intermediate, still abstract, Aircraft class that can be used as
    superclass for Aircraft derivatives that use FliteStar-exported performance
    data for their computations. This class' constructor reads the performance
    sections from a FliteStar file.
    """

    def __init__(self, performancefile):
        """Reads the performance sections from the "performancefile", which is a
        textfile with performance data exported by FliteStar.
        """
        self._performanceTables = {}    # filled below
        self._performanceTableKeys = {} # to be defined in subclass

        # Read the textfile exported by FliteStar into memory.
        performancefile_object = open(performancefile)
        performancefile_lines  = performancefile_object.readlines()
        performancefile_object.close()

        # Scan the file for performance sections. Each performance section
        # starts with a header of format "[Corporate Model .. aircraft and mode
        # ..]". Create a table with performance values for each section and
        # store this table in self._performanceTables.
        r = re.compile("\[Corporate Model.*\]")
    
        i = 0
        while (i < len(performancefile_lines)):
            line = performancefile_lines[i]
            i += 1

            if r.match(line):
                # Match -- create a new table.
                section = line.strip() # remove trailing whitespace
                self._performanceTables[section] = {"data": []}
                # The line following the section header contains the names of
                # the columns in the table that follows. Example: "# weight,
                # temp, alt, time, distance, fuel". Again, remove trailing
                # whitespace and remove the "# " at the beginning.
                column_header = performancefile_lines[i].strip()[2:]
                i += 1
                # The "columns" entry now becomes, for example, ['weight',
                # 'temp', 'alt', 'time', 'distance', 'fuel'].
                self._performanceTables[section]["columns"] = column_header.split(", ")
                # The following lines contain the performance data as
                # comma-separated float values. The performance section ends
                # when an empty line is encountered.
                while (i < len(performancefile_lines)):
                    line = performancefile_lines[i].strip()
                    i += 1
                    if (line == ""): break
                    self._performanceTables[section]["data"].append(
                        [float(v) for v in line.split(", ")])


    def _generatePerformanceDict(self, table_keys, target_dict, 
                                 insert_zero_values=False):
        """Takes the entries in self._performanceTables that are listed in
        table_keys and generates a dictionary with keys [temp][weight][altitude]
        to facilitate direct access to the performance lookup tables.
        """
        # Process all entries in self._performanceTables that are listed in
        # table_keys.
        for tkey in table_keys:

            # Get the indices for weight, temperature deviation and altitude in
            # the current table.
            weight_index = self._performanceTables[tkey]["columns"].index("weight")
            temp_index   = self._performanceTables[tkey]["columns"].index("temp")
            alt_index    = self._performanceTables[tkey]["columns"].index("alt")
            
            for dataline in self._performanceTables[tkey]["data"]:

                weight = dataline[weight_index]
                temp   = dataline[temp_index]
                alt    = dataline[alt_index]

                # Create new sub-dicts for the current temp and weight, if no
                # dicts exist for these values.
                if temp not in target_dict.keys():
                    target_dict[temp] = {}
                if weight not in target_dict[temp].keys():
                    target_dict[temp][weight] = {}

                # Copy the performance attributes (the actual attributes depend
                # on climb/decent/cruise/.. mode).
                target_dict[temp][weight][alt] = dataline[3:]

        # For climb and descent performance tables, a line with zero performance
        # values for zero altitude might be required to correctly handle
        # altitudes below the lowest altitude listed in the performance table.
        if insert_zero_values:
            for temp in target_dict.keys():
                for weight in target_dict[temp].keys():
                    alts = target_dict[temp][weight].keys()
                    num_values = len(target_dict[temp][weight][alts[0]])
                    target_dict[temp][weight][0.] = list([0.]) * num_values


    def _fetchValuesFromPerformanceTable(self, table, delta_temp_ISA, 
                                         grossweight, altitude, 
                                         use_next_lower_altitude=False):
        """Fetch values at temperature "delta_temp_ISA" off ISA daytime
        conditions, aircraft "grossweight" and aircraft "altitude" from
        performance table "table". If "_performanceTableInterpretation" is
        "conservative", the next larger table entries are returned (unless
        use_next_lower_altitude is True, in which case the table entry of the next
        smaller altitude is returned), if it is "interpolation", values are
        interpolated in grossweight and altitude.
        """
        # 1) Find enclosing grossweight values.
        # =====================================

        # Error checking.
        if self._errorHandling == "strict":
            if altitude > self.maximumCruiseAltitude_ft:
                raise ValueError("the requested altitude of %i ft is above "\
                                     "the maximum cruise altitude of %i that "\
                                     "this aircraft can reach" % \
                                     (altitude, self.maximumCruiseAltitude_ft))
            if grossweight > self.maximumTakeoffWeight_lbs:
                raise ValueError("grossweight of %i lbs exceeds maximum takeoff"\
                                     " weight of %i lbs" % (grossweight,
                                                            self.maximumTakeoffWeight_lbs))

        # Get a list of the available grossweight values in the performance
        # table of the current ISA temperature deviation. Convert the list to a
        # numpy array to be able to use the searchsorted() method.
        available_grossweights = table[delta_temp_ISA].keys()
        available_grossweights = np.array(available_grossweights)
        available_grossweights.sort()

        # searchsorted() returns the index of the value next larger than
        # "grossweight".
        gw_index = available_grossweights.searchsorted(grossweight)
        grossweight_below = available_grossweights[max(gw_index-1, 0)]
        grossweight_above = available_grossweights[min(gw_index  , len(available_grossweights)-1)]

        #print grossweight_below, grossweight_above

        # 2) Find enclosing altitude values for next larger weight.
        # =========================================================
        
        # Get a list of the available grossweight values in the performance
        # table of the current ISA temperature deviation. Convert the list to a
        # numpy array to be able to use the searchsorted() method.
        available_altitudes = table[delta_temp_ISA][grossweight_above].keys()
        available_altitudes = np.array(available_altitudes)
        available_altitudes.sort()

        # searchsorted() returns the index of the value next larger than
        # "altitude".
        alt_index = available_altitudes.searchsorted(altitude)
        altitude_below = available_altitudes[max(alt_index-1, 0)]
        altitude_above = available_altitudes[min(alt_index  , len(available_altitudes)-1)]

        #print altitude_below, altitude_above

        if self._errorHandling == "strict":
            if altitude > altitude_above:
                raise ValueError("the requested altitude of %i ft cannot be "\
                                     "reached with the given weight; maximum "\
                                     "altitude with weight %i lbs is %i ft" % \
                                     (altitude, grossweight, altitude_above))

        # 3a) Conservative interpretation of performance tables: We're done.
        # ==================================================================

        if (self._performanceTableInterpretation == "conservative"):
            # Conservative interpretation:
            if not use_next_lower_altitude:
                # Take the values of the next larger grossweight and the next
                # larger altitude. These values will overestimate the actual
                # values.
                return table[delta_temp_ISA][grossweight_above][altitude_above]
            else:
                # Take the values of the next larger grossweight and the next
                # smaller altitude. This might be required to correctly estimate
                # the climb or descent performance between two levels that both
                # fall between the same two table altitudes.
                return table[delta_temp_ISA][grossweight_above][altitude_below]

        # 3b) Interpolation: Interpolate the four adjacent table entries.
        # ===============================================================

        elif (self._performanceTableInterpretation == "interpolation"):
            # Interpolation mode:
            
            # Find the enclosing altitude values for the lower grossweight
            # value.
            available_altitudes = table[delta_temp_ISA][grossweight_below].keys()
            available_altitudes = np.array(available_altitudes)
            available_altitudes.sort()
            alt_index = available_altitudes.searchsorted(altitude)
            gw_blw_altitude_below = available_altitudes[max(alt_index-1, 0)]
            gw_blw_altitude_above = available_altitudes[min(alt_index  , len(available_altitudes)-1)]
            
            #print gw_blw_altitude_below, gw_blw_altitude_above
        
            # Fetch performance values for the four adjacent table entries.
            num_values = len(table[delta_temp_ISA][grossweight_above][altitude_above])
            values = np.zeros((4, num_values))

            # grossweight_below, altitude_below
            values[0, :] = \
                table[delta_temp_ISA][grossweight_below][gw_blw_altitude_below]
            # grossweight_below, altitude_above
            values[1, :] = \
                table[delta_temp_ISA][grossweight_below][gw_blw_altitude_above]
            # grossweight_above, altitude_below
            values[2, :] = \
                table[delta_temp_ISA][grossweight_above][altitude_below]
            # grossweight_above, altitude_above
            values[3, :] = \
                table[delta_temp_ISA][grossweight_above][altitude_above]

            for iv in range(num_values):
                # Linearly interpolate values between the altitudes ..
                values[0, iv] = np.interp(altitude, 
                                          [gw_blw_altitude_below, gw_blw_altitude_above],
                                          [values[0, iv], values[1, iv]])
                values[2, iv] = np.interp(altitude, 
                                          [altitude_below, altitude_above],
                                          [values[2, iv], values[3, iv]])
                # .. and between the grossweights.
                values[0, iv] = np.interp(grossweight, 
                                          [grossweight_below, grossweight_above],
                                          [values[0, iv], values[2, iv]])

        # Return values as list.
        return values[0, :].tolist()


    def selectConfiguration(self, config):
        """
        """
        super(FliteStarExportedAircraft, self).selectConfiguration(config)

        # Generate performance tables for current configuration.
        self._climbPerformanceTable   = {}
        self._cruisePerformanceTable  = {}
        self._descentPerformanceTable = {}

        # For climb and descent performance, zero values are added.
        self._generatePerformanceDict(self._performanceTableKeys[config]["climb"],
                                      self._climbPerformanceTable,
                                      insert_zero_values=True)

        self._generatePerformanceDict(self._performanceTableKeys[config]["descent"],
                                      self._descentPerformanceTable,
                                      insert_zero_values=True)

        for cruisemode in self._performanceTableKeys[config]["cruise"].keys():
            self._cruisePerformanceTable[cruisemode] = {}
            self._generatePerformanceDict(
                self._performanceTableKeys[config]["cruise"][cruisemode],
                self._cruisePerformanceTable[cruisemode])


