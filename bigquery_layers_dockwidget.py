# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BigQueryLayersDockWidget
                                 A QGIS plugin
 Add data from BigQuery
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-12-16
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Stefan Mandaric
        email                : stefan.mandaric@unacast.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsMessageLog, Qgis, QgsTask, QgsApplication
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt, pyqtSlot

from .bqloader.bqloader import BigQueryConnector

class EverythingIsFineException(Exception):
    pass


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'bigquery_layers_dockwidget_base.ui'))


class BigQueryLayersDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None, iface=None):
        """Constructor."""
        super(BigQueryLayersDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface

        # Elements associated with base query
        self.base_query_elements = [self.project_edit, self.query_edit, self.run_query_button]

        # Elements associated with layer imports
        self.layer_import_elements = [self.geometry_column_combo_box, self.add_all_button,
                                      self.add_extents_button, self.geometry_column_label]
        for elm in self.layer_import_elements:
            elm.setEnabled(False)

        # Handle button clicks
        self.run_query_button.clicked.connect(self.run_query_handler)
        self.add_all_button.clicked.connect(self.add_layer_button_handler)
        self.add_extents_button.clicked.connect(self.add_layer_button_handler)

        # Changed text
        self.project_edit.textChanged.connect(self.text_changed_handler)
        self.query_edit.textChanged.connect(self.text_changed_handler)

        self.base_query_complete = False


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def text_changed_handler(self):
        self.base_query_complete = False
        self.query_progress_field.clear()
        self.geometry_column_combo_box.clear()

        for elm in self.layer_import_elements:
            elm.setEnabled(False)

    def run_query_handler(self):
        # GUI
        self.base_query_complete = False

        for elm in self.base_query_elements + self.layer_import_elements:
            elm.setEnabled(False)

        self.run_query_button.setText('Running...')
        self.run_query_button.repaint()

        QgsMessageLog.logMessage('Button pressed', 'BQ Layers', Qgis.Info)

        # Run query as a task
        base_query_task = QgsTask.fromFunction('Base query task', self.run_base_query, on_finished=self.base_query_completed)
        QgsApplication.taskManager().addTask(base_query_task)
        QgsMessageLog.logMessage('Button pressed bottom', 'BQ Layers', Qgis.Info)

    def run_base_query(self, task):
        QgsMessageLog.logMessage('Running base query', 'BQ Layers', Qgis.Info)
        project_name = self.project_edit.text()
        query = self.query_edit.toPlainText()
        self.bq = BigQueryConnector()
        self.bq.set_query(query)
        self.bq.run_base_query(project_name)
        # Always return exception. On_finished is broken inside objects
        # https://gis.stackexchange.com/questions/296175/issues-with-qgstask-and-task-manager/304801#304801
        raise EverythingIsFineException()

    def base_query_completed(self, exception, result=None):
        if exception is None:
            # Should always return exception
            QgsMessageLog.logMessage('This should not occur', 'BQ Layers', Qgis.Info)
        else:
            if isinstance(exception, EverythingIsFineException):
                # Query completed without errors
                QgsMessageLog.logMessage('Completed fine', 'BQ Layers', Qgis.Info)

                # Number of rows in query
                rowcount = str(self.bq.num_rows_base())

                # Columns in query
                fields = self.bq.fields()
                self.geometry_column_combo_box.addItems(fields)

                self.query_progress_field.setText('Rows returned: {}'.format(rowcount))
                # self.query_progress_field.adjustSize()

                # Enable all elements
                self.base_query_complete = True
                for elm in self.base_query_elements + self.layer_import_elements:
                    elm.setEnabled(True)
                self.run_query_button.setText('Run query')

            else:
                QgsMessageLog.logMessage('Completed with errors', 'BQ Layers', Qgis.Info)
                self.base_query_complete = False

                # Enable top buttons, import buttons are disabled
                for elm in self.base_query_elements:
                    elm.setEnabled(True)
                self.run_query_button.setText('Run query')
                self.query_progress_field.setText('Errors in base query')
                self.iface.messageBar().pushMessage("BigQuery Layers", "Query failed: " + exception.__repr__(), level=Qgis.Critical)
                QgsMessageLog.logMessage('Running add full layer', 'BQ Layers', Qgis.Info)
                # TODO: Display exception
                raise exception

    def add_full_layer(self, task, uri):
        QgsMessageLog.logMessage('Running add full layer', 'BQ Layers', Qgis.Info)

        layer_file = self.bq.write_base_result()
        self.layer_uri = uri.format(file=layer_file)

        raise EverythingIsFineException()

    def add_extents(self, task, uri, extent_wkt, geom_field):
        QgsMessageLog.logMessage('Running add extent layer', 'BQ Layers', Qgis.Info)

        layer_file = self.bq.write_extent_result(extent_wkt, geom_field)
        self.layer_uri = uri.format(file=layer_file)

        raise EverythingIsFineException()

    def add_layer_button_handler(self):
        assert self.base_query_complete

        geom_field = self.geometry_column_combo_box.currentText()
        uri = 'file://{{file}}?delimiter=,&crs=epsg:4326&wktField={field}'.format(field=geom_field)

        for elm in self.base_query_elements + self.layer_import_elements:
            elm.setEnabled(False)

        if self.sender().objectName() == 'add_all_button':
            QgsMessageLog.logMessage('Pressed add all', 'BQ Layers', Qgis.Info)
            self.add_all_button.setText('Adding layer...')
            task = QgsTask.fromFunction('Add layer', self.add_full_layer, on_finished=self.layer_added, uri=uri)
        elif self.sender().objectName() == 'add_extents_button':
            self.add_extents_button.setText('Adding layer...')
            QgsMessageLog.logMessage('Add layer', 'BQ Layers', Qgis.Info)
            extent = self.iface.mapCanvas().extent()
            crcSource = QgsCoordinateReferenceSystem(3857)
            crcTarget = QgsCoordinateReferenceSystem(4326)
            transform = QgsCoordinateTransform(crcSource, crcTarget, QgsProject.instance())
            extent_wkt = transform.transform(extent).asWktPolygon()
            task = QgsTask.fromFunction('Add layer', self.add_extents, on_finished=self.layer_added,
                                        uri=uri, extent_wkt=extent_wkt, geom_field=geom_field)

        self.run_query_button.repaint()
        QgsApplication.taskManager().addTask(task)
        # For some reason it needs to log in order for tasks to run
        QgsMessageLog.logMessage('After add button', 'BQ Layers', Qgis.Info)

    def layer_added(self, exception, result=None):
        if exception is None:
            # Should always return exception
            QgsMessageLog.logMessage('This should not occur', 'BQ Layers', Qgis.Info)
        else:
            QgsMessageLog.logMessage('Layer added', 'BQ Layers', Qgis.Info)
            if isinstance(exception, EverythingIsFineException):
                # Must be done in main thread
                self.iface.addVectorLayer(self.layer_uri, "Bigquery layer", "delimitedtext")
                self.add_all_button.setText('Add all')
                self.add_extents_button.setText('Add window extents')
            else:
                print(exception)

            for elm in self.base_query_elements + self.layer_import_elements:
                elm.setEnabled(True)


