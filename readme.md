# Pixlovarr

## What is it?

Pixlovarr is a compagnon written in Python for Radarr and Sonarr in the form of a Telegram bot.

/help will give you all the options to control the bot and Radarr and Sonarr.

The bot will guide you with an inline keyboard, this is for User commands and Admin commands.

## Bot Commands

        -- Commands --
        /start - Start this bot
        /help - Show this text
        /signup - Request access
        /userid - Request your userid
        /series - Get all TV shows
        /movies - Get all movies
        /ds <keyword> - Download serie
        /dm <keyword> - Download movie

        -- Admin commands --
        /new - Show all new signups
        /allowed - Show all allowed members
        /denied - Show all denied members

## Docker

The build.sh script will build you your own Pixlovarr docker image. But Pixlovarr is also available on Docker Hub.

The script start_pixlovarr.sh in ./scripts will pull and run the Pixlovarr image for you.

        docker run -d \
            --name=pixlovarr \
            --restart=always \
            -v /docker/pixlovarr/config:/config \
            marc0janssen/pixlovarr

## Config

In the directory /config the python script expects a config file called 'pixlovarr.ini' with the following content:

            [COMMON]
            BOT_TOKEN = BOTTOKEN
            ADMIN_USER_ID = ID_NUMBER

            [SONARR]
            URL = http://192.168.1.1:8989
            TOKEN = SONARR_API_TOKEN

            [RADARR]
            [URL] = http://192.168.1.1:7878
            TOKEN = RADARR_API_TOKEN

Please set these to your liking. If the file pixlovarr.ini is not found, it the script will create a sample ini-file in the /config directory and exit.

## links

[Pixlovarr Github](https://github.com/marc0janssen/pixlovarr) \
[Pixlovarr Docker hub](https://hub.docker.com/r/marc0janssen/pixlovarr)

## Acknowledge

The project was coded anf setup by myself. But I have to give credit where credit is due. The API with Sonarr and Radarr was coded by Vivien Chene in a project called [pycliarr](https://github.com/vche/pycliarr).  
2021-05-02 10:35:20
