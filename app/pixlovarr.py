# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 22021-05-13 16:09:31

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)
from urllib.parse import urlparse
import logging
import json
import configparser
import shutil
import sys
import re
import imdb
import random
from time import time
from datetime import datetime, date, timedelta
from pycliarr.api import (
    RadarrCli,
    RadarrMovieItem
)
from pycliarr.api import (
    SonarrCli,
    SonarrSerieItem,
    exceptions
)
# from pycliarr.api.exceptions import CliServerError


class Pixlovarr():

    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)

        self.urlNoImage = (
            "https://postimg.cc/3dfySHP9"
        )

        self.config_file = "./config/pixlovarr.ini"

        self.cmdHistory = []
        self.maxCmdHistory = 50
        self.rankingLimitMin = 3
        self.rankingLimitMax = 100
        self.listLength = 75
        self.youTubeURL = "https://www.youtube.com/watch?v="

        self.imdb = imdb.IMDb()

        try:
            with open(self.config_file, "r") as f:
                f.close()
            try:
                self.config = configparser.ConfigParser()
                self.config.read(self.config_file)
                self.bot_token = self.config['COMMON']['BOT_TOKEN']
                self.admin_user_id = self.config['COMMON']['ADMIN_USER_ID']

                self.default_limit_ranking = self.clamp(
                    int(self.config['IMDB']['DEFAULT_LIMIT_RANKING']),
                    self.rankingLimitMin,
                    self.rankingLimitMax
                )

                self.sonarr_enabled = True if (
                    self.config['SONARR']['ENABLED'] == "ON") else False
                self.sonarr_season_folder = True if (
                    self.config['SONARR']['SEASON_FOLDER'] == "ON") else False
                self.sonarr_url = self.config['SONARR']['URL']
                self.sonarr_token = self.config['SONARR']['TOKEN']
                self.calendar_period_days_series = \
                    self.config['SONARR']['CALENDAR_PERIOD_DAYS_SERIES']

                self.radarr_enabled = True if (
                    self.config['RADARR']['ENABLED'] == "ON") else False
                self.radarr_url = self.config['RADARR']['URL']
                self.radarr_token = self.config['RADARR']['TOKEN']
                self.calendar_period_days_movies = \
                    self.config['RADARR']['CALENDAR_PERIOD_DAYS_MOVIES']

                if self.sonarr_enabled:
                    self.sonarr_node = SonarrCli(
                        self.sonarr_url, self.sonarr_token
                    )

                if self.radarr_enabled:
                    self.radarr_node = RadarrCli(
                        self.radarr_url, self.radarr_token
                    )

                if not self.sonarr_enabled and not self.radarr_enabled:
                    logging.error(
                        "Sonarr nor Radarr are enabled. Exiting."
                    )

                    sys.exit()

                self.pixlovarr_signups_file = (
                    "./config/pixlovarr_signups.json")
                self.pixlovarr_members_file = (
                    "./config/pixlovarr_members.json")
                self.pixlovarr_rejected_file = (
                    "./config/pixlovarr_rejected.json")

                self.signups = self.loaddata(self.pixlovarr_signups_file)
                self.members = self.loaddata(self.pixlovarr_members_file)
                self.rejected = self.loaddata(self.pixlovarr_rejected_file)

            except KeyError as e:
                logging.error(
                    f"Seems a key(s) {e} is missing from INI file. "
                    f"Please check for mistakes. Exiting."
                )

                sys.exit()

            except ValueError:
                logging.error(
                    "Seems a value(s) is invalid in INI file. "
                    "Please check for mistakes. Exiting."
                )

                sys.exit()

        except IOError or FileNotFoundError:
            logging.error(
                f"Can't open file {self.config_file}, "
                f"creating example INI file."
            )

            shutil.copyfile('./app/pixlovarr.ini.example',
                            './config/pixlovarr.ini.example')
            sys.exit()

    def getProfileInfo(self, profileID, mediaOfType):

        if mediaOfType == "serie":
            profiles = self.sonarr_node.get_quality_profiles()

        else:
            profiles = self.radarr_node.get_quality_profiles()

        if profiles:

            for count, p in enumerate(profiles):

                if p['id'] == profileID:
                    return p['name']

        return ""

    def getTopAmount(self, update, context, ranking):
        if re.match("^[Tt]\\d+$", ranking):
            return self.clamp(
                int(ranking[1:]),
                self.rankingLimitMin,
                self.rankingLimitMax
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"Defaulting to Top {self.default_limit_ranking}"
                )
            )
            return self.default_limit_ranking

    def clamp(self, n, minn, maxn):
        return max(min(maxn, n), minn)

    def getGenres(self, listOfGenres):
        genresText = ""
        try:
            for genre in listOfGenres:
                genresText += f"{genre}, "

            genresText = genresText[:len(genresText)-2]
        except KeyError:
            genresText = "-"

        return genresText

    def is_http_or_https(self, url):
        return urlparse(url).scheme in {'http', 'https'}

    def countItemsinQueue(
        self, update, context,
            numOfItems, queue, typeOfMedia):

        for queueitem in queue:

            numOfItems += 1

            try:
                if typeOfMedia == "serie":
                    dt = (self.datetime_from_utc_to_local(
                        datetime.strptime(queueitem[
                            'estimatedCompletionTime'],
                            "%Y-%m-%dT%H:%M:%S.%fZ")))
                else:
                    dt = (self.datetime_from_utc_to_local(
                        datetime.strptime(queueitem[
                            'estimatedCompletionTime'],
                            "%Y-%m-%dT%H:%M:%SZ")))

                pt = datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

                tl = queueitem['timeleft']

            except KeyError:
                pt = "-"
                tl = "-"

            if typeOfMedia == "serie":
                text = (
                    f"{queueitem['series']['title']} "
                    f"S{queueitem['episode']['seasonNumber']}"
                    f"E{queueitem['episode']['episodeNumber']} - "
                    f"'{queueitem['episode']['title']}'\n"
                    f"Status: {queueitem['status']}\n"
                    f"Protocol: {queueitem['protocol']}\n"
                    f"Timeleft: {tl}\n"
                    f"ETA: {pt}"
                )

#                title = f"{queueitem['episode']['title']}"
            else:
                text = (
                    f"{queueitem['movie']['title']}"
                    f"({queueitem['movie']['year']})\n"
                    f"Status: {queueitem['status']}\n"
                    f"Protocol: {queueitem['protocol']}\n"
                    f"Timeleft: {tl}\n"
                    f"ETA: {pt}"
                )

        #    txtQueue += text


#                title = (
#                    f"{queueitem['movie']['title']}"
#                    f"({queueitem['movie']['year']})"
#                )

#            callbackdata = (
#                f"deletequeueitem:{typeOfMedia}:"
#                f"{queueitem['id']}:{title}"
#            )

#            keyboard = [[InlineKeyboardButton(
#                f"Remove {title}",
#                callback_data=callbackdata)]]

#            reply_markup = InlineKeyboardMarkup(keyboard)

#            update.message.reply_text(
#                f"{text}",
#                reply_markup=reply_markup
#            )

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text
            )

        return numOfItems

    def sortOnTitle(self, e):
        return e.title

    def sortOnNameDict(self, e):
        return e['name']

    def addItemToHistory(self, cmd, uname, uid):
        historyItem = {}

        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

        historyItem["timestamp"] = dt_string
        historyItem["cmd"] = cmd
        historyItem["uname"] = uname
        historyItem["uid"] = uid

        self.cmdHistory.append(historyItem)

        if len(self.cmdHistory) > self.maxCmdHistory:
            self.cmdHistory.pop(0)

    def isAdmin(self, update, context, verbose):
        if str(update.effective_user.id) == self.admin_user_id:
            return True
        else:
            if verbose:

                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"{update.effective_user.first_name}, "
                        f"you are not authorized for this command."
                    )
                )

                logging.warning(
                    f"{update.effective_user.first_name} - "
                    f"{update.effective_user.id} "
                    f"entered an unauthorized command."
                )

            return False

    def isRejected(self, update):
        return str(update.effective_user.id) in self.rejected

    def isGranted(self, update):
        return str(update.effective_user.id) in self.members

    def datetime_from_utc_to_local(self, utc_datetime):
        now_timestamp = time()
        offset = datetime.fromtimestamp(
            now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
        return utc_datetime + offset

    def loaddata(self, file):
        try:
            with open(file, "r") as f:
                data = f.read()
                f.close()
            try:
                return json.loads(data)

            except json.JSONDecodeError:
                logging.warning(
                    f"Loaded json {file} seems corrupt, "
                    f"creating empty dictionary."
                )
                return {}

        except IOError:
            logging.info(f"Can't open file {file}, creating empty dictionary.")
            return {}

    def saveconfig(self, file, dataDictonary):
        try:
            with open(file, 'w') as f:
                f.write(json.dumps(dataDictonary))
                f.close

        except IOError:
            logging.warning(f"Can't write file {file}.")

    def showMediaInfo(self, update, context, typeOfMedia, media):

        txtMediaInfo = ""

        if media.images:
            image = f"{media.images[0]['url']}" if self.is_http_or_https(
                media.images[0]['url']) else media.images[0]['remoteUrl']
        else:
            image = self.urlNoImage

        caption = f"{media.title}({media.year})"
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image, caption=caption
        )

        try:
            textoverview = f"{media.overview[:4092]}\n\n" if \
                media.overview != "" else "No description available.\n\n"
        except AttributeError:
            textoverview = "No description available.\n\n"

        txtMediaInfo += textoverview

        try:
            if media.episodeCount > 0:
                textEpisode = f"Episode count: {media.episodeCount}\n\n"
                txtMediaInfo += textEpisode
        except AttributeError:
            pass

        try:
            genres = self.getGenres(media.genres) \
                if self.getGenres(media.genres) != '' else '-'

            txtGenres = f"Genres: {genres}\n\n"
            txtMediaInfo += txtGenres

        except AttributeError:
            pass

        try:
            if media.ratings['votes'] > 0:
                txtRatings = (
                    f"Rating: {media.ratings['value']} "
                    f"votes: {media.ratings['votes']}\n\n"
                )
                txtMediaInfo += txtRatings

        except AttributeError:
            pass

        try:
            if media.runtime > 0:
                txtRuntime = f"Runtime: {media.runtime} minutes\n\n"
                txtMediaInfo += txtRuntime

        except AttributeError:
            pass

        try:
            txtStatus = f"Status: {media.status}\n\n"
            txtMediaInfo += txtStatus

        except AttributeError:
            pass

        try:
            txtNetwork = (
                f"Network: {media.network if media.network != '' else '-'}\n\n"
            )
            txtMediaInfo += txtNetwork

        except AttributeError:
            pass

        try:
            txtStudio = (
                f"Studio: {media.studio if media.studio != '' else '-'}\n\n"
            )
            txtMediaInfo += txtStudio

        except AttributeError:
            pass

        qualityText = self.getProfileInfo(media.qualityProfileId, typeOfMedia)
        if qualityText != "":

            txtQuality = (
                f"Quality: {qualityText}\n\n"
            )
            txtMediaInfo += txtQuality

        if txtMediaInfo != "":
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=txtMediaInfo
            )

        try:
            if media.youTubeTrailerId:
                youTubeURL = f"{self.youTubeURL}{media.youTubeTrailerId}"
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{youTubeURL}"
                )
        except AttributeError:
            pass

    def showCalenderMediaInfo(self, update, context, media):
        try:
            title = (
                f"{media['series']['title']}({media['series']['year']}) - "
                f"S{media['seriesId']}\n"
                f"Episode: S{media['seasonNumber']}E{media['episodeNumber']}"
                f" - {media['title']}"
            )
        except KeyError:
            try:
                title = f"{media['title']}({media['year']}) - M{media['id']}"
            except KeyError:
                title = "-"

        try:
            dateCinema = datetime.strftime(
                datetime.strptime(
                    media['inCinemas'], '%Y-%m-%dT%H:%M:%SZ'), '%Y-%m-%d')
            dateText = "In cinemas"
        except KeyError:
            try:
                dateCinema = media['airDate']
                dateText = "Airdate"
            except KeyError:
                dateCinema = "-"
                dateText = "Date"

        return(
            f"{title}\n"
            f"{dateText}: {dateCinema}\n\n"
        )

    def listMedia(self, update, context, typeOfMedia, media):

        mediaMarker = "S" if typeOfMedia == "serie" else "M"

        if type(media) is SonarrSerieItem or \
                type(media) is RadarrMovieItem:

            text = (
                f"{media.title} ({str(media.year)}) "
                f"- {mediaMarker}{media.id}\n"
            )

            context.bot.send_message(
                chat_id=update.effective_chat.id, text=text)
        else:
            media.sort(key=self.sortOnTitle)

            allMedia = ""
            itemInList = False
            genre = ""

            if len(context.args) > 0:
                if re.match("^#[A-Za-z]+$", context.args[0]):
                    genre = context.args[0][1:]
                    context.args.pop(0)

            for count, m in enumerate(media):

                if re.search(
                    ' '.join(context.args).lower(), m.title.lower()) \
                        or not context.args:

                    if genre.lower() in (genre.lower() for genre in m.genres) \
                            or not genre:

                        allMedia += (
                            f"{m.title} ({str(m.year)}) - "
                            f"{mediaMarker}{m.id}\n")

                        if (count % self.listLength == 0 and count != 0):
                            context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=allMedia
                            )

                            allMedia = ""

                        itemInList = True

            if allMedia != "":
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=allMedia)

            if not itemInList:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"There are no results found, "
                        f"{update.effective_user.first_name}."
                    )
                )

    def listCalendar(self, update, context, media):
        if type(media) is SonarrSerieItem or \
                type(media) is RadarrMovieItem:
            text = self.showCalenderMediaInfo(update, context, media)

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text
            )

        else:

            allMedia = ""
            itemInList = False
            for count, m in enumerate(media):

                try:
                    searchString = f"{m['series']['title']} {m['title']}"
                except KeyError:
                    searchString = m['title']

                if re.search(
                    ' '.join(context.args).lower(), searchString.lower()) \
                        or not context.args:

                    allMedia += (
                        self.showCalenderMediaInfo(update, context, m))

                    if (count % self.listLength == 0 and count != 0):
                        context.bot.send_message(
                            chat_id=update.effective_chat.id, text=allMedia)

                        allMedia = ""

                    itemInList = True

            if allMedia != "":
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=allMedia)

            if not itemInList:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"There are no results found, "
                        f"{update.effective_user.first_name}."
                    )
                )

    def logCommand(self, update):
        logging.info(
            f"{update.effective_user.first_name} - "
            f"{update.effective_user.id} "
            f"issued {update.effective_message.text}."
        )

        self.addItemToHistory(
            f"{update.effective_message.text}",
            update.effective_user.first_name,
            update.effective_user.id
        )

# Default Commands

    def start(self, update, context):
        if not self.isRejected(update):
            self.logCommand(update)

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"Welcome {update.effective_user.first_name} "
                    f"to Pixlovarr, I'm your assistent for "
                    f"downloading series and movies. Please use /help "
                    f"for more information. But first request access "
                    f"with /signup."
                )
            )

    def signup(self, update, context):
        if not self.isRejected(update):

            self.logCommand(update)

            if not self.isGranted(update):
                if not str(update.effective_user.id) in self.signups:

                    self.person = {}
                    self.person['fname'] = update.effective_user.first_name
                    self.person['lname'] = update.effective_user.last_name
                    self.person['uname'] = update.effective_user.username
                    self.person['id'] = str(update.effective_user.id)

                    self.signups[self.person['id']] = self.person

                    self.saveconfig(self.pixlovarr_signups_file, self.signups)

                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=(
                            f"Thank you {update.effective_user.first_name}, "
                            f"for signing up. The admin has been notified. "
                            f"Please be patient and you will be added to "
                            f"the memberlist soon."
                        )
                    )

                    context.bot.send_message(
                        chat_id=self.admin_user_id,
                        text=(
                            f"Hi admin, {self.person['fname']} wants access.\n"
                            f"Use /new to list all new members.\n"
                        )
                    )

                else:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=(
                            f"Please be patient "
                            f"{update.effective_user.first_name}, "
                            f"we get you hooked up as soon as possible."
                        )
                    )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"No need to sign up twice, "
                        f"{update.effective_user.first_name}"
                    )
                )

    def help(self, update, context):
        if not self.isRejected(update):
            self.logCommand(update)

            helpText = (
                "-- User commands --\n"
                "/start - Start this bot\n"
                "/help - Show this text\n"
                "/signup - Request access\n"
                "/userid - Show your userid\n"
            )

            if self.isGranted(update):
                helpText = helpText + (
                    "/ls #<genre> <word> - List all series\n"
                    "/lm #<genre> <word> - List all movies\n"
                    "/sc <word> - Series calendar\n"
                    "/mc <word> - Movies calendar\n"
                    "/qu - List all queued items\n"
                    "/del <id> - Delete media from catalog\n"
                    "/di <id> - Display media info\n"
                    "/ts T<#> - Show Top series\n"
                    "/ps T<#> - Show Top popular series\n"
                    "/tm T<#> - Show Top movies\n"
                    "/pm T<#> - Show Top popular movies\n"
                    "/ti T<#> - Show Top Indian movies\n"
                    "/wm T<#> - Show Top worst movies\n"
                    "/fq - Show queued announced items\n"
                    "/ds T<#> <keyword> - Download series\n"
                    "/dm T<#> <keyword> - Download movie\n"
                )

            if self.isAdmin(update, context, False):
                helpText = helpText + (
                    "\n-- Admin commands --\n"
                    "/new - Show all new signups\n"
                    "/allowed - Show all allowed members\n"
                    "/denied - Show all denied members\n"
                    "/history - Show command history\n"
                    "/del <id> - Delete media from disk\n"
                )

            context.bot.send_message(
                chat_id=update.effective_chat.id, text=helpText)

    def userid(self, update, context):
        if not self.isRejected(update):
            self.logCommand(update)

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"Hi {update.effective_user.first_name}, "
                    f"your userid is {update.effective_user.id}."
                )
            )

# Member Commands
    def geCalendar(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.radarr_enabled:

            self.logCommand(update)

            command = update.effective_message.text.split(" ")

            startDate = date.today()

            if command[0] == "/sc":
                endDate = startDate + timedelta(
                    days=int(self.calendar_period_days_series))
                media = self.sonarr_node.get_calendar(
                    start_date=startDate, end_date=endDate)
                typeOfMedia = "serie"

            elif command[0] == "/mc":
                endDate = startDate + timedelta(
                    days=int(self.calendar_period_days_movies))
                media = self.radarr_node.get_calendar(
                    start_date=startDate, end_date=endDate)
                typeOfMedia = "movie"

            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Something went wrong...")

                return

            endtext = f"There are no {typeOfMedia}s in the calendar."

            if media:
                self.listCalendar(update, context, media)
                endtext = (
                    f"There are {len(media)} {typeOfMedia}s "
                    f"in the calendar.")

            context.bot.send_message(
                chat_id=update.effective_chat.id, text=endtext)

    def futureQueue(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                (self.sonarr_enabled or self.radarr_enabled):

            self.logCommand(update)

            series = self.sonarr_node.get_serie()
            series.sort(key=self.sortOnTitle)

            movies = self.radarr_node.get_movie()
            movies.sort(key=self.sortOnTitle)

            endtext = "There is no media in the announced queue."

            fqCount = 0
            allSeries = "Series\n"
            if type(series) is SonarrSerieItem:
                if series.status == "upcoming":
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"{series.title} ({str(series.year)}) - "
                        f"S{series.id}\n"
                    )
                    fqCount += 1
            else:
                for s in series:
                    if s.status == "upcoming":
                        fqCount += 1
                        allSeries += f"{s.title} ({str(s.year)}) - S{s.id}\n"

                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=allSeries)

                endtext = f"There are {fqCount} series in the announced queue."

            allMovies = "Movies\n"
            if type(movies) is RadarrMovieItem:
                if movies.status == "announced":
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"{movies.title} ({str(movies.year)}) - "
                        f"M{movies.id}\n"
                    )
                    fqCount += 1
            else:
                for m in movies:
                    if m.status == "announced":
                        fqCount += 1
                        allMovies += f"{m.title} ({str(m.year)}) - M{m.id}\n"

                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=allMovies)

                endtext = f"There are {fqCount} items in the announced queue."

            context.bot.send_message(
                chat_id=update.effective_chat.id, text=endtext)

    def showRankings(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update):

            self.logCommand(update)

            command = update.effective_message.text.split(" ")

            topAmount = self.getTopAmount(
                update, context, ' '.join(context.args))

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please be patient...")

            if command[0] == "/ts":
                media = self.imdb.get_top250_tv()
                typeOfMedia = "serie"
                adjective = ""

            elif command[0] == "/ps":
                media = self.imdb.get_popular100_tv()
                typeOfMedia = "serie"
                adjective = "popular "

            elif command[0] == "/tm":
                media = self.imdb.get_top250_movies()
                typeOfMedia = "movie"
                adjective = ""

            elif command[0] == "/pm":
                media = self.imdb.get_popular100_movies()
                typeOfMedia = "movie"
                adjective = "popular "

            elif command[0] == "/ti":
                media = self.imdb.get_top250_indian_movies()
                typeOfMedia = "movie"
                adjective = "Indian "

            elif command[0] == "/wm":
                media = self.imdb.get_bottom100_movies()
                typeOfMedia = "movie"
                adjective = "worst "

            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Something went wrong...")

                return

            keyboard = []

            for count, m in enumerate(media[:topAmount]):
                if count % 12 == 0 and count != 0:
                    phrass = [
                        "rm -rf /homes/* ... just kidding...",
                        "It’s hardware that makes a machine fast. It’s "
                        "software that makes a fast machine slow...",
                        "We will deliver before the Holidays...",
                        "Driving up the IMDb headquaters yourself and asking "
                        "stuff in person seems faster...",
                        "My software never has bugs. It just develops "
                        "random features..."
                    ]

                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=random.choice(phrass))

                if typeOfMedia == "serie":
                    foundMedia = self.sonarr_node.lookup_serie(term=m['title'])
                    if foundMedia is None:
                        continue

                    if type(foundMedia) != SonarrSerieItem:
                        foundMedia = foundMedia[0]
                    foundMediaID = foundMedia.tvdbId
                else:
                    foundMedia = self.radarr_node.lookup_movie(term=m['title'])
                    if foundMedia is None:
                        continue

                    if type(foundMedia) != RadarrMovieItem:
                        foundMedia = foundMedia[0]
                    foundMediaID = foundMedia.imdbId

                callbackdata = f"showdlsummary:{typeOfMedia}:{foundMediaID}"

                keyboard.append([InlineKeyboardButton(
                    f"{foundMedia.title}({foundMedia.year})",
                    callback_data=callbackdata)]
                )

            reply_markup = InlineKeyboardMarkup(keyboard)

            update.message.reply_text(
                f"IMDb top {topAmount} {adjective}{typeOfMedia}s "
                f"at the moment:",
                reply_markup=reply_markup
            )

    def showQueue(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update):

            self.logCommand(update)

            numOfItems = 0

            if self.sonarr_enabled:
                queuesonarr = self.sonarr_node.get_queue()

                if queuesonarr:
                    numOfItems = self.countItemsinQueue(
                        update, context, numOfItems, queuesonarr, "serie")

            if self.radarr_enabled:
                queueradarr = self.radarr_node.get_queue()

                if queueradarr:
                    numOfItems = self.countItemsinQueue(
                        update, context, numOfItems, queueradarr, "movie")

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"There are {numOfItems} items in the queue."
            )

    def downloadSeries(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.sonarr_enabled:

            self.logCommand(update)

            self.findMedia(update, context, "serie")

    def list(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.radarr_enabled:

            self.logCommand(update)

            command = update.effective_message.text.split(" ")

            if command[0] == "/ls":
                media = self.sonarr_node.get_serie()
                typeOfMedia = "serie"
            elif command[0] == "/lm":
                media = self.radarr_node.get_movie()
                typeOfMedia = "movie"
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Something went wrong...")

                return

            endtext = f"There are no {typeOfMedia}s in the catalog."

            if media:
                self.listMedia(update, context, typeOfMedia, media)
                endtext = (
                    f"There are {len(media)} {typeOfMedia}s in the catalog.")

            context.bot.send_message(
                chat_id=update.effective_chat.id, text=endtext)

    def downloadMovies(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.radarr_enabled:

            self.logCommand(update)

            self.findMedia(update, context, "movie")

    def displayInfo(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update):

            self.logCommand(update)

            command = update.effective_message.text.split(" ")

            if context.args:

                if re.match("^[SsMm]\\d+$", context.args[0]):
                    typeOfMedia = "serie" if(
                        context.args[0][:1] in ["s", "S"]) else "movie"
                    mediaID = context.args[0][1:]

                    try:
                        if typeOfMedia == "serie":
                            media = self.sonarr_node.get_serie(int(mediaID))
                        else:
                            media = self.radarr_node.get_movie(int(mediaID))

                        self.showMediaInfo(update, context, typeOfMedia, media)

                        if command[0] == "/del":
                            callbackdata = (
                                f"deletemedia:{typeOfMedia}:{mediaID}")
                            if self.isAdmin(update, context, False):
                                callbackdata += ":True"
                            else:
                                callbackdata += ":False"

                            keyboard = [[InlineKeyboardButton(
                                f"{media.title}({media.year})",
                                callback_data=callbackdata)]]

                            reply_markup = InlineKeyboardMarkup(keyboard)
                            update.message.reply_text(
                                "Do you want to delete this media:",
                                reply_markup=reply_markup
                            )

                    except exceptions.CliServerError as e:

                        errorResponse = json.loads(e.response)
                        if (errorResponse["message"] == "NotFound"):

                            context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=(
                                    "This ID was not found in the "
                                    "catalog.\nPlease check /ls"
                                    " or /lm for IDs."
                                )
                            )

                        else:
                            context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f"{errorResponse['message']}")

                else:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=(
                            "This ID was not recognized.\nPlease check "
                            "/ls or /lm for IDs."
                        )
                    )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "There was no ID given.\nPlease check "
                        "/ls or /lm for IDs."
                    )
                )

# Admin Commands

    def showCmdHistory(self, update, context):
        if self.isAdmin(update, context, True):

            self.logCommand(update)

            endtext = "No items in the command history."

            for historyItem in self.cmdHistory:

                text = (
                    f"{historyItem['timestamp']} - "
                    f"{historyItem['cmd']} - "
                    f"{historyItem['uname']} - "
                    f"{historyItem['uid']}"
                )

                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text
                )

                endtext = (
                    f"Found {len(self.cmdHistory)} items "
                    f"in command history."
                )

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=endtext
            )

    def new(self, update, context):
        if self.isAdmin(update, context, True):
            self.logCommand(update)

            if self.signups:

                keyboard = []

                for signup in self.signups:
                    person = self.signups[signup]
                    row = []
                    row.append(InlineKeyboardButton(
                        f"-√- {person['fname']}",
                        callback_data=f"grant:new:{person['id']}")
                    )
                    row.append(InlineKeyboardButton(
                        f"-X- {person['fname']}",
                        callback_data=f"reject:new:{person['id']}")
                    )

                    keyboard.append(row)

                reply_markup = InlineKeyboardMarkup(keyboard)

                update.message.reply_text(
                    'These are your new signups. Please Grant or Reject:',
                    reply_markup=reply_markup
                )

            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "No new signups in the queue."
                    )
                )

            self.logCommand(update)

    def allowed(self, update, context):
        if self.isAdmin(update, context, True):
            self.logCommand(update)

            if self.members:

                keyboard = []

                for member in self.members:
                    person = self.members[member]
                    keyboard.append([InlineKeyboardButton(
                        f"-X- {person['fname']}",
                        callback_data=f"reject:allowed:{person['id']}")]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                update.message.reply_text(
                    'These are your members. Please reject if needed:',
                    reply_markup=reply_markup
                )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "No members in the list."
                    )
                )

    def denied(self, update, context):
        if self.isAdmin(update, context, True):
            self.logCommand(update)

            if self.rejected:

                keyboard = []

                for member in self.rejected:
                    person = self.rejected[member]
                    keyboard.append([InlineKeyboardButton(
                        f"-√- {person['fname']}",
                        callback_data=f"grant:denied:{person['id']}")]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                update.message.reply_text(
                    'These members are denied. Please grant if needed:',
                    reply_markup=reply_markup
                )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "No members in the list."
                    )
                )

    def unknown(self, update, context):
        if not self.isRejected(update):

            self.logCommand(update)

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Sorry {update.effective_user.first_name}, "
                f"I didn't understand that command.")

# HandlerCallback Commands
    def deleteQueueItem(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:queueID, 3:mediaTitle

            print(data[2])

            if data[1] == "serie":
                res = self.sonarr_node.delete_queue(int(data[2]))
            else:
                res = self.radarr_node.delete_queue(int(data[2]))

            print(res)

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"The {data[1]} {data[3]} was removed from the queue.")

    def deleteMedia(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaID, 3:delete_files

            try:
                if data[1] == "serie":
                    self.sonarr_node.delete_serie(
                        serie_id=int(data[2]), delete_files=data[3])
                else:
                    self.radarr_node.delete_movie(
                        movie_id=int(data[2]), delete_files=data[3])

                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"The {data[1]} has been deleted.")

            except exceptions.CliServerError as e:
                errorResponse = json.loads(e.response)

                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=errorResponse["message"])

    def downloadMedia(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid
            # 3:qualityid, 4: Download which seasons?

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please be patient...")

            if data[1] == "serie":
                media = self.sonarr_node.lookup_serie(tvdb_id=data[2])

                try:
                    if data[4] == "First":
                        monitored_seasons = [1]

                    elif data[4] == "All":
                        monitored_seasons = [
                            i for i in range(1, media.seasonCount+1)]

                    elif data[4] == "New":
                        monitored_seasons = []

                    self.sonarr_node.add_serie(
                        tvdb_id=data[2], quality=int(data[3]),
                        monitored_seasons=monitored_seasons,
                        season_folder=self.sonarr_season_folder
                    )

                    self.notifyDownload(
                        update, context, data[1], media.title, media.year)

                except exceptions.CliServerError as e:
                    errorResponse = json.loads(e.response)

                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"{errorResponse[1]['errorMessage']}")
            else:
                media = self.radarr_node.lookup_movie(imdb_id=data[2])
                try:
                    self.radarr_node.add_movie(
                        imdb_id=data[2], quality=int(data[3])
                    )
                    self.notifyDownload(
                        update, context, data[1], media.title, media.year)

                except exceptions.CliServerError as e:
                    errorResponse = json.loads(e.response)

                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"{errorResponse[1]['errorMessage']}")

    def notifyDownload(self, update, context, typeOfMedia, title, year):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"The {typeOfMedia} '{title}({year})' "
            f"was added to the server, "
            f"{update.effective_user.first_name}. "
            f"Thank you and till next time.")

        logging.info(
            f"{update.effective_user.first_name} - "
            f"{update.effective_user.id} has added the "
            f"{typeOfMedia} '{title}({year})' "
            f"to the server.")

    def showDownloadSummary(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid

            if data[1] == "serie":
                profiles = self.sonarr_node.get_quality_profiles()
                callbackdata = f"selectdownload:{data[1]}:{data[2]}"
                media = self.sonarr_node.lookup_serie(tvdb_id=data[2])

            else:
                profiles = self.radarr_node.get_quality_profiles()
                callbackdata = f"selectdownload:{data[1]}:{data[2]}"
                media = self.radarr_node.lookup_movie(imdb_id=data[2])

            self.showMediaInfo(update, context, data[1], media)

            keyboard = []
            row = []
            num_columns = 2

            if profiles:

                profiles.sort(key=self.sortOnNameDict)

                for count, p in enumerate(profiles):
                    row.append(InlineKeyboardButton(
                        f"{p['name']}",
                        callback_data=f"{callbackdata}:{p['id']}")
                    )

                    if (count+1) % num_columns == 0 or \
                            count == len(profiles)-1:
                        keyboard.append(row)
                        row = []

                reply_markup = InlineKeyboardMarkup(keyboard)

            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"No profiles were found, Please set them up in"
                    f"Sonarr and Radarr, {update.effective_user.first_name}.")

                return

            reply_markup = InlineKeyboardMarkup(keyboard)

            query.message.reply_text(
                "Please select media quality:",
                reply_markup=reply_markup
            )

    def selectDownload(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):
            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid, 3: Quality

            if data[1] == "serie":
                callbackdata = f"downloadmedia:{data[1]}:{data[2]}:{data[3]}"
                keyboard = [
                    [InlineKeyboardButton(
                        "Download only season 1",
                        callback_data=f"{callbackdata}:First")],
                    [InlineKeyboardButton(
                        "Download all seasons",
                        callback_data=f"{callbackdata}:All")],
                    [InlineKeyboardButton(
                        "Download only new seasons",
                        callback_data=f"{callbackdata}:New")]
                ]
            else:
                media = self.radarr_node.lookup_movie(imdb_id=data[2])
                callbackdata = (
                    f"downloadmedia:{data[1]}:{data[2]}:{data[3]}:False")
                keyboard = [[InlineKeyboardButton(
                    f"Download {media.title}({media.year})",
                    callback_data=callbackdata)]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            query.message.reply_text(
                "Please confirm your download:",
                reply_markup=reply_markup
            )

    def findMedia(self, update, context, mediaType):

        if ' '.join(context.args):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Searching for {mediaType}s..."
            )

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} is searching for "
                f"a {mediaType} with keywords '{' '.join(context.args)}'"
            )

            args = ""
            if len(context.args) > 0:
                args = context.args[0]
                if re.match("^[Tt]\\d+$", args):
                    context.args.pop(0)

            topAmount = self.getTopAmount(update, context, args)

            searchQuery = ' '.join(context.args)

            if mediaType == "serie":
                media = self.sonarr_node.lookup_serie(term=searchQuery)
                mediaMarker = "S"
            else:
                media = self.radarr_node.lookup_movie(term=searchQuery)
                mediaMarker = "M"

            if media:
                keyboard = []

                if type(media) == SonarrSerieItem or \
                        type(media) == RadarrMovieItem:
                    temp = media
                    media = []
                    media.append(temp)

                maxResults = topAmount - 1

                presentMedia = ""

                for m in media:
                    if m.path:
                        presentMedia += (
                            f"{m.title}({m.year}) - "
                            f"{mediaMarker}{m.id}\n"
                        )

                        maxResults += 1

                        continue    # media is already in collection

                    if mediaType == "serie":
                        callbackdata = f"showdlsummary:{mediaType}:{m.tvdbId}"
                        if not m.tvdbId:

                            maxResults += 1

                            continue  # serie doesn't have ID
                    else:
                        callbackdata = f"showdlsummary:{mediaType}:{m.imdbId}"
                        if not m.imdbId:

                            maxResults += 1

                            continue  # movie doesn't have ID

                    keyboard.append([InlineKeyboardButton(
                        f"{m.title}({m.year})",
                        callback_data=callbackdata)]
                    )

                    if media.index(m) == maxResults:
                        break

#                if keyboard:
                if presentMedia != "":
                    presentMedia = (
                        f"We found these in your catalog"
                        f" already:\n{presentMedia}"
                    )
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=presentMedia)

                reply_markup = InlineKeyboardMarkup(keyboard)

                update.message.reply_text(
                    "We found the following media for you:",
                    reply_markup=reply_markup
                )

            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"The specified query has no results, "
                    f"{update.effective_user.first_name}.")
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Please specify a query, "
                f"{update.effective_user.first_name}.")

    def grant(self, update, context):
        if self.isAdmin(update, context, True):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:remarker, 1:source of person, 2:userid

            if (data[2] in self.signups or data[2] in self.rejected):

                if data[1] == "new":
                    self.members[data[2]] = \
                        self.signups[data[2]]
                    self.signups.pop(data[2], None)

                if data[1] == "denied":
                    self.members[data[2]] = \
                        self.rejected[data[2]]
                    self.rejected.pop(data[2], None)

                self.saveconfig(self.pixlovarr_members_file, self.members)
                self.saveconfig(self.pixlovarr_signups_file, self.signups)
                self.saveconfig(
                    self.pixlovarr_rejected_file, self.rejected)

                logging.info(
                    f"{self.members[data[2]]['fname']} - "
                    f"{self.members[data[2]]['id']} was added"
                    f" to the memberlist."
                )

                context.bot.send_message(
                    chat_id=self.members[data[2]]['id'],
                    text=(
                        f"Hi {self.members[data[2]]['fname']}, "
                        f"access was granted. For your new commands, "
                        f"please use /help."
                    )
                )

                context.bot.send_message(
                    chat_id=self.admin_user_id,
                    text=(
                        f"Hi admin, "
                        f"{self.members[data[2]]['fname']} "
                        f"was granted access. Message has been sent."
                    )
                )

    def reject(self, update, context):
        if self.isAdmin(update, context, True):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")

            if (data[2] in self.signups or data[2] in self.members):

                if data[1] == "new":
                    self.rejected[data[2]] = \
                        self.signups[data[2]]
                    self.signups.pop(data[2], None)

                if data[1] == "allowed":
                    self.rejected[data[2]] = \
                        self.members[data[2]]
                    self.members.pop(data[2], None)

                self.saveconfig(self.pixlovarr_members_file, self.members)
                self.saveconfig(self.pixlovarr_signups_file, self.signups)
                self.saveconfig(
                    self.pixlovarr_rejected_file, self.rejected)

                logging.info(
                    f"User {self.rejected[data[2]]['fname']} - "
                    f"{self.rejected[data[2]]['id']} was rejected."
                )

                context.bot.send_message(
                    chat_id=self.rejected[data[2]]['id'],
                    text=(
                        f"Hi {self.rejected[data[2]]['fname']}, "
                        f"access was rejected."
                    )
                )

                context.bot.send_message(
                    chat_id=self.admin_user_id,
                    text=(
                        f"Hi admin, "
                        f"{self.rejected[data[2]]['fname']} "
                        f"was rejected. Message has been sent."
                    )
                )

# Init Handlers
    def setHandlers(self):

        # Default Handlers
        self.updater = Updater(token=self.bot_token, use_context=True)
        self.dispatcher = self.updater.dispatcher

        self.start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(self.start_handler)

        self.signup_handler = CommandHandler('signup', self.signup)
        self.dispatcher.add_handler(self.signup_handler)

        self.help_handler = CommandHandler('help', self.help)
        self.dispatcher.add_handler(self.help_handler)

        self.userid_handler = CommandHandler('userid', self.userid)
        self.dispatcher.add_handler(self.userid_handler)

# Member Handlers

        self.series_handler = CommandHandler('ls', self.list)
        self.dispatcher.add_handler(self.series_handler)

        self.downloadseries_handler = CommandHandler('ds', self.downloadSeries)
        self.dispatcher.add_handler(self.downloadseries_handler)

        self.movies_handler = CommandHandler('lm', self.list)
        self.dispatcher.add_handler(self.movies_handler)

        self.downloadmovies_handler = CommandHandler('dm', self.downloadMovies)
        self.dispatcher.add_handler(self.downloadmovies_handler)

        self.showqueue_handler = CommandHandler('qu', self.showQueue)
        self.dispatcher.add_handler(self.showqueue_handler)

        self.showRankings_handler = CommandHandler(
            'ps', self.showRankings)
        self.dispatcher.add_handler(self.showRankings_handler)

        self.showTopSeries_handler = CommandHandler(
            'ts', self.showRankings)
        self.dispatcher.add_handler(self.showTopSeries_handler)

        self.showPopularMovies_handler = CommandHandler(
            'pm', self.showRankings)
        self.dispatcher.add_handler(self.showPopularMovies_handler)

        self.showtopMovies_handler = CommandHandler(
            'tm', self.showRankings)
        self.dispatcher.add_handler(self.showtopMovies_handler)

        self.showtopIndianMovies_handler = CommandHandler(
            'ti', self.showRankings)
        self.dispatcher.add_handler(self.showtopIndianMovies_handler)

        self.showBottomMovies_handler = CommandHandler(
            'wm', self.showRankings)
        self.dispatcher.add_handler(self.showBottomMovies_handler)

        self.futurequeue_handler = CommandHandler('fq', self.futureQueue)
        self.dispatcher.add_handler(self.futurequeue_handler)

        self.displayInfo_handler = CommandHandler('di', self.displayInfo)
        self.dispatcher.add_handler(self.displayInfo_handler)

        self.showMovieCalendar_handler = CommandHandler('mc', self.geCalendar)
        self.dispatcher.add_handler(self.showMovieCalendar_handler)

        self.showSerieCalendar_handler = CommandHandler('sc', self.geCalendar)
        self.dispatcher.add_handler(self.showSerieCalendar_handler)

# Keyboard Handlers

        kbgrant_handler = CallbackQueryHandler(
            self.grant, pattern='^grant:')
        self.dispatcher.add_handler(kbgrant_handler)

        kbreject_handler = CallbackQueryHandler(
            self.reject, pattern='^reject:')
        self.dispatcher.add_handler(kbreject_handler)

        kbselectDownload_handler = CallbackQueryHandler(
            self.selectDownload, pattern='^selectdownload:')
        self.dispatcher.add_handler(kbselectDownload_handler)

        kbshowDownloadSummary_handler = CallbackQueryHandler(
            self.showDownloadSummary, pattern='^showdlsummary:')
        self.dispatcher.add_handler(kbshowDownloadSummary_handler)

        kbdownloadMedia_handler = CallbackQueryHandler(
            self.downloadMedia, pattern='^downloadmedia:')
        self.dispatcher.add_handler(kbdownloadMedia_handler)

        kbdeleteMedia_handler = CallbackQueryHandler(
            self.deleteMedia, pattern='^deletemedia:')
        self.dispatcher.add_handler(kbdeleteMedia_handler)

        kbdeleteQueueItem_handler = CallbackQueryHandler(
            self.deleteQueueItem, pattern='^deletequeueitem:')
        self.dispatcher.add_handler(kbdeleteQueueItem_handler)

# Admin Handlders

        self.new_handler = CommandHandler('new', self.new)
        self.dispatcher.add_handler(self.new_handler)

        self.allowed_handler = CommandHandler('allowed', self.allowed)
        self.dispatcher.add_handler(self.allowed_handler)

        self.denied_handler = CommandHandler('denied', self.denied)
        self.dispatcher.add_handler(self.denied_handler)

        self.cmdhistory_handler = CommandHandler(
            'history', self.showCmdHistory
        )
        self.dispatcher.add_handler(self.cmdhistory_handler)

        self.delete_handler = CommandHandler('del', self.displayInfo)
        self.dispatcher.add_handler(self.delete_handler)

        self.unknown_handler = MessageHandler(Filters.command, self.unknown)
        self.dispatcher.add_handler(self.unknown_handler)

# Bot

    def startBot(self):
        self.setHandlers()
        self.updater.start_polling()

    def stopBot(self):
        self.updater.idle()


if __name__ == '__main__':

    pixlovarr = Pixlovarr()
    pixlovarr.startBot()
    pixlovarr.stopBot()
    pixlovarr = None
