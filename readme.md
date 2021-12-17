
# Pixlovarr

2021-12-07 17:11:30

## What is it?

Pixlovarr is a compagnon written in Python for Radarr and Sonarr in the form of a Telegram bot.
/help will give you all the options to control the bot for Radarr and Sonarr.
The bot will guide you with an inline keyboard, this is for User commands and Admin commands.

Radarr Library Purge is a compagnon written in Python for Radarr to automaticly remove and delete movies which are added by lists. All movies which are not tagged are not evaluated.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Y8Y078U1V)

[![Bitcoin](https://marc0janssen.github.io/bitcoin_logo.png)](https://marc0janssen.github.io/bitcoin.html)

## Changelog

Version x

* New: /smm search missing movies
* New: Keep button for admins beneath the movieinfo

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

## Tags

You can list the custom tags of the Pixlovarr users by the command /lt as an admin.
These tags can be added to Sonarr or Radarr. If the tags are added to Sonarr or Radarr, anytime
a user adds a serie or movie, their tag is added to the downloaded media in Sonarr of Radarr.

You can later use the tagged media to your liking.

## Bot Commands

        -- User commands --
        /start - Start this bot
        /help - Show this text
        /signup - Request access
        /userid - Show your userid
        /ls #<genre> <word> - List all series
        /lm #<genre> <word> - List all movies
        /ms #<genre> <word> - list my series
        /mm #<genre> <word> - list my movies
        /ns #<genre> <word> - list new series
        /nm #<genre> <word> - list new movies
        /qu - List all queued items
        /ts T<#> - Show Top series
        /ps T<#> - Show Top popular series
        /tm T<#> - Show Top movies
        /pm T<#> - Show Top popular movies
        /ti T<#> - Show Top Indian movies
        /wm T<#> - Show Top worst movies
        /rs - Show recently reviewed series
        /rm - Show recently reviewed movies       
        /fq - Show announced items in catalog
        /ms - list your series
        /mm - list your movies
        /sts - Service status info
        /rss - trigger RSS fetching
        /smm - Trigger missing media search
        /ds T<#> <keyword> - Download serie
        /dm T<#> <keyword> - Download movie

        /coffee - Buy me a coffee

        -- Admin commands --
        /new - Show all new signups
        /am - Show all allowed members
        /bm - Show all blocked members
        /ch - Show command history
        /lt - list tags
        /open - open signup
        /close - close signup 

## Examples

        List all series in the catalog
        /ls

        List all series with title "Harry"
        /ls Harry

        List all series with genre "action" 
        /ls #action

        List all series with genre "action" and title "Harry"
        /ls #action Harry

        List all movies in the catalog
        /lm

        List all movies with title "Lord"
        /lm Lord

        List all movies with genre "Fantasy" 
        /lm #Fantasy

        List all movies with genre "Fantasy" and title "Lord"
        /lm #fantasy Lord

        Show the series calendar
        /sc

        Show the series calendar for "Grey"
        /sc grey

        Show the movies calendar
        /mc

        Show the movies calendar for "Dune"
        /mc dune

        Show top movies from IMDb
        /tm

        Show top 25 movies from IMDb
        /tm t25

        Find movies with "Jake" for download
        /dm jake

        Find top25 movies with "jake" for download
        /dm t25 jake

## Docker

The build.sh script will build you your own Pixlovarr docker image. But Pixlovarr is also available on Docker Hub.

        docker build -t marc0janssen/pixlovarr:latest -f ./Dockerfile .

The script start_pixlovarr.sh in ./scripts will pull and run the Pixlovarr image for you.

        docker run -d \
                --name=pixlovarr \
                --restart=always \
                -v /path/to/config/:/config \
                -v /path/to/movies/:/movies \
                marc0janssen/pixlovarr:latest

## Config Pixlovarr

In the directory /config the python script expects a config file called 'pixlovarr.ini' with the following content:

        [COMMON]
        BOT_TOKEN = BOTTOKEN
        ADMIN_USER_ID = ID_NUMBER
        PERMANENT_DELETE_MEDIA = OFF
        USERS_CAN_ONLY_DELETE_OWN_MEDIA = ON
        SIGN_UP_IS_OPEN = ON
        ONLY_SHOW_PATH_LARGEST_FREE_SPACE = NO
        EXCLUDE_ADMIN_FROM_HISTORY = OFF

        [IMDB]
        DEFAULT_LIMIT_RANKING = 5

        [SONARR]
        ENABLED = ON
        URL = http://192.168.1.1:8989
        TOKEN = SONARR_API_TOKEN
        SEASON_FOLDER = ON
        CALENDAR_PERIOD_DAYS_SERIES = 30
        AUTO_ADD_EXCLUSION = tag1,tag2
        PERIOD_DAYS_ADDED_NEW_DOWLOAD = 5
        TAGS_KEEP_MOVIES_ANYWAY = tag3,tag4
        TAGS_TO_EXTEND_PERIOD_BEFORE_REMOVAL = tag5,tag6

        [RADARR]
        ENABLED = OFF
        URL = http://192.168.1.1:7878
        TOKEN = RADARR_API_TOKEN
        CALENDAR_PERIOD_DAYS_MOVIES = 180
        AUTO_ADD_EXCLUSION = tag7,tag8
        PERIOD_DAYS_ADDED_NEW_DOWLOAD = 5
        TAGS_KEEP_MOVIES_ANYWAY = tag9,tag10
        TAGS_TO_EXTEND_PERIOD_BEFORE_REMOVAL = tag11,ta12

        [PRUNE]
        ENABLED = OFF
        DRY_RUN = ON
        TAGS_TO_MONITOR_FOR_REMOVAL_MOVIES = tag1,tag2,tag3
        REMOVE_MOVIES_AFTER_DAYS = 30
        WARN_DAYS_INFRONT = 1
        SHOW_KEPT_MESSAGE = ON
        EXTEND_PERIOD_BY_DAYS = 30

        [PUSHOVER]
        ENABLED = OFF
        USER_KEY = xxxxxxxxxxxxxxx
        TOKEN_API = xxxxxxxxxxxxxxx
        SOUND = pushover

Please set these to your liking. If the file pixlovarr.ini is not found, it the script will create a sample ini-file in the /config directory and exit.

## links

[Pixlovarr Github](https://github.com/marc0janssen/pixlovarr) \
[Pixlovarr Docker hub](https://hub.docker.com/r/marc0janssen/pixlovarr)
