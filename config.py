#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2014, Jim Miller'
__docformat__ = 'restructuredtext en'

import traceback, copy

try:
    from PyQt5.Qt import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                          QCheckBox, QPushButton, QTabWidget, QScrollArea)
except ImportError as e:
    from PyQt4.Qt import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                          QCheckBox, QPushButton, QTabWidget, QScrollArea)

from calibre.gui2 import dynamic, info_dialog
from calibre.gui2.ui import get_gui

# pulls in translation files for _() strings
try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from calibre_plugins.smarteject.common_utils \
    import ( get_library_uuid, KeyboardConfigDialog, PrefsViewerDialog )

PREFS_NAMESPACE = 'SmartEjectPlugin'
PREFS_KEY_SETTINGS = 'settings'

# Set defaults used by all.  Library specific settings continue to
# take from here.
default_prefs = {}
default_prefs['checkreadinglistsync'] = True
default_prefs['checkdups'] = True
default_prefs['checknotinlibrary'] = True
default_prefs['checknotondevice'] = True
default_prefs['checkdups_search'] = 'ondevice:"("'
default_prefs['checknotinlibrary_search'] = 'inlibrary:False'
default_prefs['checknotondevice_search'] = 'not ondevice:"~[a-z]"'

def set_library_config(library_config):
    get_gui().current_db.prefs.set_namespaced(PREFS_NAMESPACE,
                                              PREFS_KEY_SETTINGS,
                                              library_config)
    
def get_library_config():
    db = get_gui().current_db
    library_id = get_library_uuid(db)
    library_config = db.prefs.get_namespaced(PREFS_NAMESPACE, PREFS_KEY_SETTINGS,
                                             copy.deepcopy(default_prefs))
    return library_config

# fake out so I don't have to change the prefs calls anywhere.  The
# Java programmer in me is offended by op-overloading, but it's very
# tidy.
class PrefsFacade():
    def __init__(self):
        self.libraryid = None
        self.current_prefs = None
        
    def _get_prefs(self):
        libraryid = get_library_uuid(get_gui().current_db)
        if self.current_prefs == None or self.libraryid != libraryid:
            #print("self.current_prefs == None(%s) or self.libraryid != libraryid(%s)"%(self.current_prefs == None,self.libraryid != libraryid))
            self.libraryid = libraryid
            self.current_prefs = get_library_config()
        return self.current_prefs
        
    def __getitem__(self,k):            
        prefs = self._get_prefs()
        if k not in prefs:
            return default_prefs[k]
        return prefs[k]

    def __setitem__(self,k,v):
        prefs = self._get_prefs()
        prefs[k]=v
        # self._save_prefs(prefs)

    def __delitem__(self,k):
        prefs = self._get_prefs()
        if k in prefs:
            del prefs[k]

    def save_to_db(self):
        set_library_config(self._get_prefs())

prefs = PrefsFacade()
    
class ConfigWidget(QWidget):

    def __init__(self, plugin_action):
        QWidget.__init__(self)
        self.plugin_action = plugin_action
        
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        tab_widget = QTabWidget(self)
        self.l.addWidget(tab_widget)

        self.basic_tab = BasicTab(self, plugin_action)
        tab_widget.addTab(self.basic_tab, _('Basic'))

        self.searches_tab = SearchesTab(self, plugin_action)
        tab_widget.addTab(self.searches_tab, _('Searches'))

    def save_settings(self):
        prefs['checkreadinglistsync'] = self.basic_tab.checkreadinglistsync.isChecked()
        prefs['checkdups'] = self.basic_tab.checkdups.isChecked()
        prefs['checknotinlibrary'] = self.basic_tab.checknotinlibrary.isChecked()
        prefs['checknotondevice'] = self.basic_tab.checknotondevice.isChecked()

        prefs['checkdups_search'] = unicode(self.searches_tab.checkdups_search.text())
        prefs['checknotinlibrary_search'] = unicode(self.searches_tab.checknotinlibrary_search.text())
        prefs['checknotondevice_search'] = unicode(self.searches_tab.checknotondevice_search.text())

        prefs.save_to_db()
        
    def edit_shortcuts(self):
        self.save_settings()
        d = KeyboardConfigDialog(self.plugin_action.gui, self.plugin_action.action_spec[0])
        if d.exec_() == d.Accepted:
            self.plugin_action.gui.keyboard.finalize()

class BasicTab(QWidget):

    def __init__(self, parent_dialog, plugin_action):
        QWidget.__init__(self)
        self.parent_dialog = parent_dialog
        self.plugin_action = plugin_action
        
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        label = QLabel(_('When Ejecting a Device, Check for:'))
        label.setWordWrap(True)
        self.l.addWidget(label)
        #self.l.addSpacing(5)
        
        scrollable = QScrollArea()
        scrollcontent = QWidget()
        scrollable.setWidget(scrollcontent)
        scrollable.setWidgetResizable(True)
        self.l.addWidget(scrollable)

        self.sl = QVBoxLayout()
        scrollcontent.setLayout(self.sl)
        
        self.checkreadinglistsync = QCheckBox(_('Reading List books to Sync'),self)
        self.checkreadinglistsync.setToolTip(_('Check Reading List plugin for books ready to Sync to the current device.'))
        self.checkreadinglistsync.setChecked(prefs['checkreadinglistsync'])
        self.sl.addWidget(self.checkreadinglistsync)
        if 'Reading List' not in plugin_action.gui.iactions:
            self.checkreadinglistsync.setEnabled(False)
        
        self.checkdups = QCheckBox(_('Duplicated Books'),self)
        self.checkdups.setToolTip(_('Check for books that are on the device more than once.'))
        self.checkdups.setChecked(prefs['checkdups'])
        self.sl.addWidget(self.checkdups)
        
        self.checknotinlibrary = QCheckBox(_('Deleted Books (not in Library)'),self)
        self.checknotinlibrary.setToolTip(_('Check for books on the device that are not in the current library.'))
        self.checknotinlibrary.setChecked(prefs['checknotinlibrary'])
        self.sl.addWidget(self.checknotinlibrary)
        
        self.checknotondevice = QCheckBox(_('Added Books (not on Device)'),self)
        self.checknotondevice.setToolTip(_('Check for books in the current library that are not on the device.'))
        self.checknotondevice.setChecked(prefs['checknotondevice'])
        self.sl.addWidget(self.checknotondevice)
                
        self.sl.insertStretch(-1)
        
        self.l.addSpacing(15)        

        label = QLabel(_("These controls aren't plugin settings as such, but convenience buttons for setting Keyboard shortcuts and viewing all plugins settings."))
        label.setWordWrap(True)
        self.l.addWidget(label)
        self.l.addSpacing(5)
        
        keyboard_shortcuts_button = QPushButton(_('Keyboard shortcuts...'), self)
        keyboard_shortcuts_button.setToolTip(_('Edit the keyboard shortcuts associated with this plugin'))
        keyboard_shortcuts_button.clicked.connect(parent_dialog.edit_shortcuts)
        self.l.addWidget(keyboard_shortcuts_button)
                
        view_prefs_button = QPushButton(_('&View library preferences...'), self)
        view_prefs_button.setToolTip(_('View data stored in the library database for this plugin'))
        view_prefs_button.clicked.connect(self.view_prefs)
        self.l.addWidget(view_prefs_button)
        
    def view_prefs(self):
        d = PrefsViewerDialog(self.plugin_action.gui, PREFS_NAMESPACE)
        d.exec_()
        
    def reset_dialogs(self):
        for key in dynamic.keys():
            if key.startswith('smarteject_') and key.endswith('_again') \
                                                  and dynamic[key] is False:
                dynamic[key] = True
        info_dialog(self, _('Done'),
                    _('Confirmation dialogs have all been reset'),
                    show=True,
                    show_copy_button=False)

class SearchesTab(QWidget):

    def __init__(self, parent_dialog, plugin_action):
        QWidget.__init__(self)
        self.parent_dialog = parent_dialog
        self.plugin_action = plugin_action
        
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        label = QLabel(_('Searches to use for:'))
        label.setWordWrap(True)
        self.l.addWidget(label)
        #self.l.addSpacing(5)
        
        scrollable = QScrollArea()
        scrollcontent = QWidget()
        scrollable.setWidget(scrollcontent)
        scrollable.setWidgetResizable(True)
        self.l.addWidget(scrollable)

        self.sl = QVBoxLayout()
        scrollcontent.setLayout(self.sl)

        
        self.sl.addWidget(QLabel(_("Search for Duplicated Books:")))
        self.checkdups_search = QLineEdit(self)
        self.sl.addWidget(self.checkdups_search)
        self.checkdups_search.setText(prefs['checkdups_search'])
        self.checkdups_search.setToolTip(_('Default is %s')%default_prefs['checkdups_search'])
        self.sl.addSpacing(5)
        
        self.sl.addWidget(QLabel(_("Deleted Books (not in Library):")))
        self.checknotinlibrary_search = QLineEdit(self)
        self.sl.addWidget(self.checknotinlibrary_search)
        self.checknotinlibrary_search.setText(prefs['checknotinlibrary_search'])
        self.checknotinlibrary_search.setToolTip(_('Default is %s')%default_prefs['checknotinlibrary_search'])
        self.sl.addSpacing(5)
        
        self.sl.addWidget(QLabel(_("Added Books (not on Device):")))
        self.checknotondevice_search = QLineEdit(self)
        self.sl.addWidget(self.checknotondevice_search)
        self.checknotondevice_search.setText(prefs['checknotondevice_search'])
        self.checknotondevice_search.setToolTip(_('Default is %s')%default_prefs['checknotondevice_search'])
                        
        self.sl.insertStretch(-1)
        
        self.l.addSpacing(15)        

        restore_defaults_button = QPushButton(_('Restore Defaults'), self)
        restore_defaults_button.setToolTip(_('Revert all searches to the defaults.'))
        restore_defaults_button.clicked.connect(self.restore_defaults_button)
        self.l.addWidget(restore_defaults_button)


    def restore_defaults_button(self):
        self.checkdups_search.setText(default_prefs['checkdups_search'])
        self.checknotinlibrary_search.setText(default_prefs['checknotinlibrary_search'])
        self.checknotondevice_search.setText(default_prefs['checknotondevice_search'])
