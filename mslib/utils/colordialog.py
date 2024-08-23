# -*- coding: utf-8 -*-
"""

    mslib.utils.colordialog.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Custom Color Dialog to select color from predefined swatches.

    This file is part of MSS.

    :copyright: Copyright 2024 Rohit Prasad
    :copyright: Copyright 2024 by the MSS team, see AUTHORS.
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
import functools
from PyQt5.QtWidgets import QVBoxLayout, QGridLayout
from PyQt5 import QtGui, QtWidgets, QtCore


class CustomColorDialog(QtWidgets.QDialog):
    """
    Custom Color Dialog to select color from predefined swatches.
    """
    color_selected = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Color")
        self.setFixedSize(350, 300)

        self.colors = [
            "#800000", "#c31f59", "#f59757", "#fde442", "#0000ff",
            "#60c36e", "#65d8f2", "#a446be", "#f15aea", "#b9babb",
            "#e6194B", "#d2cf94", "#356e33", "#f58231", "#2c2c2c",
            "#000075", "#9A6324", "#808000", "#000000", "#f8cbdc"
        ]

        layout = QVBoxLayout()
        # Color swatches layout
        swatch_layout = QGridLayout()
        self.color_buttons = []

        for i, color in enumerate(self.colors):
            button = QtWidgets.QPushButton()
            button.setFixedSize(50, 50)
            button.setStyleSheet(f"background-color: {color}")
            button.clicked.connect(functools.partial(self.on_color_clicked, color))
            row = i // 5
            col = i % 5
            swatch_layout.addWidget(button, row, col)
            self.color_buttons.append(button)

        # Add "Pick Custom Color" button
        self.custom_color_button = QtWidgets.QPushButton("Pick Custom Color")
        self.custom_color_button.clicked.connect(self.on_custom_color_clicked)
        self.custom_color_button.setFixedSize(325, 30)

        layout.addLayout(swatch_layout)
        layout.addWidget(self.custom_color_button)
        self.setLayout(layout)

    def on_color_clicked(self, color):
        self.color_selected.emit(QtGui.QColor(color))
        self.accept()

    def on_custom_color_clicked(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.color_selected.emit(color)
            self.accept()
