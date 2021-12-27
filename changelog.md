# Pixlovarr Changelog

2021-12-27 14:15:19

Version 1.18.0.2444

* New: PRUNE_CRON added as environment variable. Sets the CRON for pruning. If not set: default is "0 4 * * *"
* New: Prune log gets written to /log (tip: Set Volume in on startup-script)
* New: Prune log gets mailed if enabled in INI file
* New: Pixlovarr log written to /log
* Changed: Container startup
* Changed: Dockerfile to optimize for buildx
* Changed: startup script
* Changed: SHOW_KEPT_MESSAGES was replaced by ONLY_SHOW_REMOVE_MESSAGES

Versioon 1.17.5.2220

* Enabled calenders for Sonarr and Radarr

Version 1.17.5.1822

* Changed: Extensions that are monitored for pruning

Version 1.17.5.1788

* New: /smm search missing movies
* New: Keep button for admins beneath the movieinfo
* New: Language profiles for series

version 1.17.5.1624

* Changed: API from pycliarr to arrApi
* New: Option to extend movie with X days

version 1.16.5.1346

* Changed: The KEEPTAGS are respected for non-Admin users when trying to delete a movie
* Changed: Better handling of "ValueErrors" for the INI file
* New: Option to set if commands issued by an Admin are shown in /sts and /ch
* Changed: Change "Radarr Purge" to "Pixlovarr Prune" (Sorry for the caused trouble
  
version 1.14.5.979

* Fixed: API v3 had bug in build_item_path, temporarily fixed in the __main__
* New: Setting added. Show only largest available drive when downloading. This helps to even fill the drives.
* Bugfix: Check for movie to show "search button" failed.

Version 1.14.5.900

* New: Media with a "Keep tag" can not be deleted

Version 1.12.5.838

* Changed: Buy Me a Coffee link lower in the menu, plus a bitcoin option added
* Changed: Logging format changed
* Changed: Seriespath has (year) added to the path. Methods from API copied to main.
* Fixed: Series Calender info formatted better. Title had changed in v3 API Sonarr

version 1.12.4.780

* Bugfix: Unknown comand was not handled if signup was closed
* Changed: Usertag for new user is automaticly added when adding their first serie or movie

version 1.12.4.755

* Bugfix: Number of items in the queue for /sts is now correctly displayed.
* New: Buy me a coffee option /coffee add to the commands.
* New: /rss triggers the RSS events on Sonarr and Radarr.
* New: A search button is added to mediainfo (/lm) for movies that have not been downloaded yet.
