# -*- coding: utf-8 -*-
# Requires: pip install PySide6

import sys
import random
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
)

import cnc_api_client_core as core

class WcsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("WCS Monitor")
        self.resize(800, 420)

        # Current WCS in use (integer)
        self.wcs_in_use = 1

        # Label: "WCS in use : %d"
        self.lbl_wcs = QLabel(self)

        # Table: 10 x 6
        self.table = QTableWidget(10, 6, self)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)  # allow manual edits if needed

        # Headers
        self.table.setHorizontalHeaderLabels(["X","Y","Z","A","B","C",])
        self.table.setVerticalHeaderLabels(
            [
                "Working WCS",
                "WCS 1 - [G54]",
                "WCS 2 - [G55]",
                "WCS 3 - [G56]",
                "WCS 4 - [G57]",
                "WCS 5 - [G58]",
                "WCS 6 - [G59]",
                "WCS 7 - [G59.1]",
                "WCS 8 - [G59.2]",
                "WCS 9 - [G59.3]",
            ]
        )

        # allow manual edits if needed
        # self.table.setEditTriggers(QTableWidget.AllEditTriggers)

        # read-only
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # not selectionable
        self.table.setSelectionMode(QTableWidget.NoSelection)

        # Make columns stretch nicely
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)

        # Initialize cells
        for r in range(10):
            for c in range(6):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl_wcs)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # Timer to update cells
        self.timer = QTimer(self)
        self.timer.setInterval(500)  # ms
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start()

        #
        self.cnc = core.CncAPIClientCore()
        self.cnc.connect('127.0.0.1', 8000)

    def set_active_wcs_header_bold(self, working_wcs: int):
        # Map: WCS 1..9 -> table row 1..9 (row 0 is "Working WCS")
        active_row = int(working_wcs)
        if active_row < 1 or active_row > 9:
            active_row = -1  # nothing highlighted

        for r in range(self.table.rowCount()):
            hdr = self.table.verticalHeaderItem(r)
            if hdr is None:
                hdr = QTableWidgetItem(self.table.verticalHeaderItem(r).text() if self.table.verticalHeaderItem(r) else "")
                self.table.setVerticalHeaderItem(r, hdr)

            f = hdr.font()
            f.setBold(r == active_row)
            hdr.setFont(f)

    def on_timer_tick(self):
        cs_info = self.cnc.get_coordinate_systems_info()

        working_wcs = cs_info.working_wcs
        self.lbl_wcs.setText(f"WCS in use : {working_wcs:d}")

        self.set_active_wcs_header_bold(working_wcs)


        for r in range(self.table.rowCount()):
            if r == 0:
                offsets = cs_info.working_offset
            else:
                offsets = getattr(cs_info, f"wcs_{r}")
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item is None:
                    item = QTableWidgetItem()
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, c, item)
                item.setText(str(offsets[c]))

        # Example: change WCS every tick (or comment this out)
        self.wcs_in_use = 1 + (self.wcs_in_use % 9)


def main():
    app = QApplication(sys.argv)
    dlg = WcsDialog()
    dlg.exec()


if __name__ == "__main__":
    main()
