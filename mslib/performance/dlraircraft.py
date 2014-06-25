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
import os
import logging

# related third party imports
import numpy as np

# local application imports
from flitestaraircraft import FliteStarExportedAircraft


# Get the path of this module to locate the FliteStar performance files.
try:
    modulepath = os.path.dirname(__file__)
except:
    modulepath = ""


################################################################################
###                                   HALO                                   ###
################################################################################

class HALO(FliteStarExportedAircraft):
    """DLR Gulfstream G550 "HALO" (D-ADLR) performance class.
    """
    aircraftName             = "DLR Gulfstream G550 \"HALO\" (D-ADLR)"
    maximumTakeoffWeight_lbs = 91000
    fuelCapacity_lbs         = 41300
    maximumCruiseAltitude_ft = 51000
    defaultCruiseAltitude_ft = 41000
    availableCruiseModes     = ["LRC", "M.75", "M.80"] # more in pdf
    defaultCruiseMode        = "LRC"
    availableConfigurations  = ["HALO Baseline +10DC"]
    defaultConfiguration     = "HALO Baseline +10DC"

    def __init__(self):
        """Defines the performance file (exported by FliteStar) and which file
        sections map to which flight mode.
        """
        super(HALO, self).__init__(os.path.join(modulepath, "data", "HALO_+10DC.txt"))

        # Define a mapping from the sections in the FliteStar file to the
        # individual flight modes. Keys are:
        # _performanceTableKeys[configuration][climb|descent] = list of section keys
        # _performanceTableKeys[configuration][cruise][cruisemode] = list of section keys
        self._performanceTableKeys = {
            "HALO Baseline +10DC": {
                "climb": [
                    '[Corporate Model - Climb Data - "Climb ISA+10 HALO Baseline +10DC" 0.00]'
                    ],
                "descent": [
                    '[Corporate Model - Descent Data - "Descent ISA 250-300KCAS/M.75 HALO Baseline +10DC" 0.00]'
                    ],
                "cruise": {
                    "LRC": [
                        '[Corporate Model - TAS/Fuel Cruise Data - "HALO LRC +10DC" 0.00]'
                        ],
                    "M.75": [
                        '[Corporate Model - TAS/Fuel Cruise Data - "HALO M.75 +10DC" 0.00]'
                        ],
                    "M.80": [
                        '[Corporate Model - TAS/Fuel Cruise Data - "HALO M.80 +10DC" 0.00]'
                        ]
                    }
                },
            
            "__DUMMY__": {
                # Add additional configurations here.
                }
            }

        self.selectConfiguration(self.defaultConfiguration)
        #self.setPerformanceTableInterpretation("conservative")
        self.setPerformanceTableInterpretation("interpolation")
        self.setErrorHandling("strict")


    def climbPerformance(self, altitude, deltatemp, grossweight,
                         use_next_lower_altitude=False):
        """HALO Twin Engine Climb performance. Cf. HALO performance manual,
        pp. 18ff.

        Arguments:
        altitude    -- altitude in ft to climb to
        deltatemp   -- temperature deviation of ISA conditions in K
        grossweight -- total weight of the aircraft in lbs
        use_next_lower_altitude
                    -- if performance table interpretation has been set to 
                       "conservative", setting this arg to True will result
                       in the performance values of the next lower altitude
                       level listed in the performance table being returned
                       (default is True, so that the values of the next
                       higher level are returned).

        Returns time [min], distance [nm] and fuel [lbs] required for the climb.
        """

# TODO currently only the climb performance table for ISA+10 conditions is
# available. The HALO manual also lists a table for ISA+20 conditions. This
# should be integrated here (mr, 02Nov2012).
        delta_temp_ISA = 10.
        # if deltatemp > 15.: delta_temp_ISA = 20.
        # # Interpolation between the ISA+10 and ISA+20 tables would also be possible.

        time, dist, fuel = self._fetchValuesFromPerformanceTable(
            self._climbPerformanceTable, delta_temp_ISA, grossweight, altitude,
            use_next_lower_altitude)
                                                                  
        # Correction for each 10 degrees below ISA+10. See HALO performance
        # manual, p.21.
        num_10_degrees_below_ISA10 = int((-10. + deltatemp) / 10.)
        if (delta_temp_ISA == 10. and num_10_degrees_below_ISA10 < 0.):
            # time: increase by 1% for each 10 deg below ISA+10
            time += -num_10_degrees_below_ISA10 * 0.01  * time
            # fuel: decrease by 1.5% for each ..
            fuel -= -num_10_degrees_below_ISA10 * 0.015 * fuel
            # distance: decrease by 1% for each ..
            dist -= -num_10_degrees_below_ISA10 * 0.01  * dist

        return time, dist, fuel


    def cruisePerformance(self, cruisemode, altitude, deltatemp, grossweight):
        """HALO Twin Engine Cruise performance. Cf. HALO performance manual,
        pp. 27ff.

        Arguments:
        cruisemode  -- one of the values in "availableCruiseModes"
        altitude    -- altitude in ft to climb to
        deltatemp   -- temperature deviation of ISA conditions in K
        grossweight -- total weight of the aircraft in lbs        

        Returns true airspeed [knots] and fuelflow [lbs/hr].
        """
        if cruisemode not in self.availableCruiseModes:
            raise ValueError("unknown cruise mode: %s" % cruisemode)
        
        # Cruise data for HALO is only available for ISA conditions; correction
        # for non-ISA conditions is done below.
        delta_temp_ISA = 0.

        # For conservative value estimation, use the values of the next lower
        # altitude level, as these usually yield lower airspeeds and higher fuel
        # consumption (use_next_lower_altitude=True).
        tas, fuelflow = self._fetchValuesFromPerformanceTable(
            self._cruisePerformanceTable[cruisemode], delta_temp_ISA,
            grossweight, altitude, use_next_lower_altitude=True)

        # Correction for each 10 degrees off ISA conditions. See HALO
        # performance manual, p.27.
        num_10_degrees_off_ISA = int(deltatemp / 10.)
        # true airspeed: increase/decrease by 2.3% for each 10 deg off ISA day 
        # conditions
        tas += num_10_degrees_off_ISA * 0.023  * tas
        # fuelflow: increase/decrease by 3.4% for each ..
        fuelflow += num_10_degrees_off_ISA * 0.034 * fuelflow

        return tas, fuelflow


    def descentPerformance(self, altitude, deltatemp, grossweight,
                           use_next_lower_altitude=False):
        """HALO Twin Engine Descent performance. Cf. HALO performance manual,
        pp. 57ff.

        Arguments:
        altitude    -- altitude in ft to climb to
        deltatemp   -- temperature deviation of ISA conditions in K
        grossweight -- total weight of the aircraft in lbs

        Returns time [min], distance [nm] and fuel [lbs] required for the
        descent.
        """
        # Descent data for HALO is only available for ISA conditions; correction
        # for non-ISA conditions is done below.
        delta_temp_ISA = 0.

        time, dist, fuel = self._fetchValuesFromPerformanceTable(
            self._descentPerformanceTable, delta_temp_ISA, grossweight,
            altitude, use_next_lower_altitude)

        # Correction for each 10 degrees off ISA conditions. See HALO
        # performance manual, p.60.
        num_10_degrees_off_ISA = int(deltatemp / 10.)
        # time: increase/decrease by 2% for each 10 deg off ISA
        time += num_10_degrees_off_ISA * 0.02  * time
        # fuel: decrease/increase by 0.5% for each ..
        fuel -= num_10_degrees_off_ISA * 0.005 * fuel
        # distance: no change

        return time, dist, fuel


################################################################################
###                                 FALCON                                   ###
################################################################################

class Falcon(FliteStarExportedAircraft):
    """DLR Dessault Falcon E20 (D-CMET).
    """
    aircraftName             = "DLR Dessault Falcon E20 (D-CMET)"
    maximumTakeoffWeight_lbs = 30324
    fuelCapacity_lbs         = 8800
    maximumCruiseAltitude_ft = 42000
    defaultCruiseAltitude_ft = 39000
    availableCruiseModes     = ["MRC", "LRC", "M.765"]
    defaultCruiseMode        = "LRC"
    availableConfigurations  = ["FALCON Baseline"]
    defaultConfiguration     = "FALCON Baseline"

    def __init__(self):
        """
        """
        super(Falcon, self).__init__(os.path.join(modulepath, "data", "FALCON_Baseline.txt"))

        # Define a mapping from the sections in the FliteStar file to the
        # individual flight modes. Keys are:
        # _performanceTableKeys[configuration][climb|descent] = list of section keys
        # _performanceTableKeys[configuration][cruise][cruisemode] = list of section keys
        self._performanceTableKeys = {
            "FALCON Baseline": {
                "climb": [
                    '[Corporate Model - Climb Data - "Climb ISA-10 FALCON Baseline" 0.00]',
                    '[Corporate Model - Climb Data - "Climb ISA FALCON Baseline" 0.00]',
                    '[Corporate Model - Climb Data - "Climb ISA+10 FALCON Baseline" 0.00]'
                    ],
                "descent": [
                    '[Corporate Model - Descent Data - "Descent ISA M=0.76 / 270 kts FALCON Baseline" 0.00]'
                    ],
                "cruise": {
                    "MRC": [
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline MRC ISA-10" 0.00]',
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline MRC ISA " 0.00]',
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline MRC ISA-10" 0.00]'
                        ],
                    "LRC": [
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline LRC ISA-10" 0.00]',
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline LRC ISA " 0.00]',
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline LRC ISA+10" 0.00]'
                        ],
                    "M.765": [
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline M.765 ISA-10" 0.00]',
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline M.765 ISA " 0.00]',
                        '[Corporate Model - TAS/Fuel Cruise Data - "FALCON Baseline M.765 ISA+10" 0.00]'
                        ]
                    }
                },
            
            "__DUMMY__": {
                # Add additional configurations here.
                }
            }

        self.selectConfiguration(self.defaultConfiguration)
        #self.setPerformanceTableInterpretation("conservative")
        self.setPerformanceTableInterpretation("interpolation")
        self.setErrorHandling("strict")


    def climbPerformance(self, altitude, deltatemp, grossweight,
                         use_next_lower_altitude=False):
        """Falcon Twin Engine Climb performance.

        Arguments:
        altitude    -- altitude in ft to climb to
        deltatemp   -- temperature deviation of ISA conditions in K
        grossweight -- total weight of the aircraft in lbs

        Returns time [min], distance [nm] and fuel [lbs] required for the climb.
        """
        # Falcon climb data are available for temperatures of -10, 0, +10
        # degrees off day ISA conditions.
        delta_temp_ISA = 0.
        if deltatemp >= 10.: delta_temp_ISA = 10.
        elif deltatemp <= -10.: delta_temp_ISA = -10.

        time, dist, fuel = self._fetchValuesFromPerformanceTable(
            self._climbPerformanceTable, delta_temp_ISA, grossweight, altitude,
            use_next_lower_altitude)

        return time, dist, fuel


    def cruisePerformance(self, cruisemode, altitude, deltatemp, grossweight):
        """Falcon Twin Engine Cruise performance.

        Arguments:
        cruisemode  -- one of the values in "availableCruiseModes"
        altitude    -- altitude in ft to climb to
        deltatemp   -- temperature deviation of ISA conditions in K
        grossweight -- total weight of the aircraft in lbs        

        Returns true airspeed [knots] and fuelflow [lbs/hr].
        """
        if cruisemode not in self.availableCruiseModes:
            raise ValueError("unknown cruise mode: %s" % cruisemode)
        
        # Falcon cruise data are available for temperatures of -10, 0, +10
        # degrees off day ISA conditions.
        delta_temp_ISA = 0.
        if deltatemp >= 10.: delta_temp_ISA = 10.
        elif deltatemp <= -10.: delta_temp_ISA = -10.

        # For conservative value estimation, use the values of the next lower
        # altitude level, as these usually yield lower airspeeds and higher fuel
        # consumption (use_next_lower_altitude=True).
        tas, fuelflow = self._fetchValuesFromPerformanceTable(
            self._cruisePerformanceTable[cruisemode], delta_temp_ISA,
            grossweight, altitude, use_next_lower_altitude=True)

        return tas, fuelflow


    def descentPerformance(self, altitude, deltatemp, grossweight,
                           use_next_lower_altitude=False):
        """Falcon Twin Engine Descent performance.

        Arguments:
        altitude    -- altitude in ft to climb to
        deltatemp   -- temperature deviation of ISA conditions in K
        grossweight -- total weight of the aircraft in lbs

        Returns time [min], distance [nm] and fuel [lbs] required for the
        descent.
        """
        # Descent data for Falcon is only available for ISA conditions.
        delta_temp_ISA = 0.

        time, dist, fuel = self._fetchValuesFromPerformanceTable(
            self._descentPerformanceTable, delta_temp_ISA, grossweight,
            altitude, use_next_lower_altitude)

        return time, dist, fuel
