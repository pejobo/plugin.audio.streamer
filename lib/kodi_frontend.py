"""Kodi specific classes"""

import sys
import urllib
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from lib.addon import Frontend
from lib.addon import Backend

class KodiFrontend(Frontend):
    """Kodi frontend"""

    def __init__(self):
        Frontend.__init__(self)
        # 'plugin://plugin.audio.xxx/'
        self._addon_url = sys.argv[0]
        try:
            # 'plugin.audio.xxx'
            self._addon_name = sys.argv[0].split('/')[2]
        except IndexError:
            self._addon_name = ''
        self._addon_handle = int(sys.argv[1])
        xbmcplugin.setPluginCategory(self._addon_handle, "Audio")

    def log(self, message):
        if self._debug:
            xbmc.log(str(message), xbmc.LOGNOTICE)

    def get_setting(self, name):
        addon = xbmcaddon.Addon(self._addon_name)
        return addon.getSetting(name)

    @staticmethod
    def _to_unicode(text):
        result = text
        if isinstance(text, str):
            result = text.decode('utf-8')
        return result

    def get_keyboard_input(self, message):
        """Request user input"""
        dialog = xbmcgui.Dialog()
        result = dialog.input(self._to_unicode(message), self._to_unicode(''), type=xbmcgui.INPUT_ALPHANUM)
        return self._to_unicode(result).strip()

    def render(self, items):
        xbmcplugin.addSortMethod(self._addon_handle, xbmcplugin.SORT_METHOD_NONE)
        entries = []
        try:
            for item in items:
                entries.append(self._render_item(item))
        finally:
            xbmcplugin.addDirectoryItems(self._addon_handle, entries, len(entries))
            xbmcplugin.endOfDirectory(self._addon_handle)

    def _render_item(self, item):
        """render a single item"""
        list_item = xbmcgui.ListItem()
        if Backend.THUMB in item:
            thumb = item[Backend.THUMB]
            list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})
        if Backend.URL in item:
            list_item.setLabel(item[Backend.TRACK_TITLE])
            list_item.setLabel2('%s - %s (%s)' % (
                item[Backend.ARTIST],
                item[Backend.ALBUM_NAME],
                item[Backend.YEAR]))
            list_item.setProperty('IsPlayable', 'true')
            list_item.setProperty('mimetype', 'audio/mpeg')
            music_info = {
                'title': item[Backend.TRACK_TITLE],
                'artist': item[Backend.ARTIST],
                'album': item[Backend.ALBUM_NAME],
                'duration': item[Backend.DURATION]
            }
            if Backend.YEAR in item:
                music_info['year'] = item[Backend.YEAR]
            if Backend.TRACK_NUM in item:
                music_info['tracknumber'] = item[Backend.TRACK_NUM]
            list_item.setInfo('music', music_info)
            return (item[Backend.URL], list_item, False)
        else:
            list_item.setLabel(item[Backend.LABEL])
            url = self.build_url(item[Backend.TARGET])
            self.log(('directory-entry ', url))
            return (url, list_item, True)

    def build_url(self, params):
        return self._addon_url + '?' + urllib.urlencode(params)
