# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KuntaGMLtoQGIS
                                 A QGIS plugin
 Support to load KuntaGML features directly from WFS API's to QGIS
                              -------------------
        begin                : 2017-12-03
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Gispo Oy
        email                : erno@gispo.fi
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from kuntagml_to_qgis_dialog import KuntaGMLtoQGISDialog
import os.path

from qgis.core import *
from qgis.gui import *

import requests
import os
from osgeo import ogr
import codecs

class KuntaGMLtoQGIS:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'KuntaGMLtoQGIS_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&KuntaGML to QGIS plugin')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'KuntaGMLtoQGIS')
        self.toolbar.setObjectName(u'KuntaGMLtoQGIS')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('KuntaGMLtoQGIS', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = KuntaGMLtoQGISDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/KuntaGMLtoQGIS/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Get KuntaGML data'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&KuntaGML to QGIS plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            base_url = str(self.dlg.baseURLComboBox.currentText())
            feature = str(self.dlg.featureTypeComboBox.currentText())
            srs = str(self.dlg.SRSComboBox.currentText())
            wfs_version = "1.1.0"

            QgsMessageLog.logMessage(str(base_url), 'KuntaGMLPlugin', QgsMessageLog.INFO)
            QgsMessageLog.logMessage(str(feature), 'KuntaGMLPlugin', QgsMessageLog.INFO)
            QgsMessageLog.logMessage(str(srs), 'KuntaGMLPlugin', QgsMessageLog.INFO)
            QgsMessageLog.logMessage(str(wfs_version), 'KuntaGMLPlugin', QgsMessageLog.INFO)

            get_params = {
                'REQUEST': 'GetFeature',
                'SERVICE': 'WFS',
                'VERSION': wfs_version,
                'TYPENAME': feature,
                'SRS': srs}

            #print(base_url)

            response = requests.get(base_url, params=get_params)
            response.raise_for_status()
            QgsMessageLog.logMessage("Requested " + response.url, 'KuntaGMLPlugin', QgsMessageLog.INFO)
            QgsMessageLog.logMessage(response.encoding, 'KuntaGMLPlugin', QgsMessageLog.INFO)
            #response.encoding = 'ISO-8859-1'
            response.encoding = 'UTF-8'
            #print(response.text)

            #
            # Create file name that is based on the script arguments, that follows somewhat how 
            # the GDAL gmlas driver caches the schema files
            #
            url_parts = base_url.split('/')
            file_name_start = url_parts[2] + '_' + wfs_version + '_' + srs + '_' + feature
            QgsMessageLog.logMessage("Names of the files stored in the dir start with " + file_name_start, 'KuntaGMLPlugin', QgsMessageLog.INFO)


            #file_name = file_name_start + '_orig.gml'
            #with codecs.open(file_name, 'w', encoding='UTF-8') as file:
            #        file.write(response.text)

            #
            # NOTE: Since we cannot trust the GML document and it's XML is valid,
            # it is not totally safe to assume that parsing with a XML parser is successful.
            # Besides search and replace of the text is easier, so below this approach...
            # NOTE: The http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/yhteiset_2.1.6.xsd is equal to the
            # http://www.paikkatietopalvelu.fi/gml/yhteiset/2.1.6/yhteiset.xsd except the - has been
            # corrected to the \- in the lines 3283 and 3778, and
            # the http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/asemakaava_2.1.1.xsd points to the gispogdalkuntagml/yhteiset_2.1.6.xsd.
            # The  replacement is probably not needed in the future when
            # KuntaGML yhteiset.xsd is corrected to encode special characters correctly and the change
            # https://trac.osgeo.org/gdal/changeset/40429 mentioned in the
            # http://osgeo-org.1560.x6.nabble.com/gdal-dev-Namespaces-in-GMLAS-td5338379.html
            # is taken into use.

            text = response.text
            if feature.startswith('akaava:'):
                text = text.replace('xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd http://www.tekla.com/schemas/kuntagml ' + base_url + '?SERVICE=WFS&amp;VERSION=' + wfs_version + '&amp;REQUEST=DescribeFeatureType&amp;typeName=' + feature + ' "', 'xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/' + wfs_version + '/wfs.xsd http://www.paikkatietopalvelu.fi/gml/asemakaava http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/asemakaava_2.1.1.xsd http://www.paikkatietopalvelu.fi/gml/yhteiset http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/yhteiset_2.1.6.xsd http://www.ymparisto.fi http://www.paikkatietopalvelu.fi/gml/asemakaava/1.2.6/KatseDetailPlan.xsd"')
            elif feature.startswith('kanta:'):
                text = text.replace('xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd http://www.tekla.com/schemas/kuntagml ' + base_url + '?SERVICE=WFS&amp;VERSION=' + wfs_version + '&amp;REQUEST=DescribeFeatureType&amp;typeName=' + feature + ' "', 'xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/' + wfs_version + '/wfs.xsd http://www.paikkatietopalvelu.fi/gml/kantakartta http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/kantakartta_2.1.1.xsd http://www.paikkatietopalvelu.fi/gml/yhteiset http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/yhteiset_2.1.6.xsd http://www.ymparisto.fi http://www.paikkatietopalvelu.fi/gml/asemakaava/1.2.6/KatseDetailPlan.xsd"')
            elif feature.startswith('mkos:'):
                text = text.replace('xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd http://www.tekla.com/schemas/kuntagml ' + base_url + '?SERVICE=WFS&amp;VERSION=' + wfs_version + '&amp;REQUEST=DescribeFeatureType&amp;typeName=' + feature + ' "', 'xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/' + wfs_version + '/wfs.xsd http://www.paikkatietopalvelu.fi/gml/opastavattiedot/osoitteet http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/osoitteet_2.1.1.xsd http://www.paikkatietopalvelu.fi/gml/yhteiset http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/yhteiset_2.1.6.xsd http://www.ymparisto.fi http://www.paikkatietopalvelu.fi/gml/asemakaava/1.2.6/KatseDetailPlan.xsd"')
            elif feature.startswith('mkok:'):
                text = text.replace('xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd http://www.tekla.com/schemas/kuntagml ' + base_url + '?SERVICE=WFS&amp;VERSION=' + wfs_version + '&amp;REQUEST=DescribeFeatureType&amp;typeName=' + feature + ' "', 'xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/' + wfs_version + '/wfs.xsd http://www.paikkatietopalvelu.fi/gml/opastavattiedot/opaskartta http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/opaskartta_2.1.1.xsd http://www.paikkatietopalvelu.fi/gml/yhteiset http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/yhteiset_2.1.6.xsd http://www.ymparisto.fi http://www.paikkatietopalvelu.fi/gml/asemakaava/1.2.6/KatseDetailPlan.xsd"')
            #elif feature.startswith('rakval:'):
            #   text = text.replace('xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd http://www.tekla.com/schemas/kuntagml ' + base_url + '?SERVICE=WFS&amp;VERSION=' + wfs_version + '&amp;REQUEST=DescribeFeatureType&amp;typeName=' + feature + ' "', 'xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/' + wfs_version + '/wfs.xsd http://www.paikkatietopalvelu.fi/gml/rakennusvalvonta http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/rakennusvalvonta_2.2.0.xsd http://www.paikkatietopalvelu.fi/gml/yhteiset http://s3.eu-central-1.amazonaws.com/gispogdalkuntagml/yhteiset_2.1.6.xsd http://www.ymparisto.fi http://www.paikkatietopalvelu.fi/gml/asemakaava/1.2.6/KatseDetailPlan.xsd"')
            else:
                print("Turku did not have the specified feature publicly available when this script was created (Dec 2017). Feature type not supported by the script.")

            self.path = os.path.dirname(__file__)

            file_name_mod = file_name_start + '_mod.gml'

            with codecs.open(os.path.join(self.path, "data", file_name_mod), 'w', 'UTF-8') as file:
                file.write(text)

            final_file_path = os.path.join(self.path, "data", file_name_start)

            # NOTE: parameter HANDLE_MULTIPLE_IMPORTS=YES seems to do opposite to what it should in version 2.2.2+dfsg-1~xenial1
            # Also, GDAL 2.1.3 does not seem to support this ogr2ogr call at all
            ogr2ogr_convert_params = "-dim 2 -nlt convert_to_linear" \
                + " -oo REMOVE_UNUSED_LAYERS=YES" \
                + " -oo REMOVE_UNUSED_FIELDS=YES" \
                + " -oo EXPOSE_METADATA_LAYERS=YES" \
                #+ " --debug on" #\
                #+ " -oo HANDLE_MULTIPLE_IMPORTS=YES"

            #command = "ogr2ogr -f GPKG " + final_file_path + ".gpkg" + " gmlas:" + file_name_mod + " " + ogr2ogr_convert_params
            #print("calling: " + command)
            #os.system(command)
            command = "ogr2ogr -f sqlite -dsco spatialite=yes " + final_file_path + ".sqlite" + " gmlas:" + os.path.join(self.path, "data", file_name_mod) + " " + ogr2ogr_convert_params
            QgsMessageLog.logMessage("calling: " + command, 'KuntaGMLPlugin', QgsMessageLog.INFO)
            os.system(command)
