
# Pixlovarr

2021-12-31 16:43:17

## What is it?

Pixlovarr is a compagnon written in Python for Radarr and Sonarr in the form of a Telegram bot.
/help will give you all the options to control the bot for Radarr and Sonarr.
The bot will guide you with an inline keyboard, this is for User commands and Admin commands.

Radarr Library Purge is a compagnon written in Python for Radarr to automaticly remove and delete movies which are added by lists. All movies which are not tagged are not evaluated.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Y8Y078U1V) [![Bitcoin](https://marc0janssen.github.io/bitcoin_logo.png)](https://marc0janssen.github.io/bitcoin.html)

## Versions

pixlovarr: 1.19.0.2868

Stable

```shell
docker pull marc0janssen/pixlovarr:stable
```

```shell
docker pull marc0janssen/pixlovarr:1.19.0.2868
```

Latest (experimental)

```shell
docker pull marc0janssen/pixlovarr:latest
```

## Changelog

See changelog at [Github](https://github.com/marc0janssen/pixlovarr/blob/main/changelog.md)

## Tags

You can list the custom tags of the Pixlovarr users by the command /lt as an admin.
These tags can be added to Sonarr or Radarr. If the tags are added to Sonarr or Radarr, anytime
a user adds a serie or movie, their tag is added to the downloaded media in Sonarr of Radarr.

You can later use the tagged media to your liking.

## Bot Commands

```shell
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
        /sc - Show series calendar
        /mc - Show movies calendar
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
```

## Examples

```shell

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
```

## Docker

The build.sh script will build you your own Pixlovarr docker image. But Pixlovarr is also available on Docker Hub.

```shell
        docker build -t pixlovarr -f ./Dockerfile .
```

The script start_pixlovarr.sh in ./scripts will pull and run the Pixlovarr image for you.

```shell
        docker run -d \
                --name=pixlovarr \
                --restart=always \
                -v /path/to/config/:/config \
                -v /path/to/movies/:/movies \
                -v /path/to/movies2/:/movies2 \
                -v /path/to/movies3/:/movies3 \
                -v /path/to/series/:/series \
                -v /path/to/series2/:/series2 \
                -v /path/to/series3/:/series3 \
                -e PRUNE_CRON="0 4,16 * * *" \
                pixlovarr
```

## Config Pixlovarr

In the directory /config the python script expects a config file called 'pixlovarr.ini' with the following content:

```INI
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
        AUTO_ADD_EXCLUSION = tag1,tag2,pixlovarr_tagged
        PERIOD_DAYS_ADDED_NEW_DOWLOAD = 5
        TAGS_KEEP_MOVIES_ANYWAY = tag3,tag4
        TAGS_TO_EXTEND_PERIOD_BEFORE_REMOVAL = tag5,tag6

        [RADARR]
        ENABLED = OFF
        URL = http://192.168.1.1:7878
        TOKEN = RADARR_API_TOKEN
        CALENDAR_PERIOD_DAYS_MOVIES = 180
        AUTO_ADD_EXCLUSION = tag7,tag8,pixlovarr_tagged
        PERIOD_DAYS_ADDED_NEW_DOWLOAD = 5
        TAGS_KEEP_MOVIES_ANYWAY = tag9,tag10
        TAGS_TO_EXTEND_PERIOD_BEFORE_REMOVAL = tag11,ta12

        [PRUNE]
        ENABLED = OFF
        DRY_RUN = ON
        TAGS_TO_MONITOR_FOR_REMOVAL_MOVIES = tag1,tag2,tag3,pixlovarr_tagged
        REMOVE_MOVIES_AFTER_DAYS = 30
        WARN_DAYS_INFRONT = 1
        SHOW_KEPT_MESSAGE = ON
        EXTEND_PERIOD_BY_DAYS = 30
        VIDEO_EXTENSIONS_MONITORED = .mp4,.avi,.mkv,.m2ts,.wmv
        MAIL_ENABLED = OFF
        ONLY_MAIL_WHEN_REMOVED = OFF
        MAIL_PORT = 587
        MAIL_SERVER = mail.sever.tld
        MAIL_LOGIN = login@mail.tld
        MAIL_PASSWORD = sgdfjsgdjsdg
        MAIL_SENDER = sender@mail.tld
        MAIL_RECEIVER = receiver@mail.tld,receiver2@mail.tld
        TAG_UNTAGGED_MEDIA = OFF
        UNTAGGED_MEDIA_TAG = pixlovarr_tagged

        [PUSHOVER]
        ENABLED = OFF
        USER_KEY = xxxxxxxxxxxxxxx
        TOKEN_API = xxxxxxxxxxxxxxx
        SOUND = pushover
```

Please set these to your liking. If the file pixlovarr.ini is not found, it the script will create a sample ini-file in the /config directory and exit.

## links

[Pixlovarr Github](https://github.com/marc0janssen/pixlovarr) \
[Pixlovarr Docker hub](https://hub.docker.com/r/marc0janssen/pixlovarr)
