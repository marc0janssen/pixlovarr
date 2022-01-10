# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 2021-12-31 16:41:03

from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    error
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)
from urllib.parse import urlparse
from time import time, sleep
from datetime import datetime, timedelta, date

from pycliarr.api import (
    RadarrCli, RadarrMovieItem
)
from pycliarr.api import (
    SonarrCli, SonarrSerieItem
)

from arrapi import SonarrAPI, RadarrAPI

import logging
import json
import configparser
import shutil
import sys
import re
import imdb
import random
import feedparser
import ssl
import os
import glob


class Pixlovarr():

    def __init__(self):

        self.version = "1.19.0.2937"
        self.startTime = datetime.now()
        config_dir = "./config/"
        app_dir = "./app/"
        log_dir = "./log/"

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)

        logging.info("")
        logging.info(f"*** Initializing Pixlovarr version: {self.version} ***")
        logging.info("")

        self.urlNoImage = (
            "https://postimg.cc/3dfySHP9"
        )

        self.availability = ["announced", "inCinemas", "released", "preDB"]

        self.config_file = f"{config_dir}pixlovarr.ini"
        self.log_filePath = f"{log_dir}pixlovarr.log"

        self.cmdHistory = []
        self.maxCmdHistory = 50
        self.rankingLimitMin = 3
        self.rankingLimitMax = 100
        self.listLength = 25
        self.youTubeURL = "https://www.youtube.com/watch?v="

        self.newsFeedSeries = "feed:https://www.metacritic.com/rss/tv"
        self.newsFeedMovies = "feed:https://www.metacritic.com/rss/movies"

        ssl._create_default_https_context = ssl._create_unverified_context

        self.imdb = imdb.IMDb()

        try:
            with open(self.config_file, "r") as f:
                f.close()
            try:

                # COMMON
                self.config = configparser.ConfigParser()
                self.config.read(self.config_file)
                self.bot_token = self.config['COMMON']['BOT_TOKEN']
                self.admin_user_id = self.config['COMMON']['ADMIN_USER_ID']
                self.users_permanent_delete_media = True if (
                    self.config['COMMON']
                    ['PERMANENT_DELETE_MEDIA'] == "ON") else False
                self.users_can_only_delete_own_media = True if (
                    self.config['COMMON']['USERS_CAN_ONLY_DELETE_OWN_MEDIA'] ==
                    "ON") else False
                self.sign_up_is_open = True if (
                    self.config['COMMON']['SIGN_UP_IS_OPEN'] ==
                    "ON") else False
                self.path_largest_space = True if (
                    self.config['COMMON']
                    ['ONLY_SHOW_PATH_LARGEST_FREE_SPACE'] ==
                    "ON") else False
                self.exclude_admin = True if (
                    self.config['COMMON']
                    ['EXCLUDE_ADMIN_FROM_HISTORY'] ==
                    "ON") else False

                # IMDB
                self.default_limit_ranking = self.clamp(
                    int(self.config['IMDB']['DEFAULT_LIMIT_RANKING']),
                    self.rankingLimitMin,
                    self.rankingLimitMax
                )

                # SONARR
                self.sonarr_enabled = True if (
                    self.config['SONARR']['ENABLED'] == "ON") else False
                self.sonarr_season_folder = True if (
                    self.config['SONARR']['SEASON_FOLDER'] == "ON") else False
                self.sonarr_url = self.config['SONARR']['URL']
                self.sonarr_token = self.config['SONARR']['TOKEN']
                self.calendar_period_days_series = \
                    self.config['SONARR']['CALENDAR_PERIOD_DAYS_SERIES']
                self.sonarr_tags_exclusion = list(
                    self.config['SONARR']
                    ['AUTO_ADD_EXCLUSION'].split(","))
                self.sonarr_period_days_added = \
                    int(self.config['SONARR']['PERIOD_DAYS_ADDED_NEW_DOWLOAD'])
                self.tags_to_keep_sonarr = list(
                    self.config['SONARR']
                    ['TAGS_KEEP_MOVIES_ANYWAY'].split(",")
                )
                self.tags_to_extend_sonarr = list(
                    self.config['SONARR']
                    ['TAGS_TO_EXTEND_PERIOD_BEFORE_REMOVAL'].split(","))

                # RADARR
                self.radarr_enabled = True if (
                    self.config['RADARR']['ENABLED'] == "ON") else False
                self.radarr_url = self.config['RADARR']['URL']
                self.radarr_token = self.config['RADARR']['TOKEN']
                self.calendar_period_days_movies = \
                    self.config['RADARR']['CALENDAR_PERIOD_DAYS_MOVIES']
                self.radarr_tags_exclusion = list(
                    self.config['RADARR']
                    ['AUTO_ADD_EXCLUSION'].split(","))
                self.radarr_period_days_added = \
                    int(self.config['RADARR']['PERIOD_DAYS_ADDED_NEW_DOWLOAD'])
                self.tags_to_keep_radarr = list(
                    self.config['RADARR']
                    ['TAGS_KEEP_MOVIES_ANYWAY'].split(",")
                )
                self.tags_to_extend_radarr = list(
                    self.config['RADARR']
                    ['TAGS_TO_EXTEND_PERIOD_BEFORE_REMOVAL'].split(","))

                # PRUNE
                self.extend_by_days = int(
                    self.config['PRUNE']['EXTEND_PERIOD_BY_DAYS'])
                self.remove_after_days = int(
                    self.config['PRUNE']['REMOVE_MOVIES_AFTER_DAYS'])

                if self.sonarr_enabled:
                    self.sonarr_node = SonarrCli(
                        self.sonarr_url, self.sonarr_token
                    )
                    self.sonarrNode = SonarrAPI(
                        self.sonarr_url, self.sonarr_token)
                self.video_extensions = list(
                    self.config['PRUNE']
                    ['VIDEO_EXTENSIONS_MONITORED'].split(","))

                if self.radarr_enabled:
                    self.radarr_node = RadarrCli(
                        self.radarr_url, self.radarr_token
                    )
                    self.radarrNode = RadarrAPI(
                        self.radarr_url, self.radarr_token)

                if not self.sonarr_enabled and not self.radarr_enabled:
                    logging.error(
                        "Sonarr nor Radarr are enabled. Exiting."
                    )

                    sys.exit()

                self.pixlovarr_signups_file = (
                    f"{config_dir}pixlovarr_signups.json")
                self.pixlovarr_members_file = (
                    f"{config_dir}pixlovarr_members.json")
                self.pixlovarr_blocked_file = (
                    f"{config_dir}pixlovarr_blocked.json")
                self.pixlovarr_data_file = (
                    f"{config_dir}pixlovarr_data.json")

                self.signups = self.loaddata(self.pixlovarr_signups_file)
                self.members = self.loaddata(self.pixlovarr_members_file)
                self.blockedusers = self.loaddata(self.pixlovarr_blocked_file)
                self.pixlovarrdata = self.loaddata(self.pixlovarr_data_file)

                if not self.pixlovarrdata:
                    self.pixlovarrdata["uname"] = "<unknown>"
                    self.pixlovarrdata["timestamp"] = \
                        datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
                    self.pixlovarrdata["stitle"] = "<not available yet>"
                    self.pixlovarrdata["mtitle"] = "<not available yet>"
                    self.pixlovarrdata["cmdcount"] = 0

                    self.saveconfig(
                        self.pixlovarr_data_file, self.pixlovarrdata)

            except KeyError as e:
                logging.error(
                    f"Seems a key(s) {e} is missing from INI file. "
                    f"Please check for mistakes. Exiting."
                )

                sys.exit()

            except ValueError as e:
                logging.error(
                    f"Seems a invalid value in INI file. "
                    f"Please check for mistakes. Exiting. "
                    f"MSG: {e}"
                )

                sys.exit()

        except IOError or FileNotFoundError:
            logging.error(
                f"Can't open file {self.config_file}, "
                f"creating example INI file."
            )

            shutil.copyfile(f"{app_dir}pixlovarr.ini.example",
                            f"{config_dir}pixlovarr.ini.example")
            sys.exit()

    def getPruneDate(self, media):

        if media.path:
            movieDownloadDate = None
            fileList = glob.glob(media.path + "/*")
            for file in fileList:
                if file.lower().endswith(tuple(self.video_extensions)):
                    # Get modfified date on movie.nfo,
                    # Which is the downloaddate
                    modifieddate = os.stat(file).st_mtime
                    movieDownloadDate = \
                        datetime.fromtimestamp(modifieddate)
                    break

            if movieDownloadDate:
                pruneMovieDate = movieDownloadDate + \
                    timedelta(days=int(self.remove_after_days)) + \
                    timedelta(days=int(self.extend_by_days))

                return datetime.strftime(pruneMovieDate, '%Y-%m-%d')

        return False

    def getProfileInfo(self, profileID, mediaOfType):

        if mediaOfType == "serie":
            if self.sonarr_enabled:
                profiles = self.sonarrNode.quality_profile()

        else:
            if self.radarr_enabled:
                profiles = self.radarrNode.quality_profile()

        if profiles:

            for p in profiles:

                if p.id == profileID:
                    return p.name

        return ""

    def getTopAmount(self, update, context, ranking):
        if re.match("^[Tt]\\d+$", ranking):
            return self.clamp(
                int(ranking[1:]),
                self.rankingLimitMin,
                self.rankingLimitMax
            )
        else:

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                f"Defaulting to Top {self.default_limit_ranking}"
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

    def getForMedia(self, tagIDs, typeOfMedia):

        if typeOfMedia == "serie":
            tags = self.sonarrNode.all_tags()
        else:
            tags = self.radarrNode.all_tags()

        txtTags = ""

        for tag in tags:
            if tag.id in tagIDs:
                txtTags += f"{tag.label}, "

        return txtTags[:-2]

    def countItemsinQueue(
        self, update, context,
            numOfItems, queue, typeOfMedia):

        txtQueue = ""

        for queueitem in queue["records"]:

            try:
                if typeOfMedia == "episode":
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

            text = (
                f"{queueitem['title']}\n"
                f"Status: {queueitem['status']}\n"
                f"Protocol: {queueitem['protocol']}\n"
                f"Timeleft: {tl}\n"
                f"ETA: {pt}"
            )

            # title = (
            #     f"{queueitem['title']} "
            # )

            numOfItems += 1

            # if numOfItems <= 3:
            #     callbackdata = (
            #         f"deletequeueitem:{typeOfMedia}:"
            #         f"{queueitem['id']}"
            #     )

            #     keyboard = [[InlineKeyboardButton(
            #         f"Remove {title}",
            #         callback_data=callbackdata)]]

            #     reply_markup = InlineKeyboardMarkup(keyboard)

            #     self.replytext(
            #         update,
            #         text,
            #         reply_markup,
            #         False
            #     )

            # else:

            txtQueue += f"{text}\n\n"

            if (numOfItems % self.listLength == 0 and numOfItems != 0):
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    txtQueue
                )

                txtQueue = ""

                # make sure no flood
                sleep(2)

        if txtQueue != "":
            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                txtQueue
            )

        return numOfItems

    def sortOnTitle(self, e):
        return e.sortTitle

    def sortOnNameDict(self, e):
        return e.name

    def addItemToHistory(self, update, cmd, uname, uid):

        if self.isAdmin(update) and not self.exclude_admin \
                or not self.isAdmin(update):

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

    def isAdmin(self, update):
        return True \
            if str(update.effective_user.id) == self.admin_user_id else False

    def isSignUpOpen(self):
        return self.sign_up_is_open

    def isBlocked(self, update):
        return str(update.effective_user.id) in self.blockedusers

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

    def outputMediaInfo(self, update, context, typeOfMedia, media):

        txtMediaInfo = ""

        if media.images:
            image = f"{media.images[0].url}" \
                if self.is_http_or_https(media.images[0].url) \
                    else media.images[0].remoteUrl
        else:
            image = self.urlNoImage

        caption = f"{media.title} ({media.year})"
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image, caption=caption
        )

        try:
            if media.overview:
                textoverview = f"{media.overview[:4092]}\n\n" if \
                    media.overview != "" else "No description available.\n\n"
            else:
                textoverview = "No description available.\n\n"
        except AttributeError:
            textoverview = "No description available.\n\n"

        txtMediaInfo += textoverview

        try:
            if media.inCinemas:
                dateCinema = datetime.strftime(
                    media.inCinemas, '%Y-%m-%d')
                txtCinema = f"In cinemas: {dateCinema}\n\n"
                txtMediaInfo += txtCinema
        except ValueError:
            pass
        except AttributeError:
            pass

        try:
            if media.firstAired:
                dateFirstAired = datetime.strftime(
                    media.firstAired, '%Y-%m-%d')
                txtFirstAired = f"First aired: {dateFirstAired}\n\n"
                txtMediaInfo += txtFirstAired
        except ValueError:
            pass
        except AttributeError:
            pass

        try:
            if media.episodeCount > 0:
                txtEpisode = f"Episode count: {media.episodeCount}\n\n"
                txtMediaInfo += txtEpisode
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

            txtMediaInfo += f"Quality: {qualityText}\n\n"

        if media.tags:
            txtMediaInfo += \
                f"Tags: {self.getForMedia(media.tags, typeOfMedia)}\n\n"

        if typeOfMedia == "movie" and self.getPruneDate(media):
            txtMediaInfo += f"Prune: {self.getPruneDate(media)}"

        if txtMediaInfo != "":

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                txtMediaInfo
            )

        try:
            if media.youTubeTrailerId:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"{self.youTubeURL}{media.youTubeTrailerId}"
                )

        except AttributeError:
            # No Youtube ID found
            pass

    def showCalenderMediaInfo(self, media):

        try:
            serie = self.sonarr_node.get_serie(media["seriesId"])
            title = f"{serie.title}\n{media['title']}"
        except KeyError:
            try:
                title = f"{media['title']} ({media['year']})"
            except KeyError:
                title = "<Title unknown>"

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

    def listMedia(
            self,
            update,
            context,
            typeOfMedia,
            media,
            usertagEnabled,
            newDownloadOnly
    ):

        keyboard = []
        media.sort(key=self.sortOnTitle)

        genre = ""
        if len(context.args) > 0:
            for x in range(len(context.args)):
                if re.match("^#[A-Za-z]+$", context.args[0]):
                    if not genre:
                        genre = context.args[0][1:]
                    context.args.pop(0)

        headtxt = (
            f"The following {typeOfMedia}s "
            f"in the catalog:"
        )

        numOfMedia = 0
        for m in media:

            if usertagEnabled:
                usertagID = self.getUsertagID(update, typeOfMedia)
                usertagFound = usertagID in m.tags

            if newDownloadOnly:
                if typeOfMedia == "serie":
                    dateAfterAdded = datetime.now() - \
                        timedelta(days=self.sonarr_period_days_added)

                else:
                    dateAfterAdded = datetime.now() - \
                        timedelta(days=self.radarr_period_days_added)

                withinPeriod = True if m.added >= \
                    dateAfterAdded else False

            if (not usertagEnabled and not newDownloadOnly) or \
                    (usertagEnabled and usertagFound) or \
                    (newDownloadOnly and withinPeriod):

                if re.search(
                    ' '.join(context.args).lower(), m.title.lower()) \
                        or not context.args:

                    if genre.lower() in (
                        genre.lower() for genre in m.genres) \
                            or not genre:

                        callbackdata = \
                            f"showMediaInfo:{typeOfMedia}:{m.id}"

                        keyboard.append([InlineKeyboardButton(
                            f"{m.title} ({m.year})",
                            callback_data=callbackdata)]
                        )

                        numOfMedia += 1

                        if (numOfMedia % self.listLength == 0 and
                                numOfMedia != 0):

                            if numOfMedia >= self.listLength:
                                headtxt = "Next section of the catalog:"

                            reply_markup = InlineKeyboardMarkup(keyboard)

                            self.replytext(
                                update,
                                headtxt,
                                reply_markup,
                                False
                            )

                            keyboard = []

                            # make sure no flood
                            sleep(2)

        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)

            self.replytext(
                update,
                headtxt,
                reply_markup,
                False
            )

        return numOfMedia

    def listCalendar(self, update, context, media):

        numOfCalItems = 0
        if type(media) is SonarrSerieItem or \
                type(media) is RadarrMovieItem:

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                self.showCalenderMediaInfo(media)
            )

            numOfCalItems = 1

        else:

            allMedia = ""
            for m in media:

                try:
                    searchString = f"{m['series']['title']} {m['title']}"
                except KeyError:
                    searchString = m['title']

                if re.search(
                    ' '.join(context.args).lower(), searchString.lower()) \
                        or not context.args:

                    numOfCalItems += 1

                    allMedia += (
                        self.showCalenderMediaInfo(m))

                    if (numOfCalItems % self.listLength == 0 and
                            numOfCalItems != 0):

                        self.sendmessage(
                            update.effective_chat.id,
                            context,
                            update.effective_user.first_name,
                            allMedia
                        )

                        allMedia = ""

                        # make sure no flood
                        sleep(2)

            if allMedia != "":
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    allMedia
                )

        return numOfCalItems

    def writeLog(self, msg):
        try:
            logfile = open(self.log_filePath, "a")
            logfile.write(f"{datetime.now()} - {msg}\n")
            logfile.close()
        except IOError:
            logging.error(
                f"Can't write file {self.log_filePath}"
            )

    def logChoice(self, update, choice):

        service = "Open" if self.isSignUpOpen() else "Closed"
        typeOfUser = "Blocked member" if self.isBlocked(update) else \
            "Non member" if not self.isGranted(update) else \
            "Member" if not self.isAdmin(update) else "Admin"

        msg = (
            f"{service} - {typeOfUser} "
            f"{update.effective_user.first_name} - "
            f"{update.effective_user.id} "
            f"chose '{choice}'"
        )

        logging.info(msg)

        self.writeLog(msg)

    def logAdminCommand(self, update):

        service = "Open" if self.isSignUpOpen() else "Closed"
        typeOfUser = "Blocked member" if self.isBlocked(update) else \
            "Non member" if not self.isGranted(update) else \
            "Member" if not self.isAdmin(update) else "Admin"

        self.logCommand(update)

        if not self.isAdmin(update):
            logging.warning(
                f"{service} - {typeOfUser} "
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"was unauthorized for previous command "
                f"{update.effective_message.text}. "
                f"Command was not executed."
            )

    def logCommand(self, update):

        service = "Open" if self.isSignUpOpen() else "Closed"
        typeOfUser = "Blocked member" if self.isBlocked(update) else \
            "Non member" if not self.isGranted(update) else \
            "Member" if not self.isAdmin(update) else "Admin"

        msg = (
            f"{service} - {typeOfUser} "
            f"{update.effective_user.first_name} - "
            f"{update.effective_user.id} "
            f"issued {update.effective_message.text}"
        )

        if not self.isBlocked(update):

            self.pixlovarrdata["uname"] = \
                str(self.cmdHistory[-1]["uname"]) \
                if len(self.cmdHistory) != 0 else \
                update.effective_user.first_name

            self.pixlovarrdata["timestamp"] = \
                str(self.cmdHistory[-1]["timestamp"]) \
                if len(self.cmdHistory) != 0 else \
                datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

            logging.info(msg)

            self.writeLog(msg)

            self.addItemToHistory(
                update,
                f"{update.effective_message.text}",
                update.effective_user.first_name,
                update.effective_user.id
            )

            self.pixlovarrdata["cmdcount"] = len(self.cmdHistory)
            self.saveconfig(self.pixlovarr_data_file, self.pixlovarrdata)

        else:
            logging.warning(
                f"{msg} "
                f"No command was executed."
            )

    def notifyDownload(self, update, context, typeOfMedia, title, year):
        self.sendmessage(
            update.effective_chat.id,
            context,
            update.effective_user.first_name,
            f"The {typeOfMedia} '{title} ({year})' "
            f"was added to the server, "
            f"{update.effective_user.first_name}. "
            f"Thank you and till next time."
        )

        service = "Open" if self.isSignUpOpen() else "Closed"
        typeOfUser = "Blocked member" if self.isBlocked(update) else \
            "Non member" if not self.isGranted(update) else \
            "Member" if not self.isAdmin(update) else "Admin"

        logging.info(
            f"{service} - {typeOfUser} {update.effective_user.first_name} - "
            f"{update.effective_user.id} has added the "
            f"{typeOfMedia} '{title} ({year})' "
            f"to the server.")

    def notifyDeleteQueueItem(
            self, update, context, typeOfMedia, queueItemID):

        if typeOfMedia == "episode":
            if self.sonarr_enabled:
                queue = self.sonarr_node.get_queue()
        else:
            if self.radarr_enabled:
                queue = self.radarr_node.get_queue()

        for queueitem in queue:

            if int(queueItemID) == queueitem['id']:

                if typeOfMedia == "episode":
                    title = (
                        f"{queueitem['series']['title']} "
                        f"S{queueitem['episode']['seasonNumber']}"
                        f"E{queueitem['episode']['episodeNumber']} - "
                        f"{queueitem['episode']['title']}"
                    )
                else:
                    title = (
                        f"{queueitem['movie']['title']} "
                        f"({queueitem['movie']['year']})"
                    )

                break

        self.sendmessage(
            update.effective_chat.id,
            context,
            update.effective_user.first_name,
            f"The {typeOfMedia} {title} was deleted from the queue."
        )

        logging.info(
            f"{update.effective_user.first_name} - "
            f"{update.effective_user.id} has deleted the "
            f"{typeOfMedia} '{title}' "
            f"from the queue."
        )

        self.logChoice(update, f"Delete {typeOfMedia} {title} from queue")

    def createTagName(self, username, userid):
        # make striped username with only az09
        strippedfirstname = re.sub(
            r'[^A-Za-z0-9]+', '', username.lower())
        return f"{strippedfirstname}_{userid}"

    def getUsertagID(self, update, typeOfMedia):

        tagName = self.createTagName(
            update.effective_user.first_name, update.effective_user.id)

        tagnames = self.getTagLabeltoID(typeOfMedia)

        # Return the ID of the usertag if found on the server
        return tagnames.get(tagName)

    def getTagLabeltoID(self, typeOfMedia):
        # Put all tags in a dictonairy with pair label <=> ID

        TagLabeltoID = {}
        if typeOfMedia == "serie":
            for tag in self.sonarrNode.all_tags():
                # Add tag to lookup by it's name
                TagLabeltoID[tag.label] = tag.id
        else:
            for tag in self.radarrNode.all_tags():
                # Add tag to lookup by it's name
                TagLabeltoID[tag.label] = tag.id

        return TagLabeltoID

    def getIDsforTagLabels(self, typeOfmedia, tagLabels):

        TagLabeltoID = self.getTagLabeltoID(typeOfmedia)

        # Get ID's for extending media
        tagsIDs = []
        for taglabel in tagLabels:
            tagID = TagLabeltoID.get(taglabel)
            if tagID:
                tagsIDs.append(tagID)

        return tagsIDs

    def sendmessage(self, chat_id, context, username, msg):

        try:
            context.bot.send_message(
                chat_id=chat_id, text=msg)

        except error.Unauthorized as e:
            logging.error(
                f"{e} - {username} - {chat_id}.")

        except error.NetworkError as e:
            logging.error(
                f"{e} - {username} - {chat_id}.")

        except error.TimedOut as e:
            logging.error(
                f"{e}."
            )

    def replytext(self, update, msg, reply_markup, quote):

        try:
            update.message.reply_text(
                msg,
                reply_markup=reply_markup,
                quote=quote
            )

        except error.Unauthorized as e:
            logging.error(
                f"{e}."
            )
        except error.TimedOut as e:
            logging.error(
                f"{e}."
            )

# Default Commands

    def start(self, update, context):

        self.logCommand(update)

        if (not self.isBlocked(update) and self.isSignUpOpen()) or \
                self.isGranted(update) or self.isAdmin(update):

            if not self.isGranted(update):
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"Welcome {update.effective_user.first_name} "
                    f"to Pixlovarr, I'm your assistent for "
                    f"downloading series and movies. Please use /help "
                    f"for more information. But first request access "
                    f"with /signup."
                )
            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "You are still granted for the service."
                )

    def signup(self, update, context):

        self.logCommand(update)

        if (not self.isBlocked(update) and self.isSignUpOpen()) or \
                self.isGranted(update) or self.isAdmin(update):

            if not self.isGranted(update):
                if not str(update.effective_user.id) in self.signups:

                    self.person = {}
                    self.person['fname'] = update.effective_user.first_name
                    self.person['lname'] = update.effective_user.last_name
                    self.person['uname'] = update.effective_user.username
                    self.person['id'] = str(update.effective_user.id)

                    self.signups[self.person['id']] = self.person

                    self.saveconfig(self.pixlovarr_signups_file, self.signups)

                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        f"Thank you {update.effective_user.first_name}, "
                        f"for signing up. The admin has been notified. "
                        f"Please be patient and you will be added to "
                        f"the memberlist soon."
                    )

                    self.sendmessage(
                        self.admin_user_id,
                        context,
                        "Admin",
                        f"Hi admin, {self.person['fname']} wants access.\n"
                        f"Use /new to list all new members.\n"
                    )

                else:
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        f"Please be patient "
                        f"{update.effective_user.first_name}, "
                        f"we get you hooked up as soon as possible."
                    )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"No need to sign up twice, "
                    f"{update.effective_user.first_name}"
                )

    def help(self, update, context):

        self.logCommand(update)

        if (not self.isBlocked(update) and self.isSignUpOpen()) or \
                self.isGranted(update) or self.isAdmin(update):

            helpText = (
                "-- Commands --\n"
                "/start - Start this bot\n"
                "/help - Show this text\n"
                "/signup - Request access\n"
                "/userid - Show your userid\n"
            )

            if self.isGranted(update):
                helpText = helpText + (
                    "/ls #<genre> <key> - List all series\n"
                    "/lm #<genre> <key> - List all movies\n"
                    "/ms #<genre> <key> - list my series\n"
                    "/mm #<genre> <key> - list my movies\n"
                    "/ns #<genre> <key> - list new series\n"
                    "/nm #<genre> <key> - list new movies\n"
                    "/qu - List all queued items\n"
                    "/ts T<#> - Show Top series\n"
                    "/ps T<#> - Show Top popular series\n"
                    "/tm T<#> - Show Top movies\n"
                    "/pm T<#> - Show Top popular movies\n"
                    "/ti T<#> - Show Top Indian movies\n"
                    "/wm T<#> - Show Top worst movies\n"
                    "/rs - Show recently reviewed series\n"
                    "/rm - Show recently reviewed movies\n"
                    "/fq - Show announced items in catalog\n"
                    "/sc - Show series calendar\n"
                    "/mc - Show movies calendar\n"
                    "/sts - Service status info\n"
                    "/rss - Trigger RSS fetching\n"
                    "/smm - Trigger missing media search\n"
                    "/ds T<#> <key> - Download series\n"
                    "/dm T<#> <key> - Download movie\n\n"
                    "/coffee - Buy me a coffee\n"

                )

            if self.isAdmin(update):
                helpText = helpText + (
                    "\n-- Admin commands --\n"
                    "/new - Show all new signups\n"
                    "/am - Show all allowed members\n"
                    "/bm - Show all blocked members\n"
                    "/ch - Show command history\n"
                    "/lt - list tags\n"
                    "/open - open signup\n"
                    "/close - close signup\n"
                )

            helpText += f"\nversion: {self.version}\n"

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                helpText
            )

    def userid(self, update, context):

        self.logCommand(update)

        if (not self.isBlocked(update) and self.isSignUpOpen()) or \
                self.isGranted(update) or self.isAdmin(update):

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                f"Hi {update.effective_user.first_name}, "
                f"your userid is {update.effective_user.id}."
            )

# Member Commands

    def performRSS(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and self.isGranted(update):

            txtRSSsync = (
                "-- RSS Sync triggerd --\n"
                "RSS request sent. Latest media posts are being fetched. "
                "If any new media is available, the download clients are "
                "triggered.\n\n"
            )

            if self.sonarr_enabled:
                respSonarr = self.sonarrNode.send_command("RssSync")
                txtRSSsync += (
                    f"Sonarr message: {respSonarr.message}\n"
                    f"Sonarr priority: {respSonarr.priority}\n\n"
                )
            if self.radarr_enabled:
                respRadarr = self.radarrNode.send_command("RssSync")
                txtRSSsync += (
                    f"Radarr message: {respRadarr.message}\n"
                    f"Radarr priority: {respRadarr.priority}\n"
                )

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                txtRSSsync
            )

    def buymeacoffee(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and self.isGranted(update):

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Thank you for considering a tip.\n"
                "I love converting coffee into code.\n"
                "Hope you enjoy these zeros and ones.\n"
                "Thanks for tipping me, it is appreciated.\n\n"
                "https://ko-fi.com/marc0janssen"
            )

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "You can tip me on Bitcoin too.\n"
                "Thanks for tipping me, it is appreciated.\n\n"
                "https://marc0janssen.github.io/bitcoin.html"
            )

    def serviceStatus(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and self.isGranted(update):

            numOfQueueItems = 0

            if self.sonarr_enabled:
                queuesonarr = self.sonarr_node.get_queue()
                numOfQueueItems = int(queuesonarr["totalRecords"])

            if self.radarr_enabled:
                queueradarr = self.radarr_node.get_queue()
                numOfQueueItems += int(queueradarr["totalRecords"])

            service = "Open" if self.isSignUpOpen() else "Closed"

            stsText = (
                f"-- Status --\n"
                f"Uptime service: "
                f"{str(datetime.now() - self.startTime).split('.')[0]}\n"
                f"Last active member: {str(self.pixlovarrdata['uname'])}\n"
                f"Last timestamp: {str(self.pixlovarrdata['timestamp'])}\n"
                f"Last serie: {str(self.pixlovarrdata['stitle'])}\n"
                f"Last movie: {str(self.pixlovarrdata['mtitle'])}\n"
                f"series: {len(self.sonarrNode.all_series())}\n"
                f"movies: {len(self.radarrNode.all_movies())}\n"
                f"Items in queue: {str(numOfQueueItems)}\n"
                f"Commands issued: {str(self.pixlovarrdata['cmdcount'])}\n"
                f"Granted members: {len(self.members)}\n"
                f"Blocked members: {len(self.blockedusers)}\n"
                f"New signups: {len(self.signups)}\n"
                f"Signup: {service}\n"
                f"Service version: {self.version}\n"
            )

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                stsText
            )

    def showMeta(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and self.isGranted(update):

            command = update.effective_message.text.split(" ")

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Please be patient..."
            )

            if re.match("^/[Rr][Ss]$", command[0]):
                typeOfMedia = "serie"
                NewsFeed = feedparser.parse(self.newsFeedSeries)

            elif re.match("^/[Rr][Mm]$", command[0]):
                typeOfMedia = "movie"
                NewsFeed = feedparser.parse(self.newsFeedMovies)

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "Something went wrong..."
                )

                return

            if NewsFeed:

                keyboard = []

                for newsitem in NewsFeed.entries[:20]:

                    titleClean = newsitem.title.replace(":", " ")
                    # replace : for ' '

                    titleClean = re.sub(
                        '\\([0-9]+\\)',
                        '',
                        titleClean
                    )  # Remove (2019) for ''

                    titleClean = re.sub(
                        '\\([a-zA-Z\\s\\+]+\\)',
                        '',
                        titleClean
                    )  # Remove (Netflix) for ''

                    callbackdata = (
                        f"showMetaInfo:{typeOfMedia}:{titleClean}"[:64]
                    )

                    keyboard.append([InlineKeyboardButton(
                        f"{newsitem.title}",
                        callback_data=callbackdata)]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    update,
                    f"Top 20 recently reviewed {typeOfMedia}s:",
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"There are no {typeOfMedia}s in the newsfeed."
                )

    def getCalendar(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update):

            command = update.effective_message.text.split(" ")

            startDate = date.today()

            if re.match("^/[Ss][Cc]$", command[0]):
                if self.sonarr_enabled:
                    endDate = startDate + timedelta(
                        days=int(self.calendar_period_days_series))
                    media = self.sonarr_node.get_calendar(
                        start_date=startDate, end_date=endDate)
                    typeOfMedia = "episode"

            elif re.match("^/[Mm][Cc]$", command[0]):
                if self.radarr_enabled:
                    endDate = startDate + timedelta(
                        days=int(self.calendar_period_days_movies))
                    media = self.radarr_node.get_calendar(
                        start_date=startDate, end_date=endDate)
                    typeOfMedia = "movie"

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "Something went wrong..."
                )

                return

            endtext = f"There are no {typeOfMedia}s in the calendar."

            if media:
                numOfCalItems = self.listCalendar(update, context, media)
                endtext = (
                    f"There are {len(media)} {typeOfMedia}s "
                    f"in the calendar.")

                if numOfCalItems > 0:
                    if numOfCalItems != len(media):
                        endtext = (
                            f"Listed {numOfCalItems} of {len(media)} "
                            f"scheduled {typeOfMedia}s from the calendar."
                        )
                    else:
                        endtext = (
                            f"Listed {numOfCalItems} scheduled "
                            f"{typeOfMedia}s "
                            f"from the calendar."
                        )

                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        endtext
                    )

                else:
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        f"There were no results found, "
                        f"{update.effective_user.first_name}."
                    )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"There are no scheduled {typeOfMedia}s in the calendar."
                )

    def futureQueue(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update):

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Please be patient..."
            )

            if self.sonarr_enabled:
                series = self.sonarrNode.all_series()
                series.sort(key=self.sortOnTitle)

                endtext = "There is no media in the announced queue."

                fqCount = 0
                allSeries = "Series\n"

                for s in series:
                    if s.status == "upcoming":
                        fqCount += 1
                        allSeries += (
                            f"{s.title} ({str(s.year)})\n")

                        if (fqCount % self.listLength == 0 and
                                fqCount != 0):

                            self.sendmessage(
                                update.effective_chat.id,
                                context,
                                update.effective_user.first_name,
                                allSeries
                            )

                            allSeries = ""

                            # make sure no flood
                            sleep(2)

                if allSeries != "":
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        allSeries
                    )

                endtext = (
                    f"There are {fqCount} series in the announced queue.")

            if self.radarr_enabled:
                movies = self.radarrNode.all_movies()
                movies.sort(key=self.sortOnTitle)

                allMovies = "Movies\n"

                #  for m in movies:
                for m in movies:

                    #  if m.status == "announced":
                    if not m.hasFile:
                        fqCount += 1
                        allMovies += (
                            f"{m.title} ({str(m.year)})\n")

                        if (fqCount % self.listLength == 0 and
                                fqCount != 0):

                            self.sendmessage(
                                update.effective_chat.id,
                                context,
                                update.effective_user.first_name,
                                allMovies
                            )

                            allMovies = ""

                            # make sure no flood
                            sleep(2)

                if allMovies != "":
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        allMovies
                    )

                endtext = (
                    f"There are {fqCount} items in the announced queue.")

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                endtext
            )

    def showRankings(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update):

            command = update.effective_message.text.split(" ")

            topAmount = self.getTopAmount(
                update, context, ' '.join(context.args))

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Please be patient..."
            )

            if re.match("^/[Tt][Ss]$", command[0]):
                media = self.imdb.get_top250_tv()
                typeOfMedia = "serie"
                adjective = ""

            elif re.match("^/[Pp][Ss]$", command[0]):
                media = self.imdb.get_popular100_tv()
                typeOfMedia = "serie"
                adjective = "popular "

            elif re.match("^/[Tt][Mm]$", command[0]):
                media = self.imdb.get_top250_movies()
                typeOfMedia = "movie"
                adjective = ""

            elif re.match("^/[Pp][Mm]$", command[0]):
                media = self.imdb.get_popular100_movies()
                typeOfMedia = "movie"
                adjective = "popular "

            elif re.match("^/[Tt][Ii]$", command[0]):
                media = self.imdb.get_top250_indian_movies()
                typeOfMedia = "movie"
                adjective = "Indian "

            elif re.match("^/[Ww][Mm]$", command[0]):
                media = self.imdb.get_bottom100_movies()
                typeOfMedia = "movie"
                adjective = "worst "

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "Something went wrong..."
                )

                return

            keyboard = []
            keyboardPresentMedia = []

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

                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        random.choice(phrass)
                    )

                if typeOfMedia == "serie":

                    if self.sonarr_enabled:

                        foundMedia = \
                            self.sonarrNode.search_series(term=m['title'])

                        if foundMedia is None:
                            continue

                        foundMedia = foundMedia[0]
                        MediaID = foundMedia.tvdbId
                else:
                    if self.radarr_enabled:
                        foundMedia = \
                            self.radarrNode.search_movies(term=m['title'])
                        if foundMedia is None:
                            continue

                        foundMedia = foundMedia[0]
                        MediaID = foundMedia.imdbId

                # Is a not downloaded movie? Then show download button
                # Otherwise show mediainfo button
                if not foundMedia.id:
                    callbackdata = \
                        f"showdlsummary:{typeOfMedia}:{MediaID}"

                    keyboard.append([InlineKeyboardButton(
                        f"{foundMedia.title} ({foundMedia.year})",
                        callback_data=callbackdata)]
                    )

                else:
                    callbackdata = \
                        f"showMediaInfo:{typeOfMedia}:{foundMedia.id}"

                    keyboardPresentMedia.append([InlineKeyboardButton(
                        f"{foundMedia.title} ({foundMedia.year})",
                        callback_data=callbackdata)]
                    )

            if keyboardPresentMedia:
                reply_markup_PresentMedia = InlineKeyboardMarkup(
                    keyboardPresentMedia)

                self.replytext(
                    update,
                    f"We found these {adjective}{typeOfMedia}s of the "
                    f"IMDb top {topAmount} in the catalog:",
                    reply_markup_PresentMedia,
                    False
                )

            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    update,
                    f"These {adjective}{typeOfMedia}s of IMDb top {topAmount} "
                    f"are not in the catalog at the moment:",
                    reply_markup,
                    False
                )

    def showQueue(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update):

            numOfItems = 0

            if self.sonarr_enabled:
                queuesonarr = self.sonarr_node.get_queue()

                if queuesonarr["totalRecords"] != 0:
                    numOfItems = self.countItemsinQueue(
                        update, context, numOfItems, queuesonarr, "episode")

            if self.radarr_enabled:
                queueradarr = self.radarr_node.get_queue()

                if queueradarr["totalRecords"] != 0:
                    numOfItems = self.countItemsinQueue(
                        update, context, numOfItems, queueradarr, "movie")

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                f"There are {numOfItems} items in the queue."
            )

    def downloadSeries(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update) and \
                self.sonarr_enabled:

            self.findMedia(update, context, None, "serie", context.args)

    def listNewMedia(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update):

            command = update.effective_message.text.split(" ")

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Please be patient..."
            )

            media = []

            if re.match("^/[Nn][Ss]$", command[0]):
                typeOfMedia = "serie"
                if self.sonarr_enabled:
                    media = self.sonarrNode.all_series()

            elif re.match("^/[Nn][Mm]$", command[0]):
                typeOfMedia = "movie"
                if self.radarr_enabled:
                    media = self.radarrNode.all_movies()

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "Something went wrong..."
                )

                return

            if media:
                numofMedia = self.listMedia(
                    update, context, typeOfMedia, media, False, True)
                if numofMedia > 0:
                    if numofMedia != len(media):
                        endtext = (
                            f"Listed {numofMedia} of {len(media)} "
                            f"{typeOfMedia}s from the catalog."
                        )
                    else:
                        endtext = (
                            f"Listed {numofMedia} {typeOfMedia}s "
                            f"from the catalog."
                        )

                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        endtext
                    )

                else:
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        f"There were no results found, "
                        f"{update.effective_user.first_name}."
                    )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"There are no {typeOfMedia}s in the catalog."
                )

    def listMyMedia(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update):

            command = update.effective_message.text.split(" ")

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Please be patient..."
            )

            media = []

            if re.match("^/[Mm][Ss]$", command[0]):
                typeOfMedia = "serie"
                if self.sonarr_enabled:
                    media = self.sonarrNode.all_series()

            elif re.match("^/[Mm][Mm]$", command[0]):
                typeOfMedia = "movie"
                if self.radarr_enabled:
                    media = self.radarrNode.all_movies()

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "Something went wrong...."
                )

                return

            if media:
                numofMedia = self.listMedia(
                    update, context, typeOfMedia, media, True, False)
                if numofMedia > 0:
                    if numofMedia != len(media):
                        endtext = (
                            f"Listed {numofMedia} of {len(media)} "
                            f"{typeOfMedia}s from the catalog."
                        )
                    else:
                        endtext = (
                            f"Listed {numofMedia} {typeOfMedia}s "
                            f"from the catalog."
                        )

                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        endtext
                    )

                else:
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        f"There were no results found, "
                        f"{update.effective_user.first_name}."
                    )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"There are no {typeOfMedia}s in the catalog."
                )

    def list(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update):

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Please be patient..."
            )

            command = update.effective_message.text.split(" ")

            media = []

            if re.match("^/[Ll][Ss]$", command[0]):
                if self.sonarr_enabled:
                    media = self.sonarrNode.all_series()
                    typeOfMedia = "serie"

            elif re.match("^/[Ll][Mm]$", command[0]):
                if self.radarr_enabled:
                    media = self.radarrNode.all_movies()
                    typeOfMedia = "movie"

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "Something went wrong..."
                )

                return

            if media:
                numofMedia = self.listMedia(
                    update, context, typeOfMedia, media, False, False)
                if numofMedia > 0:
                    if numofMedia != len(media):
                        endtext = (
                            f"Listed {numofMedia} of {len(media)} "
                            f"{typeOfMedia}s from the catalog."
                        )
                    else:
                        endtext = (
                            f"Listed {numofMedia} {typeOfMedia}s "
                            f"from the catalog."
                        )

                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        endtext
                    )

                else:
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        f"There were no results found, "
                        f"{update.effective_user.first_name}."
                    )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"There are no {typeOfMedia}s in the catalog."
                )

    def downloadMovies(self, update, context):

        self.logCommand(update)

        if not self.isBlocked(update) and \
                self.isGranted(update) and \
                self.radarr_enabled:

            self.findMedia(update, context, None, "movie", context.args)

# Admin Commands

    def opensignup(self, update, context):

        self.logAdminCommand(update)

        if self.isAdmin(update):

            if not self.isSignUpOpen():

                self.sign_up_is_open = True
                msg = "Signup is now open."

            else:
                msg = "Signup was already open."

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                msg
            )

    def closesignup(self, update, context):

        self.logAdminCommand(update)

        if self.isAdmin(update):

            if self.isSignUpOpen():
                self.sign_up_is_open = False
                msg = "Signup is now closed."

            else:
                msg = "Signup was already closed."

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                msg
            )

    def listtags(self, update, context):

        self.logAdminCommand(update)

        if self.isAdmin(update):

            tagstxt = "-- Tags --\n"
            for member in self.members:
                person = self.members[member]
                strippedfname = re.sub(
                    r'[^A-Za-z0-9]+', '', person['fname'].lower())
                tagName = f"{strippedfname}_{person['id']}"
                tagstxt = tagstxt + f"{tagName}\n"

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                tagstxt
            )

    def showCmdHistory(self, update, context):

        self.logAdminCommand(update)

        if self.isAdmin(update):

            endtext = "No items in the command history."
            historytext = ""

            if self.cmdHistory:
                for count, historyItem in enumerate(self.cmdHistory):

                    historytext += (
                        f"{historyItem['timestamp']} - "
                        f"{historyItem['cmd']} - "
                        f"{historyItem['uname']} - "
                        f"{historyItem['uid']}\n"
                    )

                    if (count % self.listLength == 0 and count != 0):
                        self.sendmessage(
                            update.effective_chat.id,
                            context,
                            update.effective_user.first_name,
                            historytext
                        )

                        historytext = ""

                        # make sure no flood
                        sleep(2)

                if historytext != "":
                    self.sendmessage(
                        update.effective_chat.id,
                        context,
                        update.effective_user.first_name,
                        historytext
                    )

                endtext = (
                    f"Found {len(self.cmdHistory)} items "
                    f"in command history."
                )

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                endtext
            )

    def showSignups(self, update, context):

        self.logAdminCommand(update)

        if self.isAdmin(update):

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
                        callback_data=f"block:new:{person['id']}")
                    )

                    keyboard.append(row)

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    update,
                    "These are your new signups. Please Grant or Block:",
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "No new signups in the queue."
                )

    def showAllowed(self, update, context):

        self.logAdminCommand(update)

        if self.isAdmin(update):

            if self.members:

                keyboard = []

                for member in self.members:
                    person = self.members[member]
                    keyboard.append([InlineKeyboardButton(
                        f"-X- {person['fname']}",
                        callback_data=f"block:allowed:{person['id']}")]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    update,
                    "These are your members. Please block if needed:",
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "No members in the list."
                )

    def showBlocked(self, update, context):

        self.logAdminCommand(update)

        if self.isAdmin(update):

            if self.blockedusers:

                keyboard = []

                for member in self.blockedusers:
                    person = self.blockedusers[member]
                    keyboard.append([InlineKeyboardButton(
                        f"-√- {person['fname']}",
                        callback_data=f"grant:blocked:{person['id']}")]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    update,
                    "These members are blocked. Please grant if needed:",
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    "No members in the list."
                )

    def unknown(self, update, context):

        self.logCommand(update)

        if (not self.isBlocked(update) and self.isSignUpOpen()) or \
                self.isGranted(update) or self.isAdmin(update):

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                f"Sorry {update.effective_user.first_name}, "
                f"I didn't understand that command."
            )

# HandlerCallback Commands

    def keepMedia(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid

            self.logChoice(update, "Keep media")

            if data[1] == "serie":
                if self.sonarr_enabled:
                    media = self.sonarrNode.get_series(int(data[2]))
                    tagLabels_to_keep = self.tags_to_keep_sonarr
            else:
                if self.radarr_enabled:
                    media = self.radarrNode.get_movie(int(data[2]))
                    tagLabels_to_keep = self.tags_to_keep_radarr

            tagIDs_To_Keep = self.getIDsforTagLabels(
                data[1], tagLabels_to_keep)

            # If there not IDs yet, then create them for the first time
            if not tagIDs_To_Keep:
                if data[1] == "serie":
                    if self.sonarr_enabled:
                        tag = self.sonarrNode.create_tag(
                            tagLabels_to_keep[0])

                else:
                    if self.radarr_enabled:
                        tag = self.radarrNode.create_tag(
                            tagLabels_to_keep[0])

                tagIDs_To_Keep = [tag.id]

            if not set(media.tagsIds) & set(tagIDs_To_Keep):

                media.edit(
                    tags=[tagIDs_To_Keep[0]],
                    apply_tags="add"
                )

                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"The {data[1]} is kept on the server "
                    f"and refrained from pruning."
                )

    def extendPeriodMedia(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid

            self.logChoice(update, "Extend media retention")

            if data[1] == "serie":
                if self.sonarr_enabled:
                    media = self.sonarrNode.get_series(int(data[2]))
                    tagLabels_to_extend = self.tags_to_extend_sonarr
            else:
                if self.radarr_enabled:
                    media = self.radarrNode.get_movie(int(data[2]))
                    tagLabels_to_extend = self.tags_to_extend_radarr

            tagIDs_To_Extend = self.getIDsforTagLabels(
                data[1], tagLabels_to_extend)

            # If there not IDs yet, then create them for the first time
            if not tagIDs_To_Extend:
                if data[1] == "serie":
                    if self.sonarr_enabled:
                        tag = self.sonarrNode.create_tag(
                            tagLabels_to_extend[0])

                else:
                    if self.radarr_enabled:
                        tag = self.radarrNode.create_tag(
                            tagLabels_to_extend[0])

                tagIDs_To_Extend = [tag.id]

            if not set(media.tagsIds) & set(tagIDs_To_Extend):

                media.edit(
                    tags=[tagIDs_To_Extend[0]],
                    apply_tags="add"
                )

                # Get modfified date on movie.nfo,
                # Which is the downloaddate

                if self.getPruneDate(media):
                    newPruneDate = self.getPruneDate(media)

                    txtPruneDate = (
                        f"New prune date is {newPruneDate}."
                    )
                else:
                    txtPruneDate = (
                        "New prune date is not known because "
                        "movie file missing."
                    )

                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"The {data[1]} retention is extended with another "
                    f"{self.extend_by_days} days. "
                    f"{txtPruneDate}"
                )

    def searchMissingMedia(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            # query = update.callback_query
            # query.answer()
            # data = query.data.split(":")
            # # 0:marker, 1:type of media

            # called via /smm, not via button
            if not update.callback_query:
                self.logCommand(update)
            else:
                self.logChoice(update, "Search missing media")

            txtMissingMedia = (
                "Searching for all missing movies. "
                "If you have more missing movies, "
                "they are all being searched at the moment as well.\n\n"
            )

            if self.radarr_enabled:
                respRadarr = \
                    self.radarrNode.send_command("MissingMoviesSearch")
                txtMissingMedia += (
                    f"Radarr message: {respRadarr.message}\n"
                    f"Radarr priority: {respRadarr.priority}\n\n"
                )
            else:
                txtMissingMedia += (
                    "Radarr message: Radarr disabled\n"
                    "Radarr priority: -\n\n"
                )

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                txtMissingMedia
            )

    def selectRootFolder(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid, 3: Quality
            # 4:Language/Availability

            if data[1] == "serie":
                if self.sonarr_enabled:
                    root_paths = self.sonarrNode.root_folder()
                    languages = self.sonarrNode.language_profile()

                    for lang in languages:
                        if lang.id == int(data[4]):
                            self.logChoice(update, lang.name)
            else:
                if self.radarr_enabled:
                    root_paths = self.radarrNode.root_folder()

                    availability = str(self.availability[int(data[4])])
                    self.logChoice(update, availability)

            if root_paths:

                keyboard = []
                freespace = 0

                for root_path in root_paths:

                    # if check for largest and not an Admin
                    if self.path_largest_space and not self.isAdmin(update):

                        # If stored space value is less the current space
                        if freespace < root_path.freeSpace:

                            # store the larger valve and clear "keyboard"
                            freespace = root_path.freeSpace
                            keyboard = []

                        else:
                            continue

                    callbackdata = (
                        f"selectdownload:{data[1]}:{data[2]}:"
                        f"{data[3]}:{data[4]}:{root_path.id}"
                    )

                    keyboard.append([InlineKeyboardButton(
                        f"{root_path.path} "
                        f"({root_path.freeSpace // (1024**3)} GB Free)",
                        callback_data=callbackdata)]
                    )

                    txtKeyboard = "Please select download location:"

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    query,
                    txtKeyboard,
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"No paths were found, Please set them up in "
                    f"Sonarr and radarr, "
                    f"{update.effective_user.first_name}."
                )

    def selectLanguage(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid, 3: Quality

            if data[1] == "serie":
                if self.sonarr_enabled:
                    languages = self.sonarrNode.language_profile()
                    profiles = self.sonarrNode.quality_profile()

                    for p in profiles:
                        if p.id == int(data[3]):
                            self.logChoice(update, p.name)
            else:
                if self.radarr_enabled:
                    pass

            if languages:

                keyboard = []

                for language in languages:

                    callbackdata = (
                        f"selectRootFolder:{data[1]}:{data[2]}:"
                        f"{data[3]}:{language.id}"
                    )

                    keyboard.append([InlineKeyboardButton(
                        f"{language.name}",
                        callback_data=callbackdata)]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    query,
                    "Please select language profile:",
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"No language profiles were found, Please set them up in "
                    f"Sonarr, "
                    f"{update.effective_user.first_name}."
                )

    def selectAvailability(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid, 3: Quality

            if data[1] == "serie":
                if self.sonarr_enabled:
                    return
            else:
                if self.radarr_enabled:
                    profiles = self.sonarrNode.quality_profile()

                    for p in profiles:
                        if p.id == int(data[3]):
                            self.logChoice(update, p.name)

            if self.availability:

                keyboard = []

                for count, availability in enumerate(self.availability):

                    callbackdata = (
                        f"selectRootFolder:{data[1]}:{data[2]}:"
                        f"{data[3]}:{count}"
                    )

                    keyboard.append([InlineKeyboardButton(
                        f"{availability}",
                        callback_data=callbackdata)]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    query,
                    "Please select availability:",
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"No availability was found, Please set them up in "
                    f"INIT, "
                    f"{update.effective_user.first_name}."
                )

    def showMetaInfo(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):
            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:title

            args = []
            args.append(data[2])
            self.findMedia(update, context, query, data[1], args)

    def showMediaInfo(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaID

            if data[1] == "serie":
                if self.sonarr_enabled:
                    media = self.sonarrNode.get_series(series_id=int(data[2]))
                    tagLabels_to_keep = self.tags_to_keep_sonarr
            else:
                if self.radarr_enabled:
                    media = self.radarrNode.get_movie(movie_id=int(data[2]))
                    tagLabels_to_keep = self.tags_to_keep_radarr

            self.logChoice(update, f"{media.title} ({media.year})")

            self.outputMediaInfo(update, context, data[1], media)

            keyboard = []

            # Get ID's for keeping movies anyway
            tagsIDs_to_keep = self.getIDsforTagLabels(
                data[1], tagLabels_to_keep)

            # IF in the media there are not "KEEP" tags,
            # then show delete button

            if not set(media.tagsIds) & set(tagsIDs_to_keep) or \
                    self.isAdmin(update):

                # Show button if:
                #   - If "only users can delete own media" is enabled
                #           and it is their own media
                #   - If "only users can delete own media" is disabled
                #   -  User is an Admin

                if (self.users_can_only_delete_own_media and
                        self.getUsertagID(update, data[1]) in media.tagsIds) \
                            or not self.users_can_only_delete_own_media or \
                        self.isAdmin(update):

                    callbackdata = (f"deletemedia:{data[1]}:{data[2]}")

                    if self.isAdmin(update) or \
                            self.users_permanent_delete_media:
                        callbackdata += ":True"
                    else:
                        callbackdata += ":False"

                    keyboard.append([InlineKeyboardButton(
                        f"Delete '{media.title} ({media.year})'",
                        callback_data=callbackdata)]
                    )

            tagLabels_to_extend = self.tags_to_extend_radarr
            tagIDs_To_Extend = self.getIDsforTagLabels(
                data[1], tagLabels_to_extend)

            if data[1] == "movie" and \
                    not set(media.tagsIds) & set(tagIDs_To_Extend):
                callbackdata = (f"extendperiod:{data[1]}:{data[2]}")

                keyboard.append([InlineKeyboardButton(
                    f"Extend '{media.title} ({media.year})' "
                    f"with {self.extend_by_days} days",
                    callback_data=callbackdata)]
                )

            tagLabels_to_keep = self.tags_to_keep_radarr
            tagIDs_To_Keep = self.getIDsforTagLabels(
                data[1], tagLabels_to_keep)

            if not set(media.tagsIds) & set(tagIDs_To_Keep) \
                    and self.isAdmin(update):
                callbackdata = (f"keepmedia:{data[1]}:{data[2]}")

                keyboard.append([InlineKeyboardButton(
                    f"Keep '{media.title} ({media.year})'",
                    callback_data=callbackdata)]
                )

            if data[1] == "movie" and not media.hasFile:
                callbackdata = (f"searchmedia:{data[1]}")

                keyboard.append([InlineKeyboardButton(
                    f"Search '{media.title} ({media.year})'",
                    callback_data=callbackdata)]
                )

            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    query,
                    "Actions:",
                    reply_markup,
                    False
                )

    def deleteQueueItem(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:queueID

            if data[1] == "episode":
                if self.sonarr_enabled:
                    self.sonarr_node.delete_queue(int(data[2]))
            else:
                if self.radarr_enabled:
                    self.radarr_node.delete_queue(int(data[2]))

            self.notifyDeleteQueueItem(update, context, data[1], data[2])

    def deleteMedia(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaID, 3:delete_files

            if data[1] == "serie":

                # Get ID's for exclusion list movies
                tagLabels_for_exclusion = \
                    self.sonarr_tags_exclusion
                tagsIDs_for_exclusion = self.getIDsforTagLabels(
                    data[1], tagLabels_for_exclusion)

                media = self.sonarrNode.get_series(series_id=data[2])

                if self.sonarr_enabled:
                    self.sonarrNode.delete_series(
                        series_id=int(data[2]),
                        tvdb_id=None,
                        addImportListExclusion=True if
                        set(media.tagsIds) &
                        set(tagsIDs_for_exclusion)
                        else False,
                        deleteFiles=data[3]
                    )
            else:

                # Get ID's for exclusion list movies
                tagLabels_for_exclusion = \
                    self.radarr_tags_exclusion
                tagsIDs_for_exclusion = self.getIDsforTagLabels(
                    data[1], tagLabels_for_exclusion)

                media = self.radarrNode.get_movie(movie_id=data[2])

                if self.radarr_enabled:
                    self.radarrNode.delete_movie(
                        movie_id=int(data[2]),
                        tmdb_id=None,
                        imdb_id=None,
                        addImportExclusion=True if
                        set(media.tagsIds) &
                        set(tagsIDs_for_exclusion)
                        else False,
                        deleteFiles=data[3]
                    )

            self.logChoice(update, f"Delete {data[1]}")

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                f"The {data[1]} has been deleted."
            )

    def downloadMedia(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker,
            # 1:type of media,
            # 2:mediaid
            # 3:qualityid,
            # 4:Langausge Profile / Availability
            # 5:rootfolder
            # 6:Download which seasons?

            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                "Please be patient..."
            )

            if data[1] == "serie":
                if self.sonarr_enabled:

                    self.logChoice(update, data[6])

                    media = self.sonarrNode.get_series(tvdb_id=data[2])

                    self.pixlovarrdata["stitle"] = media.title
                    self.saveconfig(
                        self.pixlovarr_data_file, self.pixlovarrdata)

                    # get usertag from server and to movie
                    usertagID = self.getUsertagID(update, data[1])
                    if not usertagID:
                        tagName = self.createTagName(
                            update.effective_user.first_name,
                            update.effective_user.id
                        )

                        newTag = self.sonarrNode.create_tag(tagName)
                        usertagID = newTag.id

                    tags = []
                    tags.append(usertagID)

                    media.add(
                        int(data[5]),
                        int(data[3]),
                        int(data[4]),
                        data[6],
                        self.sonarr_season_folder,
                        True,
                        False,
                        "standard",
                        tags
                    )

                    self.notifyDownload(
                        update, context, data[1], media.title, media.year)

            else:
                if self.radarr_enabled:
                    media = self.radarrNode.get_movie(imdb_id=data[2])

                    self.pixlovarrdata["mtitle"] = media.title
                    self.saveconfig(
                        self.pixlovarr_data_file, self.pixlovarrdata)

                    # get usertag from server and to movie
                    usertagID = self.getUsertagID(update, data[1])
                    if not usertagID:
                        tagName = self.createTagName(
                            update.effective_user.first_name,
                            update.effective_user.id
                        )

                        newTag = self.radarrNode.create_tag(tagName)
                        usertagID = newTag.id

                    tags = []
                    tags.append(usertagID)

                    availability = str(self.availability[int(data[4])])

                    media.add(
                        int(data[5]),
                        int(data[3]),
                        True,
                        True,
                        availability,
                        tags
                    )

                    self.notifyDownload(
                        update, context, data[1], media.title, media.year)

    def showDownloadSummary(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid

            if data[1] == "serie":
                if self.sonarr_enabled:
                    profiles = self.sonarrNode.quality_profile()
                    callbackdata = f"selectlang:{data[1]}:{data[2]}"
                    media = self.sonarrNode.get_series(tvdb_id=data[2])

            else:
                if self.radarr_enabled:
                    profiles = self.radarrNode.quality_profile()
                    callbackdata = f"selectAvailability:{data[1]}:{data[2]}"
                    media = self.radarrNode.get_movie(imdb_id=data[2])

            self.logChoice(update, f"{media.title} ({media.year})")

            self.outputMediaInfo(update, context, data[1], media)

            keyboard = []
            row = []
            num_columns = 2

            if profiles:

                profiles.sort(key=self.sortOnNameDict)

                for count, p in enumerate(profiles):
                    if data[1] == "serie":
                        row.append(InlineKeyboardButton(
                            f"{p.name}",
                            callback_data=f"{callbackdata}:{p.id}")
                        )
                    else:
                        row.append(InlineKeyboardButton(
                            f"{p.name}",
                            callback_data=f"{callbackdata}:{p.id}")
                        )

                    if (count+1) % num_columns == 0 or \
                            count == len(profiles)-1:
                        keyboard.append(row)
                        row = []

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"No profiles were found, Please set them up in"
                    f"Sonarr and Radarr, "
                    f"{update.effective_user.first_name}."
                )

                return

            reply_markup = InlineKeyboardMarkup(keyboard)

            self.replytext(
                query,
                "Please select media quality:",
                reply_markup,
                False
            )

    def selectDownload(self, update, context):
        if not self.isBlocked(update) and self.isGranted(update):
            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid, 3: Quality
            # 4: Langauge Profile, 5: RootFolder

            callbackdata = (
                f"downloadmedia:{data[1]}:{data[2]}:{data[3]}:"
                f"{data[4]}:{data[5]}"
            )

            if data[1] == "serie":
                if self.sonarr_enabled:

                    root_paths = self.sonarrNode.root_folder()
                    for r in root_paths:
                        if r.id == int(data[5]):
                            self.logChoice(update, r.path)

                    keyboard = [
                        [InlineKeyboardButton(
                            "Download All seasons",
                            callback_data=f"{callbackdata}:all")],
                        [InlineKeyboardButton(
                            "Download Future seasons",
                            callback_data=f"{callbackdata}:future")],
                        [InlineKeyboardButton(
                            "Download missing seasons",
                            callback_data=f"{callbackdata}:missing")],
                        [InlineKeyboardButton(
                            "Download existing seasons",
                            callback_data=f"{callbackdata}:existing")],
                        [InlineKeyboardButton(
                            "Download only pilot episode",
                            callback_data=f"{callbackdata}:pilot")],
                        [InlineKeyboardButton(
                            "Download first season",
                            callback_data=f"{callbackdata}:firstSeason")],
                        [InlineKeyboardButton(
                            "Download lastest season",
                            callback_data=f"{callbackdata}:latestSeason")],
                        [InlineKeyboardButton(
                            "Download no seasons",
                            callback_data=f"{callbackdata}:none")]
                    ]
            else:
                if self.radarr_enabled:

                    root_paths = self.radarrNode.root_folder()
                    for r in root_paths:
                        if r.id == int(data[5]):
                            self.logChoice(update, r.path)

                    media = self.radarrNode.get_movie(imdb_id=data[2])
                    keyboard = [[InlineKeyboardButton(
                        f"Download '{media.title} ({media.year})'",
                        callback_data=f"{callbackdata}:False")]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            self.replytext(
                query,
                "Please confirm:",
                reply_markup,
                False
            )

    def findMedia(self, update, context, query, typeOfMedia, args):

        ranking = ""
        if len(args) > 0:
            ranking = args[0]
            if re.match("^[Tt]\\d+$", ranking):
                context.args.pop(0)

        if ' '.join(args):

            topAmount = self.getTopAmount(update, context, ranking)

            searchQuery = ' '.join(args)
            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                f"Searching for {typeOfMedia}s..."
            )

            if typeOfMedia == "serie":
                if self.sonarr_enabled:
                    media = self.sonarrNode.search_series(term=searchQuery)
            else:
                if self.radarr_enabled:
                    media = self.radarrNode.search_movies(term=searchQuery)

            if media:
                keyboard = []
                keyboardPresentMedia = []

                maxResults = topAmount - 1

                for m in media:
                    if m.id:  # Media found in database

                        callbackdata = f"showMediaInfo:{typeOfMedia}:{m.id}"

                        keyboardPresentMedia.append([InlineKeyboardButton(
                            f"{m.title} ({m.year})",
                            callback_data=callbackdata)]
                        )

                        maxResults += 1

                        continue    # media is already in collection

                    if typeOfMedia == "serie":
                        callbackdata = (
                            f"showdlsummary:{typeOfMedia}:{m.tvdbId}")
                        if not m.tvdbId:

                            maxResults += 1

                            continue  # serie doesn't have ID
                    else:
                        callbackdata = (
                            f"showdlsummary:{typeOfMedia}:{m.imdbId}")
                        if not m.imdbId:

                            maxResults += 1

                            continue  # movie doesn't have ID

                    keyboard.append([InlineKeyboardButton(
                        f"{m.title} ({m.year})",
                        callback_data=callbackdata)]
                    )

                    if media.index(m) == maxResults:
                        break

                if query is not None:
                    message = query
                else:
                    message = update

                if keyboardPresentMedia:
                    reply_markup_PresentMedia = InlineKeyboardMarkup(
                        keyboardPresentMedia)

                    self.replytext(
                        message,
                        f"We found these {typeOfMedia}s in your catalog:",
                        reply_markup_PresentMedia,
                        False
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                self.replytext(
                    message,
                    "We found the following media for you:",
                    reply_markup,
                    False
                )

            else:
                self.sendmessage(
                    update.effective_chat.id,
                    context,
                    update.effective_user.first_name,
                    f"The specified query has no results, "
                    f"{update.effective_user.first_name}."
                )

        else:
            self.sendmessage(
                update.effective_chat.id,
                context,
                update.effective_user.first_name,
                f"Please specify a query, "
                f"{update.effective_user.first_name}."
            )

    def grantMember(self, update, context):
        if self.isAdmin(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:source of person, 2:userid

            if (data[2] in self.signups or data[2] in self.blockedusers):

                if data[1] == "new":
                    self.members[data[2]] = self.signups[data[2]]
                    self.signups.pop(data[2], None)

                if data[1] == "blocked":
                    self.members[data[2]] = self.blockedusers[data[2]]
                    self.blockedusers.pop(data[2], None)

                self.saveconfig(self.pixlovarr_members_file, self.members)
                self.saveconfig(self.pixlovarr_signups_file, self.signups)
                self.saveconfig(
                    self.pixlovarr_blocked_file, self.blockedusers)

                logging.info(
                    f"{self.members[data[2]]['fname']} - "
                    f"{self.members[data[2]]['id']} was added"
                    f" to the memberlist."
                )

                self.sendmessage(
                    self.members[data[2]]['id'],
                    context,
                    self.members[data[2]]['fname'],
                    f"Hi {self.members[data[2]]['fname']}, "
                    f"access was granted. For your new commands, "
                    f"please use /help."
                )

                self.sendmessage(
                    self.admin_user_id,
                    context,
                    "Admin",
                    f"Hi admin, "
                    f"{self.members[data[2]]['fname']} "
                    f"was granted access. Message has been sent."
                )

    def blockMember(self, update, context):
        if self.isAdmin(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:source of person, 2:userid

            if (data[2] in self.signups or data[2] in self.members):

                if data[1] == "new":
                    self.blockedusers[data[2]] = self.signups[data[2]]
                    self.signups.pop(data[2], None)

                if data[1] == "allowed":
                    self.blockedusers[data[2]] = self.members[data[2]]
                    self.members.pop(data[2], None)

                self.saveconfig(self.pixlovarr_members_file, self.members)
                self.saveconfig(self.pixlovarr_signups_file, self.signups)
                self.saveconfig(
                    self.pixlovarr_blocked_file, self.blockedusers)

                logging.info(
                    f"Member {self.blockedusers[data[2]]['fname']} - "
                    f"{self.blockedusers[data[2]]['id']} was blocked."
                )

                self.sendmessage(
                    self.blockedusers[data[2]]['id'],
                    context,
                    self.blockedusers[data[2]]['fname'],
                    f"Hi {self.blockedusers[data[2]]['fname']}, "
                    f"access was blocked."
                )

                self.sendmessage(
                    self.admin_user_id,
                    context,
                    "Admin",
                    f"Hi admin, "
                    f"{self.blockedusers[data[2]]['fname']} was blocked."
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

        self.showMovieCalendar_handler = CommandHandler('mc', self.getCalendar)
        self.dispatcher.add_handler(self.showMovieCalendar_handler)

        self.showSerieCalendar_handler = CommandHandler('sc', self.getCalendar)
        self.dispatcher.add_handler(self.showSerieCalendar_handler)

        self.meta_handler = CommandHandler('rm', self.showMeta)
        self.dispatcher.add_handler(self.meta_handler)

        self.meta_handler = CommandHandler('rs', self.showMeta)
        self.dispatcher.add_handler(self.meta_handler)

        self.listMyMedia_handler = CommandHandler('mm', self.listMyMedia)
        self.dispatcher.add_handler(self.listMyMedia_handler)

        self.listMyMedia_handler = CommandHandler('ms', self.listMyMedia)
        self.dispatcher.add_handler(self.listMyMedia_handler)

        self.listNewMedia_handler = CommandHandler('nm', self.listNewMedia)
        self.dispatcher.add_handler(self.listNewMedia_handler)

        self.listNewMedia_handler = CommandHandler('ns', self.listNewMedia)
        self.dispatcher.add_handler(self.listNewMedia_handler)

        self.servicestatus_handler = CommandHandler('sts', self.serviceStatus)
        self.dispatcher.add_handler(self.servicestatus_handler)

        self.buymeacoffee_handler = CommandHandler('coffee', self.buymeacoffee)
        self.dispatcher.add_handler(self.buymeacoffee_handler)

        self.performRSS_handler = CommandHandler('rss', self.performRSS)
        self.dispatcher.add_handler(self.performRSS_handler)

        self.searchMissingMedia_handler = \
            CommandHandler('smm', self.searchMissingMedia)
        self.dispatcher.add_handler(self.searchMissingMedia_handler)

# Keyboard Handlers

        kbgrant_handler = CallbackQueryHandler(
            self.grantMember, pattern='^grant:')
        self.dispatcher.add_handler(kbgrant_handler)

        kbblock_handler = CallbackQueryHandler(
            self.blockMember, pattern='^block:')
        self.dispatcher.add_handler(kbblock_handler)

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

        kbshowMediaInfo_handler = CallbackQueryHandler(
            self.showMediaInfo, pattern='^showMediaInfo:')
        self.dispatcher.add_handler(kbshowMediaInfo_handler)

        kbshowMetaInfo_handler = CallbackQueryHandler(
            self.showMetaInfo, pattern='^showMetaInfo:')
        self.dispatcher.add_handler(kbshowMetaInfo_handler)

        kbselectRootFolder_handler = CallbackQueryHandler(
            self.selectRootFolder, pattern='^selectRootFolder:')
        self.dispatcher.add_handler(kbselectRootFolder_handler)

        kbselectSearchMissingMedia_handler = CallbackQueryHandler(
            self.searchMissingMedia, pattern='^searchmedia:')
        self.dispatcher.add_handler(kbselectSearchMissingMedia_handler)

        kbselectExtendPeriodMedia_handler = CallbackQueryHandler(
            self.extendPeriodMedia, pattern='^extendperiod:')
        self.dispatcher.add_handler(kbselectExtendPeriodMedia_handler)

        kbselectKeepMedia_handler = CallbackQueryHandler(
            self.keepMedia, pattern='^keepmedia:')
        self.dispatcher.add_handler(kbselectKeepMedia_handler)

        kbselectLanguage_handler = CallbackQueryHandler(
            self.selectLanguage, pattern='^selectlang:')
        self.dispatcher.add_handler(kbselectLanguage_handler)

        kbselectAvailability_handler = CallbackQueryHandler(
            self.selectAvailability, pattern='^selectAvailability:')
        self.dispatcher.add_handler(kbselectAvailability_handler)

# Admin Handlders

        self.showsignups_handler = CommandHandler('new', self.showSignups)
        self.dispatcher.add_handler(self.showsignups_handler)

        self.showallowed_handler = CommandHandler('am', self.showAllowed)
        self.dispatcher.add_handler(self.showallowed_handler)

        self.showblocked_handler = CommandHandler('bm', self.showBlocked)
        self.dispatcher.add_handler(self.showblocked_handler)

        self.cmdhistory_handler = CommandHandler('ch', self.showCmdHistory)
        self.dispatcher.add_handler(self.cmdhistory_handler)

        self.listtags_handler = CommandHandler('lt', self.listtags)
        self.dispatcher.add_handler(self.listtags_handler)

        self.opensignup_handler = CommandHandler('open', self.opensignup)
        self.dispatcher.add_handler(self.opensignup_handler)

        self.closesignup_handler = CommandHandler('close', self.closesignup)
        self.dispatcher.add_handler(self.closesignup_handler)

        self.unknown_handler = MessageHandler(Filters.command, self.unknown)
        self.dispatcher.add_handler(self.unknown_handler)

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
