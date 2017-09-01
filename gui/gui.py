import sys
import json
from traceback import format_exc

import upnpclient
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox, QTreeWidgetItem
)

from ui_scan import Ui_uPnPScannerForm

app = QApplication(sys.argv)
window = QDialog()


class ActionItem(QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        super(ActionItem, self).__init__(*args, **kwargs)
        self.service = None
        self.action = None


class ScanForm(Ui_uPnPScannerForm):
    def setupUi(self, *args, **kwargs):
        super(ScanForm, self).setupUi(*args, **kwargs)

        self.devices = {}

        self.connectButton.clicked.connect(self.connect_button_clicked)
        self.scanButton.clicked.connect(self.scan_button_clicked)
        self.resultTree.itemDoubleClicked.connect(self.action_double_clicked)

    def scan_button_clicked(self):
        self.resultTree.clear()
        self.devices = {}
        devices = upnpclient.discover()
        for device in devices:
            self.add_device(device)

    def connect_button_clicked(self):
        url = self.serverUrl.text()
        try:
            print("Looking up service details for %r..." % url)
            device = upnpclient.Device(url)
        except Exception as exc:
            print("Failure :(")
            print(exc)
            msgbox = QMessageBox()
            msgbox.setText("Doh")
            msgbox.setInformativeText(str(exc))
            msgbox.exec_()
            return
        self.add_device(device)

    def add_device(self, device):
        self.devices[device.device_name] = device
        device_item = QTreeWidgetItem(
            self.resultTree,
            ["%s (%s)" % (device.friendly_name, device.device_name)]
        )
        for svc in device.services:
            service_item = QTreeWidgetItem(device_item, [svc.service_id])
            for action in svc.actions:
                ai = ActionItem(service_item, [action.name])
                ai.service = svc
                ai.action = action


    def action_double_clicked(self, item, col_no):
        mb = QMessageBox()
        try:
            res = item.action()
            mb.setText(item.action.name)
            mb.setInformativeText(json.dumps(res, indent=2))
        except Exception as exc:
            mb.setText("Doh")
            mb.setInformativeText(str(exc))
            print(format_exc())
        mb.exec_()

if __name__ == "__main__":
    ui = ScanForm()
    ui.setupUi(window)

    window.show()
    sys.exit(app.exec_())
