# Name: Pixlovarr Prune
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-11-15 21:38:51
# update: 2021-12-16 16:28:51

import logging
import configparser
import sys
import shutil
import os
import glob

from datetime import datetime, timedelta
from arrapi import RadarrAPI
from chump import Application


class RLP():

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

                # COMMON
                self.delete_files = True if (
                    self.config['COMMON']
                    ['PERMANENT_DELETE_MEDIA'] == "ON") else False

                # RADARR
                self.radarr_enabled = True if (
                    self.config['RADARR']['ENABLED'] == "ON") else False
                self.radarr_url = self.config['RADARR']['URL']
                self.radarr_token = self.config['RADARR']['TOKEN']
                self.radarr_tags_exclusion = list(
                    self.config['RADARR']
                    ['AUTO_ADD_EXCLUSION'].split(","))
                self.tags_to_keep = list(
                    self.config['RADARR']
                    ['TAGS_KEEP_MOVIES_ANYWAY'].split(",")
                )
                self.tags_to_extend = list(
                    self.config['RADARR']
                    ['TAGS_TO_EXTEND_PERIOD_BEFORE_REMOVAL'].split(","))

                # PRUNE
                self.tags_to_remove = list(
                    self.config['PRUNE']
                    ['TAGS_TO_MONITOR_FOR_REMOVAL_MOVIES'].split(",")
                )
                self.remove_after_days = int(
                    self.config['PRUNE']['REMOVE_MOVIES_AFTER_DAYS'])
                self.warn_days_infront = int(
                    self.config['PRUNE']['WARN_DAYS_INFRONT'])
                self.dry_run = True if (
                    self.config['PRUNE']['DRY_RUN'] == "ON") else False
                self.enabled_run = True if (
                    self.config['PRUNE']['ENABLED'] == "ON") else False
                self.show_kept_message = True if (
                    self.config['PRUNE']
                    ['SHOW_KEPT_MESSAGE'] == "ON") else False
                self.extend_by_days = int(
                    self.config['PRUNE']['EXTEND_PERIOD_BY_DAYS'])

                # PUSHOVER
                self.pushover_enabled = True if (
                    self.config['PUSHOVER']['ENABLED'] == "ON") else False
                self.pushover_user_key = self.config['PUSHOVER']['USER_KEY']
                self.pushover_token_api = self.config['PUSHOVER']['TOKEN_API']
                self.pushover_sound = self.config['PUSHOVER']['SOUND']

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

            shutil.copyfile('./app/pixlovarr.ini.example',
                            './config/pixlovarr.ini.example')
            sys.exit()

    def sortOnTitle(self, e):
        return e.sortTitle

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

    def evalMovie(self, movie, labels):

        # Get ID's for keeping movies anyway
        tagLabels_to_keep = self.tags_to_keep
        tagsIDs_to_keep = self.getIDsforTagLabels(
            "movie", tagLabels_to_keep)

        # check if ONE of the "KEEP" tags is
        # in the set of "MOVIE TAGS"
        if set(movie.tagsIds) & set(tagsIDs_to_keep) and \
                self.show_kept_message:

            logging.info(
                f"Prune - KEEPING - {movie.title} ({movie.year}). Skipping."
            )
        else:

            # Get ID's for removal movies
            tagLabels_to_remove = self.tags_to_remove
            tagsIDs_to_remove = self.getIDsforTagLabels(
                "movie", tagLabels_to_remove)

            # Get ID's for extended removal
            tagLabels_to_extend = self.tags_to_extend
            tagsIDs_to_extend = self.getIDsforTagLabels(
                "movie", tagLabels_to_extend)

            # Warning if no valid tags was found for removal movies
            if not tagsIDs_to_remove:
                logging.warning(
                    "No valid tags found from the INI file to indentify "
                    "movies. No movies will be removed in this run. "
                    "TIP: Add existing tags from your RADARR server."
                )

            # check if ONE of the "REMOVAL" tags is
            #  in the set of "MOVIE TAGS"
            if set(movie.tagsIds) & set(tagsIDs_to_remove):

                movieDownloadDate = None
                fileList = glob.glob(movie.path + "/*")
                for file in fileList:
                    if file.lower().endswith(('.mp4', '.avi', '.mkv')):
                        # Get modfified date on movie.nfo,
                        # Which is the downloaddate
                        # movieNfo = os.path.join(movie.path, "movie.nfo")
                        modifieddate = os.stat(file).st_mtime
                        movieDownloadDate = \
                            datetime.fromtimestamp(modifieddate)
                        break

                if not fileList or not movieDownloadDate:
                    # If FIle is not found, the movie is missing
                    # add will be skipped These are probably
                    # movies in the future
                    logging.info(
                        f"Prune - MISSING - "
                        f"{movie.title} ({movie.year})"
                        f" is not downloaded yet. Skipping."
                    )
                    return False

                now = datetime.now()
                extend_period = self.extend_by_days \
                    if (set(movie.tagsIds) & set(tagsIDs_to_extend)) else 0

                # check if there needs to be warn "DAYS" infront of removal
                # 1. Are we still within the period before removel?
                # 2. Is "NOW" less than "warning days" before removal?
                # 3. is "NOW" more then "warning days - 1" before removal
                #               (warn only 1 day)
                if (
                    timedelta(days=self.remove_after_days + extend_period) >
                    now - movieDownloadDate and
                    movieDownloadDate +
                    timedelta(days=self.remove_after_days + extend_period) -
                    now <= timedelta(days=self.warn_days_infront) and
                    movieDownloadDate +
                    timedelta(days=self.remove_after_days + extend_period) -
                    now > timedelta(days=self.warn_days_infront) -
                    timedelta(days=1)
                ):

                    self.timeLeft = (
                        movieDownloadDate +
                        timedelta(
                            days=self.remove_after_days +
                            extend_period) - now)

                    if self.pushover_enabled:
                        self.message = self.userPushover.send_message(
                            message=f"Prune - {movie.title} ({movie.year}) "
                            f"will be removed from server in "
                            f"{'h'.join(str(self.timeLeft).split(':')[:2])}",
                            sound=self.pushover_sound
                        )

                    logging.info(
                        f"Prune - WILL BE REMOVED - "
                        f"{movie.title} ({movie.year})"
                        f" in {'h'.join(str(self.timeLeft).split(':')[:2])}"
                        f" - {movieDownloadDate}"
                    )

                # Check is movie is older than "days set in INI"
                if (
                    now - movieDownloadDate >=
                        timedelta(
                            days=self.remove_after_days + extend_period)
                ):

                    if not self.dry_run:
                        if self.radarr_enabled:

                            # Get ID's for exclusion list movies
                            tagLabels_for_exclusion = \
                                self.radarr_tags_exclusion
                            tagsIDs_for_exclusion = self.getIDsforTagLabels(
                                "movie", tagLabels_for_exclusion)

                            self.radarrNode.delete_movie(
                                movie_id=movie.id,
                                tmdb_id=None,
                                imdb_id=None,
                                addImportExclusion=True if
                                set(movie.tagsIds) &
                                set(tagsIDs_for_exclusion)
                                else False,
                                deleteFiles=self.delete_files
                            )

                    if self.delete_files:
                        self.txtFilesDelete = \
                            ", files deleted."
                    else:
                        self.txtFilesDelete = \
                            ", files preserved."

                    if self.pushover_enabled:
                        self.message = self.userPushover.send_message(
                            message=f"{movie.title} ({movie.year}) "
                            f"Prune - REMOVED - {movie.title} ({movie.year})"
                            f"{self.txtFilesDelete}"
                            f" - {movieDownloadDate}",
                            sound=self.pushover_sound
                        )

                    logging.info(
                        f"Prune - REMOVED - {movie.title} ({movie.year})"
                        f"{self.txtFilesDelete}"
                        f" - {movieDownloadDate}"
                    )
                    return True
        return False

    def run(self):
        if not self.enabled_run:
            logging.info(
                "Prune - Library purge disabled")
            sys.exit()

        if self.dry_run:
            logging.info(
                "*****************************************************")
            logging.info(
                "**** DRY RUN, NOTHING WILL BE DELETED OR REMOVED ****")
            logging.info(
                "*****************************************************")

        # Connect to Radarr
        if self.radarr_enabled:
            self.radarrNode = RadarrAPI(
                self.radarr_url, self.radarr_token)

        # Convert tags to a dictionary
        tagIDsByLabels = {}
        for tag in self.radarrNode.all_tags():
            # Add tag to lookup by it's name
            tagIDsByLabels[tag.label] = tag.id

        if not tagIDsByLabels:
            logging.info(
                "Prune - No tags found on Radarr server. "
                "Exiting script."
            )

            sys.exit()

        # Setting for PushOver
        if self.pushover_enabled:
            self.appPushover = Application(self.pushover_token_api)
            self.userPushover = \
                self.appPushover.get_user(self.pushover_user_key)

        # Get all movies from the server.
        if self.radarr_enabled:
            media = self.radarrNode.all_movies()

        # Make sure the library is not empty.
        numDeleted = 0
        if media:
            media.sort(key=self.sortOnTitle)  # Sort the list on Title
            for movie in media:
                if self.evalMovie(movie, tagIDsByLabels):
                    numDeleted += 1

        if numDeleted > 0:
            if self.pushover_enabled:
                self.message = self.userPushover.send_message(
                    message=(
                        f"Prune - There were {numDeleted} movies removed from "
                        "the server"
                    ),
                    sound=self.pushover_sound
                )

            logging.info(
                f"Prune - There were {numDeleted} movies removed from "
                f"the server"
            )
        else:
            if self.pushover_enabled:
                self.message = self.userPushover.send_message(
                    message="Prune - No movies were removed from "
                    "the server",
                    sound=self.pushover_sound
                )

            logging.info(
                "Prune - No movies were removed from the server"
            )


if __name__ == '__main__':

    rlp = RLP()
    rlp.run()
    rlp = None
