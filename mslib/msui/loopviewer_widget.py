# -*- coding: utf-8 -*-
"""
    mslib.msui.loopviewer_widget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Widget to display batch-generated images.

    This module provides three classes used by "loopview.py":
    1) ProductChooserDialog: To display a dialog in which the user can choose
    a product to load into an image widget (e.g. ECMWF Europe relative humidity).
    2) LoopLabel: Derived from QLabel. This is a label that is used to display
    an image, extended by a method that observes mouse wheel events (for time
    and level navigation).
    3) ImageLoopWidget: Widget that includes a LoopLabel for an image. Additionally
    provides GUI elements to control zoom and vertical level navigation. A double
    click on the widget opens a ProductChooserDialog.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
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


from datetime import datetime, timedelta

import StringIO
import functools
import logging
import os
import urllib2

# related third party imports
from mslib.msui.mss_qt import QtGui, QtCore, QtWidgets

# local application imports
from mslib.msui.mss_qt import ui_imageloop_widget as ui
from mslib.msui.mss_qt import ui_imageloop_load_dialog as uipc
from mslib.msui.wms_control import MSS_WMS_AuthenticationDialog


class ProductChooserDialog(QtWidgets.QDialog, uipc.Ui_ProductChooserDialog):
    """Dialog to let the user choose a product to load (e.g. ECMWF Europe
       relative humidity).

       The constructor is passed a configuration dictionary from
       mss_settings, from which the keys are displayed to the user.
    """

    def __init__(self, config=None, *args):
        super(ProductChooserDialog, self).__init__(*args)
        self.setupUi(self)
        self.setModal(True)
        self.config = config
        self.loadConfiguration()

        # Initialise date/time fields with current day, 00 UTC.
        self.dteInitTime.setDateTime(QtCore.QDateTime(
            datetime.utcnow().replace(hour=0, minute=0, second=0,
                                      microsecond=0)))

        # Connect slots and signals.
        self.cbType.currentIndexChanged.connect(self.loadProducts)
        self.cbProduct.currentIndexChanged.connect(self.loadRegions)

        self.tbInitTime_back.clicked.connect(functools.partial(self.changeInitTime, False))
        self.tbInitTime_fwd.clicked.connect(functools.partial(self.changeInitTime, True))

    def type(self):
        return str(self.cbType.currentText())

    def product(self):
        return str(self.cbProduct.currentText())

    def region(self):
        return str(self.cbRegion.currentText())

    def initTime(self):
        return self.dteInitTime.dateTime().toPyDateTime()

    def loadConfiguration(self):
        """Fill the combobox with configurations in the 'config' dictionary.
        """
        self.cbType.clear()
        self.cbProduct.clear()
        self.cbRegion.clear()
        keys = self.config.keys()
        keys.sort()
        self.cbType.addItems(keys)
        self.loadProducts(self.cbType.currentText())

    def loadProducts(self, _type):
        """Fill the combobox with products for the chosen configuration.
        """
        self.cbProduct.clear()
        _type = str(_type)
        keys = self.config[_type]["products"].keys()
        keys.sort()
        self.cbProduct.addItems(keys)
        self.loadRegions(self.cbProduct.currentText())

    def loadRegions(self, product):
        """Fill the combobox with available regions for the chosen configuration
           and product.
        """
        product = str(product)
        if product == "":
            return
        _type = str(self.cbType.currentText())
        self.cbRegion.clear()
        keys = self.config[_type]["products"][product]["regions"].keys()
        keys.sort()
        self.cbRegion.addItems(keys)

    def changeInitTime(self, forward):
        """Slot called when one of the time fwd/back buttons has been
           clicked.
        """
        forward = 1 if forward else -1
        _type = str(self.cbType.currentText())
        timestep = self.config[_type]["init_timestep"]
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteInitTime.dateTime()
        # Add value from sbInitTime_step and set new date.
        self.dteInitTime.setDateTime(d.addSecs(forward * 3600. *
                                               timestep))


class LoopLabel(QtWidgets.QLabel):
    """This is a label that is used to display an image, extended by a method
       that observes mouse wheel events (for time and level navigation).
    """

    wheelOnImage = QtCore.pyqtSignal([bool], name="wheelOnImage")
    shiftWheelOnImage = QtCore.pyqtSignal([bool], name="shiftWheelOnImage")

    def wheelEvent(self, event):
        """Called when the mouse wheel has been moved above the label.

        Emits wheelOnImage(bool) and shiftWheelOnImage(bool) signals,
        depending on whether the <Shift> key is pressed while the mouse
        wheel is moved. The boolean parameter is True if the wheel has
        been moved upwards, False if it has been moved downwards.
        """
        if event.modifiers() == QtCore.Qt.ShiftModifier:
            self.shiftWheelOnImage.emit(event.delta() > 0)
        else:
            self.wheelOnImage.emit(event.delta() > 0)
        event.accept()


class ImageLoopWidget(QtWidgets.QWidget, ui.Ui_ImageLoopWidget):
    """Widget that includes a LoopLabel for an image. Additionally
       provides GUI elements to control zoom and vertical level navigation.
       A double click on the widget opens a ProductChooserDialog.

       Principle:
       - the images to load are chosen by the user in a ProductChooserDialog,
         which is opened when the user double clicks the widget.
       - all time steps and vertical levels of the product are loaded into
         a list of QPixmap (method loadDataFromHTTP).
         NOTE: this can consume quite a bit of memory!
       - the pixmaps are displayed in a LoopLabel instance. This widget observes
         the mouse wheen signals of the label and changes time or level
         (methods changeValidTime and changeLevel).
       - instances if these widgets are combined in MSSLoopWindow (loopview.py).
    """

    num = 0
    signalChangeValidTime = QtCore.pyqtSignal([bool, object])

    def __init__(self, config=None, *args):
        super(ImageLoopWidget, self).__init__(*args)
        self.setupUi(self)
        self.viewer_parent = self.parentWidget()

        self.id = ImageLoopWidget.num
        ImageLoopWidget.num += 1

        # Scale factor of the displayed image.
        self.scaleFactor = 1.0

        # List that buffers all pixmaps.
        self.pixmaps = []
        self.current_pixmap = 0
        self.current_level = 0
        self.pixmap = None
        self.valid_time = None
        self.init_time = None

        self.retrieval_successful = False

        # Create a label that accomodates the images and make it the
        # central widget of the scroll area.
        self.imageLabel = LoopLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setText("double click to select a product for retrieval.")
        self.imageLabel.adjustSize()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setAlignment(QtCore.Qt.AlignCenter)
        self.scrollArea.setWidget(self.imageLabel)

        self.config = config
        self.levels = []

        self.btFitToWindow.setChecked(False)
        self.fitToWindow()

        self.products_dialog = ProductChooserDialog(config=config)

        # Connect slots and signals.
        self.btZoomIn.clicked.connect(self.zoomIn)
        self.btZoomOut.clicked.connect(self.zoomOut)
        self.btZoomNormalSize.clicked.connect(self.normalSize)
        self.btFitToWindow.clicked.connect(self.fitToWindow)

        self.tbLevel_down.clicked.connect(functools.partial(self.changeLevel, False))
        self.tbLevel_up.clicked.connect(functools.partial(self.changeLevel, True))

        self.imageLabel.wheelOnImage.connect(self.changeValidTime)
        self.imageLabel.shiftWheelOnImage.connect(self.changeLevel)

        # Progress dialog to inform the user about image ongoing retrievals.
        self.pdlg = QtWidgets.QProgressDialog("retrieving images...", "Cancel", 0, 100, self)

    def zoomIn(self):
        """Slot connected to the '+' button (zooms in).
        """
        self.scaleImage(1.25)

    def zoomOut(self):
        """Slot connected to the '-' button (zooms out).
        """
        self.scaleImage(0.8)

    def normalSize(self):
        """Slot connected to the 'orig' button (original image size).
        """
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        """Slot connected to the 'fit' button (fits image to available screen
           space.).
        """
        fitToWindow = self.btFitToWindow.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.imageLabel.adjustSize()
        self.updateActions()

    def updateActions(self):
        """Disable the zoom controls if 'fit to screen space' is checked.
        """
        self.btZoomIn.setEnabled(not self.btFitToWindow.isChecked())
        self.btZoomOut.setEnabled(not self.btFitToWindow.isChecked())
        self.btZoomNormalSize.setEnabled(not self.btFitToWindow.isChecked())

    def scaleImage(self, factor):
        """Does the actual zooming.
        """
        if not self.retrieval_successful:
            return

        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.btZoomIn.setEnabled(self.scaleFactor < 3.0)
        self.btZoomOut.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep() / 2)))

    def loadDataFromHTTP(self, _type, product, region, init_time):
        """Load batch products from the MSS website.

        Fill 'self.pixmaps' with the loaded images. Time steps that are given
        in the configuration dictionary but not available on the server are
        ignored. For each loaded image, its valid time is also stored to allow
        for the time synchronization.
        """
        self.retrieval_successful = False

        # Show the progress dialog, since the retrieval can take a few seconds.
        self.pdlg.reset()
        self.pdlg.setValue(0)
        self.pdlg.show()
        self.pdlg.repaint()

        base_url = self.config[_type]["url"]
        prod_abbrev = self.config[_type]["products"][product]["abbrev"]
        reg_abbrev = self.config[_type]["products"][product]["regions"][region]

        steps = self.config[_type]["products"][product]["forecast_steps"]
        levels = self.config[_type]["products"][product]["levels"]

        init_time_str = init_time.strftime("%Y%m%d%H%M")

        self.pixmaps = []
        num_levels = len(levels)
        num_steps = len(steps)
        username = None
        password = None
        realm = ""
        cancel = False
        auth_installed = False

        # LOOP over LEVELS *****************************************************
        for ilevel, level in enumerate(levels):

            pixmap_cache = []

            filename = u"{}_{}_{}".format(prod_abbrev, reg_abbrev, str(level))
            url = u"{0}_%03i.png".format(os.path.join(base_url, init_time_str, filename))

            # LOOP over TIMESTEPS **********************************************
            for istep, step in enumerate(steps):
                retrieve = url.format(step)
                logging.debug(u"attempting to retrieve image file: '{}'".format(retrieve))
                try:
                    auth_required = True
                    while auth_required:
                        if username and password and not auth_installed:
                            logging.debug("setting HTTP authentication..")
                            # (see http://docs.python.org/library/urllib2.html#examples).
                            # Create an OpenerDirector with support for Basic HTTP Authentication...
                            auth_handler = urllib2.HTTPBasicAuthHandler()
                            auth_handler.add_password(realm=realm,
                                                      uri=base_url,
                                                      user=username,
                                                      passwd=password)
                            opener = urllib2.build_opener(auth_handler)
                            # ...and install it globally so it can be used with urlopen.
                            urllib2.install_opener(opener)
                            auth_installed = True
                        try:
                            urlobject = urllib2.urlopen(retrieve)
                            auth_required = False
                        except urllib2.HTTPError as ex:
                            if ex.code == 401:
                                # Catch the "401 Unauthorized" error if one has been
                                # returned by the server and ask the user for username
                                # and password.
                                realm = ex.hdrs["WWW-Authenticate"].split('"')[1]
                                logging.debug(u"'{}' asks for authentication.".format(realm))
                                dlg = MSS_WMS_AuthenticationDialog(parent=self)
                                dlg.lblMessage.setText(realm)
                                dlg.setModal(True)
                                if dlg.exec_() == QtWidgets.QDialog.Accepted:
                                    username, password = dlg.getAuthInfo()
                                    auth_installed = False
                                else:
                                    cancel = True
                                    break
                            else:
                                raise
                    if not cancel:
                        # Read the image file from the URL into a string (urlobject.read())
                        # and wrap this string into a StringIO object that behaves like a file.
                        imageIO = StringIO.StringIO(urlobject.read())
                        qp = QtGui.QPixmap()
                        qp.loadFromData(imageIO.getvalue())

                        valid_time = init_time + timedelta(seconds=3600 * step)
                        pixmap_cache.append((qp, valid_time))
                except urllib2.HTTPError as ex:
                    logging.debug("timestep {:03d} not available (HTTP error {d})".format(step, ex.code))

                # Update progress dialog.
                self.pdlg.setValue((float(ilevel) + float(istep) / num_steps) / num_levels * 100.)
                self.pdlg.repaint()
                QtWidgets.QApplication.processEvents()
                if self.pdlg.wasCanceled() or cancel:
                    break

            if self.pdlg.wasCanceled() or cancel:
                logging.warning("map retrieval was canceled by the user.")
                self.retrieval_successful = False
                break

            if len(pixmap_cache) > 0:
                self.retrieval_successful = True
            self.pixmaps.append(pixmap_cache)

        # Reset image display after loading is complete.
        self.current_pixmap = 0
        self.current_level = 0
        if self.retrieval_successful:
            # Update image display and emit the time of the first image. This
            # time will become the global synchronized valid time (i.e. all
            # other widgets will synchronize to this time).
            self.synchronized = True
            self.levels = levels
            self.init_time = init_time
            self.lblInfo.setToolTip(u"Initialisation time: {}"
                                    .format(self.init_time.strftime("%Y-%m-%d %H:%M UTC")))
            self.updateImage()
            self.signalChangeValidTime.emit(True, self.valid_time)
            self.signalChangeValidTime.emit(False, self.valid_time)

            # TODO: Resize the window so that the image fits exactly. Also make the image
            #      keep its aspect ratio on fit-to-window resizes (mr, 2010-09-02):
            #      http://lists.trolltech.com/qt-interest/2005-11/thread01034-0.html
            self.fitToWindow()
            pxm = self.imageLabel.pixmap()
            self.resize(pxm.width() + 50, pxm.height() + 150)

            self.viewer_parent.signalChangeValidTime.connect(self.changeValidTime)

        else:
            self.imageLabel.clear()
            self.imageLabel.setText("retrieval was unsuccessful.")
            self.imageLabel.adjustSize()

        # Close the progress dialog.
        self.pdlg.close()

    def updateLabel(self, time=None):
        """Update the color and font style of the information label, depending
           on the time synchronization status of the currently displayed piymap.

        If an external time signal has been passed determine whether this
        widget is synchronized with the global valid time. If not, the
        label is shown in red.
        """
        if time:
            if time != self.valid_time:
                self.synchronized = False
            else:
                self.synchronized = True
        colour = "black" if self.synchronized else "red"
        self.lblInfo.setText(u"<font style='color: {};'><b>VT: {}, LVL: {}</b></font>"
                             .format(colour,
                                     self.valid_time.strftime("%Y-%m-%d %H:%M UTC"),
                                     self.levels[self.current_level]))

    def updateImage(self, time=None):
        """Update the displayed pixmap.
        """
        self.pixmap, self.valid_time = \
            self.pixmaps[self.current_level][self.current_pixmap]
        self.imageLabel.setPixmap(self.pixmap)
        self.updateLabel(time)

    def changeValidTime(self, forward, time=None):
        """Update the displayed image when the current valid time has been
           changed by either

         a) wheelOnImage signal of the LoopLabel.
         b) changeValidTime signal of the parent window.
        """
        # logging.debug("Widget #%i: received changeValidTime %s / %s" % \
        #              (self.id, "fwd" if forward else "back", time))

        if not self.retrieval_successful:
            return

        # If the transmitted time equals the currently displayed time nothing
        # needs to be done.
        if time == self.valid_time:
            self.updateLabel(time)
            return

        # Update image pointer:
        if time is None:
            # A) The easy case, no time information has been passed: Increment
            # or decrement image pointer unless we are at the end or beginning
            # of the image series.
            if forward:
                if self.current_pixmap < len(self.pixmaps[self.current_level]) - 1:
                    self.current_pixmap += 1
            else:
                if self.current_pixmap > 0:
                    self.current_pixmap -= 1
            # We assign the global valid time now, so we are synchronized.
            self.synchronized = True
        else:
            # B) The more difficult case, time information has been passed and
            # needs to be synchronized.
            if forward:
                while self.current_pixmap < len(self.pixmaps[self.current_level]) - 1 \
                        and (time - self.valid_time) > \
                        (self.pixmaps[self.current_level][self.current_pixmap + 1][1] - time):
                    self.current_pixmap += 1
                    self.valid_time = self.pixmaps[self.current_level][self.current_pixmap][1]
            else:
                while self.current_pixmap > 0 and (self.valid_time - time) > \
                        (time - self.pixmaps[self.current_level][self.current_pixmap - 1][1]):
                    self.current_pixmap -= 1
                    self.valid_time = self.pixmaps[self.current_level][self.current_pixmap][1]

        # Display image and update internal pointers to current pixmap and time.
        self.updateImage(time)
        # Emit a changeValidTime signal to inform the other image views
        # of the time change.
        if time is None:
            self.changeValidTime.emit(forward, self.valid_time)

    def changeLevel(self, up):
        """Change the current level. Called on either
        a) one of the up/down buttons has been clicked
        b) shift+wheel has been observed on the image.
        """
        if not self.retrieval_successful:
            return
        if not up:
            if self.current_level < len(self.pixmaps) - 1:
                self.current_level += 1
        else:
            if self.current_level > 0:
                self.current_level -= 1
        self.updateImage()

    def mouseDoubleClickEvent(self, event):
        """A double click on the widget opens the product chooser dialog
           and lets the user load new images.
        """
        result = self.products_dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            self.loadDataFromHTTP(self.products_dialog.type(),
                                  self.products_dialog.product(),
                                  self.products_dialog.region(),
                                  self.products_dialog.initTime())
        event.accept()
