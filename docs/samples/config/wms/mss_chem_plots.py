# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1.inset_locator
import mpl_toolkits.basemap
from matplotlib import patheffects

from mslib.mswms.mpl_hsec import MPLBasemapHorizontalSectionStyle
from mslib.mswms.mpl_vsec import AbstractVerticalSectionStyle
from mslib.mswms.utils import get_style_parameters, get_cbar_label_format
from mslib.utils import convert_to
from mslib import thermolib


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
    'nconc': ('mole_concentration', 'mol m-3', 1),
}


MSSChemTargets = {
    qtylong + '_of_' + species + '_in_air': (key, qty, units, scale)
    for key, species in MSSChemSpecies.items()
    for qty, (qtylong, units, scale) in MSSChemQuantities.items()}


class HS_MSSChemStyle(MPLBasemapHorizontalSectionStyle):
    """
    Pressure level version for Chemical Mixing ratios.
    """
    styles = [
        ("auto", "auto colour scale"),
        ("autolog", "auto logcolour scale"), ]

    # In order to use information from the DataAccess class to construct the titles, we override the set_driver to set
    # self.title.  This cannot happen in __init__, as the WMSServer doesn't initialize the layers with the driver but
    # rather sets the driver only after initialization.
    def set_driver(self, driver):
        super(HS_MSSChemStyle, self).set_driver(driver=driver)
        self.title = self._title_tpl.format(modelname=self.driver.data_access._modelname)

    def _plot_style(self):
        bm = self.bm
        ax = self.bm.ax

        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        lonmesh, latmesh = bm(lonmesh_, latmesh_)

        show_data = np.ma.masked_invalid(self.data[self.dataname]) * self.unit_scale
        # get cmin, cmax, cbar_log and cbar_format for level_key
        cmin, cmax, clevs, cmap, norm, ticks = get_style_parameters(
            self.dataname, self.style, None, None, show_data)

        tc = bm.contourf(lonmesh, latmesh, show_data, levels=clevs, cmap=cmap, extend="both", norm=norm)

        for cont_data, cont_levels, cont_colour, cont_label_colour, cont_style, cont_lw, pe in self.contours:
            cs_pv = ax.contour(lonmesh, latmesh, self.data[cont_data], cont_levels,
                               colors=cont_colour, linestyles=cont_style, linewidths=cont_lw)
            cs_pv_lab = ax.clabel(cs_pv, colors=cont_label_colour, fmt='%i')
            if pe:
                plt.setp(cs_pv.collections, path_effects=[patheffects.withStroke(linewidth=cont_lw + 2,
                                                                                 foreground="w")])
                plt.setp(cs_pv_lab, path_effects=[patheffects.withStroke(linewidth=1, foreground="w")])

        # define position of the colorbar and the orientation of the ticks
        if self.crs.lower() == "epsg:77774020":
            cbar_location = 3
            tick_pos = 'right'
        else:
            cbar_location = 4
            tick_pos = 'left'

        # Format for colorbar labels
        cbar_label = self.title
        cbar_format = get_cbar_label_format(self.style, np.abs(clevs).max())

        if not self.noframe:
            cbar = self.fig.colorbar(tc, fraction=0.05, pad=0.08, shrink=0.7,
                                     norm=norm, label=cbar_label, format=cbar_format, ticks=ticks)
            cbar.set_ticks(clevs)
            cbar.set_ticklabels(clevs)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="3%", height="40%", loc=cbar_location)
            self.fig.colorbar(tc, cax=axins1, orientation="vertical", format=cbar_format, ticks=ticks)

            # adjust colorbar fontsize to figure height
            fontsize = self.fig.bbox.height * 0.024
            axins1.yaxis.set_ticks_position(tick_pos)
            for x in axins1.yaxis.majorTicks:
                x.label1.set_path_effects([patheffects.withStroke(linewidth=4, foreground='w')])
                x.label1.set_fontsize(fontsize)


def make_msschem_hs_class(
        entity, nam, vert, units, scale, add_data=None, add_contours=None, fix_styles=None,
        add_styles=None, add_prepare=None):
    if add_data is None:
        add_data = []
    _contourname = ""
    if add_contours is None:
        add_contours = []
    elif add_contours[0][0] == "air_pressure":
        _contourname = "_pcontours"

    class fnord(HS_MSSChemStyle):
        name = f"HS_{entity}_{vert}{_contourname}"
        dataname = entity
        units = units
        unit_scale = scale
        _title_tpl = nam + " (" + vert + ")"
        long_name = entity
        if units:
            _title_tpl += f"({units})"

        required_datafields = [(vert, entity, None)] + add_data
        contours = add_contours

    fnord.__name__ = nam
    fnord.styles = list(fnord.styles)

    return fnord


for vert in ["ml", "al", "pl"]:
    for stdname, props in MSSChemTargets.items():
        name, qty, units, scale = props
        key = "HS_MSSChemStyle_" + vert.upper() + "_" + name + "_" + qty
        globals()[key] = make_msschem_hs_class(stdname, name, vert, units, scale)

_pressurelevels = np.linspace(5000, 95000, 19)
_npressurelevels = len(_pressurelevels)
for vert in ["ml"]:
    for stdname, props in MSSChemTargets.items():
        name, qty, units, scale = props
        key = "HS_MSSChemStyle_" + vert.upper() + "_" + name + "_" + qty + "_pcontours"
        globals()[key] = make_msschem_hs_class(
            stdname, name, vert, units, scale, add_data=[(vert, "air_pressure", None)],
            add_contours=[("air_pressure", _pressurelevels,
                           ["dimgrey"] * _npressurelevels,
                           ["dimgrey"] * _npressurelevels,
                           ["dotted"] * _npressurelevels, 1, True)],)


class VS_MSSChemStyle(AbstractVerticalSectionStyle):
    """ CTM tracer vertical tracer cross sections via MSS-Chem
    """
    styles = [
        ("auto", "auto colour scale"),
        ("autolog", "auto log colour scale"), ]

    # Variables with the highest number of dimensions first (otherwise
    # MFDatasetCommonDims will throw an exception)!
    required_datafields = [("ml", "air_pressure", "Pa")]

    # In order to use information from the DataAccess class to construct the titles, we override the set_driver to set
    # self.title.  This cannot happen in __init__, as the WMSServer doesn't initialize the layers with the driver but
    # rather sets the driver only after initialization.
    def set_driver(self, driver):
        super(VS_MSSChemStyle, self).set_driver(driver=driver)
        # for altitude level model data, when we don't have air_pressure information, we want to warn users that the
        # vertical section is only an approximation
        vert = self.name[-2:]
        if vert != "pl":
            # look for valid times including air_pressure
            init_times = self.driver.data_access.get_init_times()
            valid_times = self.driver.data_access.get_valid_times(
                "air_pressure", vert, init_times[0])
            if len(valid_times) == 0:
                self.title = self.title.replace(
                    "(" + vert + ")", "(" + vert + "; WARNING: vert. distribution only approximate!)")

    def _prepare_datafields(self):
        """Computes potential temperature from pressure and temperature if
        it has not been passed as a data field.
        """
        if self.name[-2:] == "pl":
            self.data["air_pressure"] = np.empty_like(self.data[self.dataname])
            self.data["air_pressure"][:] = self.driver.vert_data[::-self.driver.vert_order, np.newaxis]
        elif self.name[-2:] == "tl":
            self.data["air_potential_temperature"] = np.empty_like(self.data[self.dataname])
            self.data["air_potential_temperature"][:] = self.driver.vert_data[::-self.driver.vert_order, np.newaxis]
        elif self.name[-2:] == "al":
            # CAMS Regional Ensemble doesn't provide any pressure information, but we want to plot vertical sections
            # anyways, so we do a poor-man's on-the-fly conversion here.
            if 'air_pressure' not in self.data:
                self.data["air_pressure"] = np.empty_like(self.data[self.dataname])
                self.data['air_pressure'][:] = thermolib.flightlevel2pressure_a(convert_to(
                    self.driver.vert_data[::-self.driver.vert_order, np.newaxis],
                    self.driver.vert_units, "hft"))

    def _plot_style(self):
        ax = self.ax
        curtain_cc = self.data[self.dataname] * self.unit_scale
        curtain_cc = np.ma.masked_invalid(curtain_cc)
        curtain_p = self.data["air_pressure"]

        numlevel = curtain_p.shape[0]
        numpoints = len(self.lats)
        curtain_lat = self.lat_inds.repeat(numlevel).reshape((numpoints, numlevel)).transpose()

        # Filled contour plot of cloud cover.
        # INFO on COLORMAPS:
        #    http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
        if self.p_bot > self.p_top:
            visible = (curtain_p <= self.p_bot) & (curtain_p >= self.p_top)
        else:
            visible = (curtain_p >= self.p_bot) & (curtain_p <= self.p_top)

        if visible.sum() == 0:
            visible = np.ones_like(curtain_cc, dtype=bool)

        cmin, cmax, clevs, cmap, norm, ticks = get_style_parameters(
            self.dataname, self.style, None, None, curtain_cc[visible])

        cs = ax.contourf(curtain_lat, curtain_p, curtain_cc, clevs, cmap=cmap, extend="both", norm=norm)

        # Contour lines
        for cont_data, cont_levels, cont_colour, cont_label_colour, cont_style, cont_lw, pe in self.contours:
            if cont_levels is None:
                pl_cont = ax.plot(self.lat_inds, self.data[cont_data].reshape(-1), "o", color="k", zorder=100)
                plt.setp(pl_cont, path_effects=[patheffects.withStroke(linewidth=4, foreground="w")])
            else:
                cs_pv = ax.contour(curtain_lat, curtain_p, self.data[cont_data], cont_levels,
                                   colors=cont_colour, linestyles=cont_style, linewidths=cont_lw)
                plt.setp(cs_pv.collections,
                         path_effects=[patheffects.withStroke(linewidth=cont_lw + 2, foreground="w")])
                cs_pv_lab = ax.clabel(cs_pv, colors=cont_label_colour, fontsize=8, fmt='%i')
                plt.setp(cs_pv_lab, path_effects=[patheffects.withStroke(linewidth=1, foreground="w")])

        # Pressure decreases with index, i.e. orography is stored at the
        # zero-p-index (data field is flipped in mss_plot_driver.py if
        # pressure increases with index).
        self._latlon_logp_setup(titlestring=self.title)

        # Format for colorbar labels
        cbar_format = get_cbar_label_format(self.style, np.median(np.abs(clevs)))
        cbar_label = self.title

        # Add colorbar.
        if not self.noframe:
            self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.14)
            self.fig.colorbar(cs, fraction=0.05, pad=0.01, format=cbar_format, label=cbar_label, ticks=ticks)
        else:
            axins1 = mpl_toolkits.axes_grid1.inset_locator.inset_axes(
                ax, width="1%", height="40%", loc=1)
            self.fig.colorbar(cs, cax=axins1, orientation="vertical", format=cbar_format, ticks=ticks)

            # adjust colorbar fontsize to figure height
            fontsize = self.fig.bbox.height * 0.024
            axins1.yaxis.set_ticks_position("left")
            for x in axins1.yaxis.majorTicks:
                x.label1.set_path_effects([patheffects.withStroke(linewidth=4, foreground='w')])
                x.label1.set_fontsize(fontsize)


def make_msschem_vs_class(
        entity, nam, vert, units, scale, add_data=None,
        add_contours=None, fix_styles=None, add_styles=None, add_prepare=None):

    # This is CTM output, so we cannot expect any additional meteorological
    # parameters except for air_pressure
    if add_data is None:
        if vert == "al":
            # "al" is altitude layer, i.e., for CTM output with no pressure information
            # at all (e.g., CAMS reg. Ensemble)
            # In those cases we derive air_pressure from the altitude alone, in the _prepare_datafields() method
            add_data = []
        elif vert == 'pl':
            # "pl" are pressure levels.  Here, the air_pressure information is implicitly contained in the vertical
            # dimension coordinate, so we don't need to explicitly load it here.
            add_data = []

        else:
            # all other layer types need to read air_pressure from the data
            add_data = [(vert, "air_pressure", "Pa")]
    if add_contours is None:
        add_contours = []

    class fnord(VS_MSSChemStyle):
        name = f"VS_{entity}_{vert} "
        dataname = entity
        units = units
        unit_scale = scale
        title = nam + " (" + vert + ")"
        long_name = entity
        if units:
            title += f"({units})"
        required_datafields = [(vert, entity, None)] + add_data
        contours = add_contours if add_contours else []

    fnord.__name__ = nam
    fnord.styles = list(fnord.styles)

    if add_styles is not None:
        fnord.styles += add_styles
    if fix_styles is not None:
        fnord.styles = fix_styles
    if add_prepare is not None:
        fnord._prepare_datafields = add_prepare

    return fnord


for vert in ["ml", "tl", "pl", "al"]:
    for stdname, props in MSSChemTargets.items():
        name, qty, units, scale = props
        key = "VS_MSSChemStyle_" + vert.upper() + "_" + name + "_" + qty
        globals()[key] = make_msschem_vs_class(stdname, name, vert, units, scale)
