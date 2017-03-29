# -*- coding: utf-8 -*-
"""

    mslib.mswms.msschem
    ~~~~~~~~~~~~~~~~~~~

    This module provides functions for using CTM chemical forecasts prepared
    with MSS-Chem

    This file is part of mss.

    :copyright: Copyright 2017 Andreas Hilboll
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

MSSChemSpecies = {
        'AERMR01': 'fine_sea_salt_aerosol',
        'AERMR02': 'medium_sea_salt_aerosol',
        'AERMR03': 'coarse_sea_salt_aerosol',
        'AERMR04': 'fine_dust_aerosol',
        'AERMR05': 'medium_dust_aerosol',
        'AERMR06': 'coarse_dust_aerosol',
        'AERMR07': 'hydrophobic_organic_matter_aerosol',
        'AERMR08': 'hydrophilic_organic_matter_aerosol',
        'AERMR09': 'hydrophobic_black_carbon_aerosol',
        'AERMR10': 'hydrophilic_black_carbon_aerosol',
        'AERMR11': 'sulfate_aerosol',
        'C2H6': 'ethane',
        'C3H8': 'propane',
        'C5H8': 'isoprene',
        'CH4': 'methane',
        'CO': 'carbon_monoxide',
        'HCHO': 'formaldehyde',
        'HNO3': 'nitric_acid',
        'NH3': 'ammonia',
        'NMVOC': 'nmvoc_expressed_as_carbon',
        'NO': 'nitrogen_monoxide',
        'NO2': 'nitrogen_dioxide',
        'O3': 'ozone',
        'OH': 'hydroxyl_radical',
        'PAN': 'peroxyacetyl_nitrate',
        'PM2P5': 'pm2p5_ambient_aerosol',
        'PM10': 'pm10_ambient_aerosol',
        'SO2': 'sulfur_dioxide',
        }


MSSChemQuantities = {
    'mfrac': ('mass_fraction', 'kg kg-1', 1),
    'mconc': ('mass_concentration', 'ug m-3', 1),
    'nfrac': ('mole_fraction', 'mol mol-1', 1),
}


MSSChemTargets = {
        qtylong + '_of_' + species + '_in_air': (key, qty, units, scale)
        for key, species in MSSChemSpecies.items()
        for qty, (qtylong, units, scale) in MSSChemQuantities.items()}
