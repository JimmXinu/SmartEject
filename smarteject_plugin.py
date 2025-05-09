#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2019, Jim Miller'
__docformat__ = 'restructuredtext en'

from calibre.gui2 import question_dialog

# The class that all interface action plugins must inherit from
from calibre.gui2.actions import InterfaceAction

from calibre_plugins.smarteject.common_utils import get_icon
from calibre_plugins.smarteject.config import prefs, default_prefs

# pulls in translation files for _() strings
try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

# PLUGIN_ICONS = ['images/icon.png']

class SmartEjectPlugin(InterfaceAction):

    name = 'SmartEject'

    # Declare the main action associated with this plugin
    # The keyboard shortcut can be None if you dont want to use a keyboard
    # shortcut. Remember that currently calibre has no central management for
    # keyboard shortcuts, so try to use an unusual/unused shortcut.
    # (text, icon_path, tooltip, keyboard shortcut)
    # icon_path isn't in the zip--icon loaded below.
    action_spec = (_('SmartEject'), None,
                   _('Check for duplicated/deleted/added books before ejecting.'), ())
    # None for keyboard shortcut doesn't allow shortcut.  () does, there just isn't one yet

    action_type = 'global'
    # make button menu drop down only
    #popup_type = QToolButton.InstantPopup

    #: Set of locations to which this action must not be added.
    #: See :attr:`all_locations` for a list of possible locations
    dont_add_to = frozenset(['toolbar', 'context-menu', 'toolbar-child',
                             'context-menu-device', 'menubar',
                             'context-menu-cover-browser'])

    def genesis(self):

        # This method is called once per plugin, do initial setup here

        base = self.interface_action_base_plugin
        self.version = base.name+" v%d.%d.%d"%base.version

        # Set the icon for this interface action
        # The get_icons function is a builtin function defined for all your
        # plugin code. It loads icons from the plugin zip file. It returns
        # QIcon objects, if you want the actual data, use the analogous
        # get_resources builtin function.

        # Note that if you are loading more than one icon, for performance, you
        # should pass a list of names to get_icons. In this case, get_icons
        # will return a dictionary mapping names to QIcons. Names that
        # are not found in the zip file will result in null QIcons.
        icon = get_icon('eject.png')

        self.qaction.setText(_('SmartEject'))
        # The qaction is automatically created from the action_spec defined
        # above
        self.qaction.setIcon(icon)

        # Call function when plugin triggered.
        self.qaction.triggered.connect(self.plugin_button)

    def plugin_button(self):
        if not self.gui.device_manager.is_device_present:
            # no device connected, silently skip.
            return

        if 'Reading List' in self.gui.iactions and ( prefs['checkreadinglistsync']
                                                     or prefs['checkreadinglistsyncfromdevice']):
            rl_plugin = self.gui.iactions['Reading List']
            list_names = rl_plugin.get_list_names(exclude_auto=True)
            all_list_names = rl_plugin.get_list_names(exclude_auto=False)
            auto_list_names = list(set(all_list_names) - set(list_names))
            if self.gui.device_manager.is_device_connected:
                sync_total = rl_plugin._count_books_for_connected_device()
                ## why is this setting the enabled for RL?
                ## Probably RL's rebuild_menus hasn't been called
                # print(all_list_names)
                # print(auto_list_names)
                # print(sync_total)
                rl_plugin.sync_now_action.setEnabled(bool(sync_total > 0) or len(auto_list_names) > 0)
                if sync_total > 0 and prefs['checkreadinglistsync']:
                    if question_dialog(self.gui, _("Sync Reading List?"), _("There are books that need syncing according to Reading List.<p>Sync Books?"), show_copy_button=False):
                        rl_plugin.sync_now(force_sync=True)
                        return
                elif len(auto_list_names) > 0 and prefs['checkreadinglistsyncfromdevice']:
                    if prefs['silentsyncfromdevice'] or question_dialog(self.gui, _("Sync Now Reading List?"), _("There are lists that could be sync'ed according to Reading List.<p>Sync before ejecting?"), show_copy_button=False):
                        # print("doreadinglistsync")
                        rl_plugin.sync_now(force_sync=True)

        if prefs['checkdups']:
            # As of Calibre 5.42, the duplicate search needs to change.
            # Automatically change it if it's the old default search.
            if prefs['checkdups_search'] == 'ondevice:"("':
                prefs['checkdups_search'] = default_prefs['checkdups_search']
                print("checkdups_search changed to new default value.")
                prefs.save_to_db()
            if self.gui.library_view.model().db.search_getting_ids(prefs['checkdups_search'], None):
                dodelete = prefs['deletedups']
                if dodelete:
                    qtext = _("There are duplicate ebooks on the device.<p>Delete duplicates?  (Make sure you uncheck the ones you want to keep).")
                else:
                    qtext = _("There are duplicate ebooks on the device.<p>Display duplicates?")
                if question_dialog(self.gui, _("Duplicates on Device"), qtext, show_copy_button=False):
                    self.gui.location_manager._location_selected('library')
                    self.gui.search.setEditText(prefs['checkdups_search'])
                    self.gui.search.do_search()
                    if dodelete:
                        self.gui.library_view.selectAll()
                        self.gui.iactions['Remove Books'].remove_matching_books_from_device()
                    return

        if prefs['checknotinlibrary']:
            devices = [ (self.gui.memory_view, 'Main', 'main'),
                        (self.gui.card_a_view, 'Card A', 'carda'),
                        (self.gui.card_b_view, 'Card B', 'cardb') ]
            for (view, viewname, locationname) in devices:
                model = view.model()
                savesearch = model.last_search
                model.search(prefs['checknotinlibrary_search'])
                if model.count() > 0:
                    dodelete = prefs['deletenotinlibrary']
                    if dodelete:
                        qtext = _("There are books on the device in %s that are not in the Library.<p>Delete books not in Library?")%viewname
                    else:
                        qtext = _("There are books on the device in %s that are not in the Library.<p>Display books not in Library?")%viewname
                    if question_dialog(self.gui, _("Books on Device not in Library"), qtext, show_copy_button=False):
                        self.gui.search.setEditText(prefs['checknotinlibrary_search'])
                        self.gui.search.do_search()
                        self.gui.location_manager._location_selected(locationname)
                        if dodelete:
                            view.selectAll()
                            # remove_matching_books_from_device()
                            # always operates on library_view, can't
                            # use here on device view.
                            self.gui.iactions['Remove Books'].delete_books()
                        return
                model.search(savesearch)
                #print("model.count():%s"%model.count())

        if prefs['checknotondevice'] and self.gui.library_view.model().db.search_getting_ids(prefs['checknotondevice_search'], None):
            dosend = prefs['sendnotondevice']
            if dosend:
                qtext = _("There are books in the Library that are not on the Device.<p>Send books not on Device?")
            else:
                qtext = _("There are books in the Library that are not on the Device.<p>Display books not on Device?")
            if question_dialog(self.gui,
                               _("Books in Library not on Device"),
                               qtext,
                               show_copy_button=False):
                self.gui.location_manager._location_selected('library')
                self.gui.search.setEditText(prefs['checknotondevice_search'])
                self.gui.search.do_search()
                if dosend:
                    self.gui.library_view.selectAll()
                    self.gui.iactions['Send To Device'].do_sync()
                return

        self.gui.location_manager._location_selected('library')

        from calibre.gui2.device import device_name_for_plugboards
        device_name = device_name_for_plugboards(self.gui.device_manager.connected_device.__class__)
        # print(device_name)

        self.gui.location_manager._eject_requested()

        if prefs['stopsmartdevice'] and 'SMART_DEVICE_APP' in device_name:
            self.gui.device_manager.stop_plugin('smartdevice')

        # if one of the configured searchs, clear it.
        #print("self.gui.search.current_text :(%s)"%self.gui.search.current_text )
        if self.gui.search.current_text in (prefs['checkdups_search'],prefs['checknotinlibrary_search'],prefs['checknotondevice_search']):
            self.gui.search.clear()

    def apply_settings(self):
        # No need to do anything with prefs here, but we could.
        prefs
