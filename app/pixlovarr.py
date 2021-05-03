# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 2021-05-02 10:11:33

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters
)
import logging
import json
import configparser
import shutil
import sys
from pycliarr.api import (
    RadarrCli,
    RadarrMovieItem
)
from pycliarr.api import (
    SonarrCli,
    SonarrSerieItem
)
from pycliarr.api.exceptions import CliServerError


class Pixlovarr():

    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)

        self.config_file = "./config/pixlovarr.ini"

        try:
            with open(self.config_file, "r") as f:
                f.close()
            try:
                self.config = configparser.ConfigParser()
                self.config.read(self.config_file)
                self.bot_token = self.config['COMMON']['BOT_TOKEN']
                self.admin_user_id = self.config['COMMON']['ADMIN_USER_ID']
                self.sonarr_enabled = True if (
                    self.config['SONARR']['ENABLED'] == "ON") else False
                self.sonarr_url = self.config['SONARR']['URL']
                self.sonarr_token = self.config['SONARR']['TOKEN']
                self.radarr_enabled = True if (
                    self.config['RADARR']['ENABLED'] == "ON") else False
                self.radarr_url = self.config['RADARR']['URL']
                self.radarr_token = self.config['RADARR']['TOKEN']

                if self.sonarr_enabled:
                    self.sonarr_node = SonarrCli(
                        self.sonarr_url, self.sonarr_token
                    )

                if self.radarr_enabled:
                    self.radarr_node = RadarrCli(
                        self.radarr_url, self.radarr_token
                    )

                self.pixlovarr_signups_file = (
                    "./config/pixlovarr_signups.json")
                self.pixlovarr_members_file = (
                    "./config/pixlovarr_members.json")
                self.pixlovarr_rejected_file = (
                    "./config/pixlovarr_rejected.json")

                self.signups = self.loaddata(self.pixlovarr_signups_file)
                self.members = self.loaddata(self.pixlovarr_members_file)
                self.rejected = self.loaddata(self.pixlovarr_rejected_file)

            except KeyError:
                logging.error(
                    "Can't get keys from INI file. "
                    "Please check for mistakes."
                )

                sys.exit()

        except IOError or FileNotFoundError:
            logging.error(f"Can't open file {self.config_file}, "
                          f"creating example INI file.")

            shutil.copyfile('./app/pixlovarr.ini.example',
                            './config/pixlovarr.ini.example')
            sys.exit()

    def isAdmin(self, update, context, verbose):
        if str(update.effective_chat.id) == self.admin_user_id:
            return True
        else:
            if verbose:

                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"{update.effective_chat.first_name}, "
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

# Default Commands

    def start(self, update, context):
        if not self.isRejected(update):
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

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /start."
            )

    def signup(self, update, context):
        if not self.isRejected(update):
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
                            f"Thank you {update.effective_chat.first_name}, "
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

                    logging.info(
                        f"{update.effective_user.first_name} - "
                        f"{update.effective_user.id} "
                        f"issued /signup."
                    )

                else:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=(
                            f"Please be patient "
                            f"{update.effective_chat.first_name}, "
                            f"we get you hooked up as soon as possible."
                        )
                    )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"No need to sign up twice, "
                        f"{update.effective_chat.first_name}"
                    )
                )

    def help(self, update, context):
        if not self.isRejected(update):
            helpText = (
                "-- Commands --\n"
                "/start - Start this bot\n"
                "/help - Show this text\n"
                "/signup - Request access\n"
                "/userid - Request your userid\n"
            )

            if self.isGranted(update):
                helpText = helpText + (
                    "/series - Get all TV shows\n"
                    "/movies - Get all movies\n"
                    "/ds <keyword> - Download serie\n"
                    "/dm <keyword> - Download movie\n"
                )

            if self.isAdmin(update, context, False):
                helpText = helpText + (
                    "\n-- Admin commands --\n"
                    "/new - Show all new signups\n"
                    "/allowed - Show all allowed members\n"
                    "/denied - Show all denied members\n"
                )

            context.bot.send_message(
                chat_id=update.effective_chat.id, text=helpText)

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /help."
            )

    def userid(self, update, context):
        if not self.isRejected(update):

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"Hi {update.effective_chat.first_name}, "
                    f"your userid is {update.effective_user.id}."
                )
            )

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /userid."
            )

# Member Commands

    def series(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.sonarr_enabled:

            serie = self.sonarr_node.get_serie()

            if type(serie) is SonarrSerieItem:

                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=serie.title)
            else:
                allSeries = ""
                for s in serie:
                    allSeries += f"{s.title} ({str(s.year)})\n"

                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=allSeries)

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /series."
            )

    def downloadSeries(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.sonarr_enabled:

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /ds."
            )

            self.findMedia(update, context, "serie", ' '.join(context.args))

    def movies(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.radarr_enabled:

            movie = self.radarr_node.get_movie()

            if type(movie) is RadarrMovieItem:

                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=movie.title)
            else:
                allMovies = ""
                for m in movie:
                    allMovies += f"{m.title} ({str(m.year)})\n"

                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=allMovies)

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /movies."
            )

    def downloadMovies(self, update, context):
        if not self.isRejected(update) and \
                self.isGranted(update) and \
                self.radarr_enabled:

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /dm."
            )

            self.findMedia(update, context, "movie", ' '.join(context.args))

# Admin Commands
    def new(self, update, context):
        if self.isAdmin(update, context, True):
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

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /new."
            )

    def allowed(self, update, context):
        if self.isAdmin(update, context, True):
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

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /allowed."
            )

    def denied(self, update, context):
        if self.isAdmin(update, context, True):
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

            logging.info(
                f"{update.effective_user.first_name} - "
                f"{update.effective_user.id} "
                f"issued /denied."
            )

    def unknown(self, update, context):
        if not self.isRejected(update):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Sorry {update.effective_chat.first_name}, "
                f"I didn't understand that command.")

            logging.info(
                f"{update.effective_chat.first_name} - "
                f"{update.effective_user.id} Unknown command given."
            )

# HandlerCallback Commands

    def downloadMedia(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid
            # 3:qualityid, 4: Download all seasons for serie

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please be patient...")

            if data[1] == "serie":
                media = self.sonarr_node.lookup_serie(tvdb_id=data[2])

                try:
                    monitored_seasons = []
                    if data[4] == "False":
                        monitored_seasons = [1]

                    self.sonarr_node.add_serie(
                        tvdb_id=data[2], quality=data[3],
                        monitored_seasons=monitored_seasons
                    )

                    self.notifyDownload(
                        update, context, data[1], media.title, media.year)

                except CliServerError:
                    pass
            else:
                media = self.radarr_node.lookup_movie(imdb_id=data[2])
                try:
                    self.radarr_node.add_movie(
                        imdb_id=data[2], quality=data[3]
                    )
                    self.notifyDownload(
                        update, context, data[1], media.title, media.year)

                except CliServerError:
                    pass

    def notifyDownload(self, update, context, typeOfMedia, title, year):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"The {typeOfMedia} '{title}({year})' "
            f"was added to the downloadserver, "
            f"{update.effective_chat.first_name}. "
            f"Thank you and till next time.")

        logging.info(
            f"{update.effective_chat.first_name} - "
            f"{update.effective_user.id} has added the "
            f"{typeOfMedia} '{title}({year})' "
            f"to the queue.")

    def showDownloadSummary(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):

            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid, 3:qualityid

            if data[1] == "serie":
                media = self.sonarr_node.lookup_serie(tvdb_id=data[2])
                callbackdata = f"download:{data[1]}:{data[2]}:{data[3]}"
                keyboard = [
                    [InlineKeyboardButton(
                        f"Download season 1 of "
                        f"'{media.title}({media.year})'",
                        callback_data=f"{callbackdata}:False")],
                    [InlineKeyboardButton(
                        f"Download only new seasons of "
                        f"'{media.title}({media.year})'",
                        callback_data=f"{callbackdata}:True")]
                ]
            else:
                media = self.radarr_node.lookup_movie(imdb_id=data[2])
                callbackdata = f"download:{data[1]}:{data[2]}:{data[3]}:False"
                keyboard = [[InlineKeyboardButton(
                    f"Download '{media.title}({media.year})'",
                    callback_data=callbackdata)]]

            if media.images:
                image = f"{media.images[0]['url']}"
            else:
                image = ("https://2.bp.blogspot.com/-s5kMEQvEAog/"
                         "T3CgSowJ7xI/AAAAAAAADHc/Hqk13CMLQQI/s400/banner.jpg")

            caption = f"{media.title}({media.year})"
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image, caption=caption
            )
            if data[1] == "serie" and media.overview:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{media.overview}"[:4096]
                )

            reply_markup = InlineKeyboardMarkup(keyboard)

            query.message.reply_text(
                f"Is this the {data[1]} you are looking for?",
                reply_markup=reply_markup
            )

    def selectQuality(self, update, context):
        if not self.isRejected(update) and self.isGranted(update):
            query = update.callback_query
            query.answer()
            data = query.data.split(":")
            # 0:marker, 1:type of media, 2:mediaid

            if data[1] == "serie":
                profiles = self.sonarr_node.get_quality_profiles()
                callbackdata = f"showdlsummary:{data[1]}:{data[2]}"
            else:
                profiles = self.radarr_node.get_quality_profiles()
                callbackdata = f"showdlsummary:{data[1]}:{data[2]}"

            keyboard = []

            if profiles:
                for p in profiles:
                    keyboard.append([InlineKeyboardButton(
                        f"{p['name']}",
                        callback_data=f"{callbackdata}:{p['id']}")]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                query.message.reply_text(
                    "Please select a download quality:",
                    reply_markup=reply_markup
                )

#            for p in profiles:
#                print(f"{p['name']} - {p['id']}\n")
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"No profiles were found, Please set them up in Sonarr "
                f"and Radarr {update.effective_chat.first_name}.")

    def findMedia(self, update, context, mediaType, searchQuery):

        if searchQuery:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Searching for {mediaType}s..."
            )

            logging.info(
                f"{update.effective_chat.first_name} - "
                f"{update.effective_user.id} is searching for "
                f"a {mediaType} with keywords '{searchQuery}'"
            )

            if mediaType == "serie":
                media = self.sonarr_node.lookup_serie(term=searchQuery)
            else:
                media = self.radarr_node.lookup_movie(term=searchQuery)

            if media:
                keyboard = []

                if type(media) == SonarrSerieItem or \
                        type(media) == RadarrMovieItem:
                    temp = media
                    media = []
                    media.append(temp)

                maxResults = 4

                for m in media:
                    if m.path:
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"We found that {m.title}({m.year}) is "
                            f"already in the collection.")
                        maxResults += 1
                        continue    # media is already in collection

                    if mediaType == "serie":
                        callbackdata = f"selectedmedia:{mediaType}:{m.tvdbId}"
                        if not m.tvdbId:
                            maxResults += 1
                            continue  # serie doesn't have ID
                    else:
                        callbackdata = f"selectedmedia:{mediaType}:{m.imdbId}"
                        if not m.imdbId:
                            maxResults += 1
                            continue  # movie doesn't have ID

                    keyboard.append([InlineKeyboardButton(
                        f"{m.title}({m.year})",
                        callback_data=callbackdata)]
                    )

#                    if mediaType == "serie":
#                        print(
#                            f"{m.title} - {m.year} - {m.path} - "
#                            f"{m.imdbId} - {m.tvdbId}\n")
#                    else:
#                        print(
#                            f"{m.title} - {m.year} - {m.path} - "
#                            f"{m.imdbId}\n")

                    if media.index(m) == maxResults:
                        break

                if keyboard:
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    update.message.reply_text(
                        "We found the following media for you:",
                        reply_markup=reply_markup
                    )

            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"The specified query has no results, "
                    f"{update.effective_chat.first_name}.")
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Please specify a query, "
                f"{update.effective_chat.first_name}.")

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

        self.series_handler = CommandHandler('series', self.series)
        self.dispatcher.add_handler(self.series_handler)

        self.downloadseries_handler = CommandHandler('ds', self.downloadSeries)
        self.dispatcher.add_handler(self.downloadseries_handler)

        self.movies_handler = CommandHandler('movies', self.movies)
        self.dispatcher.add_handler(self.movies_handler)

        self.downloadmovies_handler = CommandHandler('dm', self.downloadMovies)
        self.dispatcher.add_handler(self.downloadmovies_handler)

# Keyboard Handlders

        kbgrant_handler = CallbackQueryHandler(
            self.grant, pattern='^grant:')
        self.dispatcher.add_handler(kbgrant_handler)

        kbreject_handler = CallbackQueryHandler(
            self.reject, pattern='^reject:')
        self.dispatcher.add_handler(kbreject_handler)

        kbselectquality_handler = CallbackQueryHandler(
            self.selectQuality, pattern='^selectedmedia:')
        self.dispatcher.add_handler(kbselectquality_handler)

        kbshowDownloadSummary_handler = CallbackQueryHandler(
            self.showDownloadSummary, pattern='^showdlsummary:')
        self.dispatcher.add_handler(kbshowDownloadSummary_handler)

        kbdownloadMedia_handler = CallbackQueryHandler(
            self.downloadMedia, pattern='^download:')
        self.dispatcher.add_handler(kbdownloadMedia_handler)

# Admin Handlders

        self.new_handler = CommandHandler('new', self.new)
        self.dispatcher.add_handler(self.new_handler)

        self.allowed_handler = CommandHandler('allowed', self.allowed)
        self.dispatcher.add_handler(self.allowed_handler)

        self.denied_handler = CommandHandler('denied', self.denied)
        self.dispatcher.add_handler(self.denied_handler)

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
