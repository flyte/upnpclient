# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scan.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_uPnPScannerForm(object):
    def setupUi(self, uPnPScannerForm):
        uPnPScannerForm.setObjectName("uPnPScannerForm")
        uPnPScannerForm.resize(812, 570)
        self.verticalLayoutWidget = QtWidgets.QWidget(uPnPScannerForm)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(9, 9, 791, 551))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.serverUrl = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.serverUrl.setObjectName("serverUrl")
        self.horizontalLayout.addWidget(self.serverUrl)
        self.connectButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.connectButton.setObjectName("connectButton")
        self.horizontalLayout.addWidget(self.connectButton)
        self.scanButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.scanButton.setObjectName("scanButton")
        self.horizontalLayout.addWidget(self.scanButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.resultTree = QtWidgets.QTreeWidget(self.verticalLayoutWidget)
        self.resultTree.setObjectName("resultTree")
        self.resultTree.headerItem().setText(0, "Results")
        self.verticalLayout.addWidget(self.resultTree)

        self.retranslateUi(uPnPScannerForm)
        QtCore.QMetaObject.connectSlotsByName(uPnPScannerForm)

    def retranslateUi(self, uPnPScannerForm):
        _translate = QtCore.QCoreApplication.translate
        uPnPScannerForm.setWindowTitle(_translate("uPnPScannerForm", "uPnP Scanner"))
        self.connectButton.setText(_translate("uPnPScannerForm", "Connect"))
        self.scanButton.setText(_translate("uPnPScannerForm", "Scan"))
