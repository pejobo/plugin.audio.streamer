from lib.addon import Addon
from lib.deezerbackend import DeezerBackend
from lib.kodi_frontend import KodiFrontend

kodi = KodiFrontend()
deezer = DeezerBackend(kodi)
Addon(deezer, kodi, debug=True).main()