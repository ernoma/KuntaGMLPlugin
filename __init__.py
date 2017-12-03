# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KuntaGMLtoQGIS
                                 A QGIS plugin
 Support to load KuntaGML features directly from WFS API's to QGIS
                             -------------------
        begin                : 2017-12-03
        copyright            : (C) 2017 by Gispo Oy
        email                : erno@gispo.fi
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
    """Load KuntaGMLtoQGIS class from file KuntaGMLtoQGIS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .kuntagml_to_qgis import KuntaGMLtoQGIS
    return KuntaGMLtoQGIS(iface)
