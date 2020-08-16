import sys
import time

import fs
import mock
import pytest

from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.demodata import create_test_files
from mslib.mscolab.server import APP, db, initialize_managers
from mslib.msui.mscolab import MSSMscolabWindow
from mslib.msui.mss_qt import QtCore, QtTest, QtWidgets


# TODO: FIX THESE TESTS
class Test_Mscolab(object):
    def setup(self):

        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=MSCOLAB_URL_TEST)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)
        create_test_files()

    def teardown(self):
        # to disconnect connections, and clear token
        self.window.disconnect_handler()
        QtWidgets.QApplication.processEvents()
        self.window.close()
        QtWidgets.QApplication.processEvents()
        with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as mss_dir:
            if mss_dir.exists('local_mscolab_data'):
                mss_dir.removetree('local_mscolab_data')
        # self.application.quit()
        # QtWidgets.QApplication.processEvents()

    @pytest.mark.skip(reason="Need to fix test for dialog")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_save_overwrite_to_server(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.overwriteBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_local_wp.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_server_wp.lat

    @pytest.mark.skip(reason="Need to fix test for dialog")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_save_keep_server_points(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.keepServerBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(2)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat != new_local_wp.lat
        assert new_local_wp.lat == wp_server_before.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat == new_server_wp.lat

    @pytest.mark.skip(reason="Need to fix test for dialog")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_save_merge_points(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        self.window.waypoints_model.invert_direction()
        merge_waypoints_model = None

        def handle_merge_dialog():
            nonlocal merge_waypoints_model
            self._select_waypoints(self.window.merge_dialog.localWaypointsTable)
            self._select_waypoints(self.window.merge_dialog.serverWaypointsTable)
            merge_waypoints_model = self.window.merge_dialog.merge_waypoints_model
            QtTest.QTest.mouseClick(self.window.merge_dialog.saveBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(2)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model
        new_wp_count = len(merge_waypoints_model.waypoints)
        assert new_wp_count == 4
        assert len(new_local_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_local_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_server_wp = self.window.waypoints_model
        assert len(new_server_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_server_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat

    @pytest.mark.skip(reason="Need to fix test for dialog")
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_fetch_from_server(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.keepServerBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(2)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.fetch_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model
        assert len(new_local_wp.waypoints) == 2
        assert new_local_wp.waypoint_data(0).lat == wp_server_before.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        assert self.window.waypoints_model.waypoint_data(0).lat == wp_server_before.lat

    def _connect_to_mscolab(self):
        self.window.url.setEditText("http://localhost:8084")
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self, emailid="merge_waypoints_user", password="password"):
        self._connect_to_mscolab()
        self.window.emailid.setText(emailid)
        self.window.password.setText(password)
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _select_waypoints(self, table):
        for row in range(table.model().rowCount()):
            table.selectRow(row)
            QtWidgets.QApplication.processEvents()
