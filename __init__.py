# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BigQueryLayers
                                 A QGIS plugin
 Add data from BigQuery
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-12-16
        copyright            : (C) 2018 by Stefan Mandaric
        email                : stefan.mandaric@unacast.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load BigQueryLayers class from file BigQueryLayers.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .bigquery_layers import BigQueryLayers
    return BigQueryLayers(iface)
