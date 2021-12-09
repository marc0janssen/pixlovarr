# Name: Pixlovarr Prune
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-11-15 21:38:51
# update: 2021-12-09 14:20:16

import logging
import configparser
import sys
import shutil
import os
import time

from datetime import datetime, timedelta

from pycliarr.api import (
    RadarrCli,
    RadarrMovieItem
)
from chump import Application


class RLP():

    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)

        self.config_file = "./config/pixlovarr.ini"

        # Set "any movie removed" to FALSE
        self.anyMovieRemoved = False

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
                self.radarr_add_exclusion = True if (
                    self.config['RADARR']
                    ['AUTO_ADD_EXCLUSION'] == "ON") else False
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

    def evalMovie(self, movie, labels):

        # Get ID's for keeping movies anyway
        tagsIDs_to_keep = []
        for tag_to_keep in self.tags_to_keep:
            self.tagID_to_keep = labels.get(tag_to_keep)
            if self.tagID_to_keep:
                tagsIDs_to_keep.append(self.tagID_to_keep)

        # check if ONE of the "KEEP" tags is
        # in the set of "MOVIE TAGS"
        if set(movie.tags) & set(tagsIDs_to_keep) and \
                self.show_kept_message:

            logging.info(
                f"Script - KEPT - {movie.title} ({movie.year})"
            )
        else:
            # Get ID's for removal movies
            tagsIDs_to_remove = []
            for tag_to_remove in self.tags_to_remove:
                tagID_to_remove = labels.get(tag_to_remove)
                if tagID_to_remove:
                    tagsIDs_to_remove.append(tagID_to_remove)

            # Get ID's for extended removal
            tagsIDs_to_extend = []
            for tag_to_extend in self.tags_to_extend:
                tagID_to_extend = labels.get(tag_to_extend)
                if tagID_to_extend:
                    tagsIDs_to_extend.append(tagID_to_extend)

            # Warning if no valid tags was found for removal movies
            if not tagsIDs_to_remove:
                logging.warning(
                    "No valid tags found from the INI file to indentify "
                    "movies. No movies will be removed in this run. "
                    "TIP: Add existing tags from your RADARR server."
                )

            # check if ONE of the "REMOVAL" tags is
            #  in the set of "MOVIE TAGS"
            if set(movie.tags) & set(tagsIDs_to_remove):

                try:
                    movieNfo = os.path.join(movie.path, "movie.nfo")
                    ti_m = os.path.getmtime(movieNfo)
                    m_ti = time.ctime(ti_m)
                    print(f"{m_ti} - {movieNfo}")

                except IOError or FileNotFoundError:
                    logging.info(
                        f"Can't open file {movie.path}/movie.nfo"
                    )

                movieDateAdded = datetime.strptime(
                    movie.added, '%Y-%m-%dT%H:%M:%SZ'
                )

                now = datetime.now()
                extend_period = self.extend_by_days \
                    if (set(movie.tags) & set(tagsIDs_to_extend)) else 0

                # check if there needs to be warn "DAYS" infront of removal
                # 1. Are we still within the period before removel?
                # 2. Is "NOW" less than "warning days" before removal?
                # 3. is "NOW" more then "warning days - 1" before removal
                #               (warn only 1 day)
                if (
                    timedelta(days=self.remove_after_days + extend_period) >
                    now - movieDateAdded and
                    movieDateAdded +
                    timedelta(days=self.remove_after_days + extend_period) -
                    now <= timedelta(days=self.warn_days_infront) and
                    movieDateAdded +
                    timedelta(days=self.remove_after_days + extend_period) -
                    now > timedelta(days=self.warn_days_infront) -
                    timedelta(days=1)
                ):

                    self.timeLeft = (
                        movieDateAdded +
                        timedelta(
                            days=self.remove_after_days +
                            extend_period) - now)

                    if self.pushover_enabled:
                        self.message = self.userPushover.send_message(
                            message=f"Script - {movie.title} ({movie.year}) "
                            f"will be removed from server in "
                            f"{'h'.join(str(self.timeLeft).split(':')[:2])}",
                            sound=self.pushover_sound
                        )

                    logging.info(
                        f"Script - WILL BE REMOVED - "
                        f"{movie.title} ({movie.year})"
                        f" in {'h'.join(str(self.timeLeft).split(':')[:2])}"
                        f" - {movieDateAdded}"
                    )

                # Check is movie is older than "days set in INI"
                if (
                    now - movieDateAdded >=
                        timedelta(
                            days=self.remove_after_days + extend_period)
                ):

                    if not self.dry_run:
                        if self.radarr_enabled:
                            self.radarr_node.delete_movie(
                                movie_id=movie.id,
                                delete_files=self.delete_files,
                                add_exclusion=self.radarr_add_exclusion)

                    if self.delete_files:
                        self.txtFilesDelete = \
                            ", files deleted."
                    else:
                        self.txtFilesDelete = \
                            ", files preserved."

                    if self.pushover_enabled:
                        self.message = self.userPushover.send_message(
                            message=f"{movie.title} ({movie.year}) "
                            f"Script - REMOVED - {movie.title} ({movie.year})"
                            f"{self.txtFilesDelete}"
                            f" - {movieDateAdded}",
                            sound=self.pushover_sound
                        )

                    logging.info(
                        f"Script - REMOVED - {movie.title} ({movie.year})"
                        f"{self.txtFilesDelete}"
                        f" - {movieDateAdded}"
                    )
                    self.anyMovieRemoved = True

    def run(self):
        if not self.enabled_run:
            logging.info(
                "Script - Library purge disabled")
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
            self.radarr_node = RadarrCli(
                self.radarr_url, self.radarr_token)

        # Convert tags to a dictionary
        tagIDsByLabels = {}
        for tag in self.radarr_node.get_tag():
            # Add tag to lookup by it's name
            tagIDsByLabels[tag['label']] = tag['id']

        if not tagIDsByLabels:
            logging.info(
                "Script - No tags found on Radarr server. "
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
            media = self.radarr_node.get_movie()

        # Make sure the library is not empty.
        if media:
            # There is only 1 movie in the library
            if type(media) is RadarrMovieItem:
                self.evalMovie(media, tagIDsByLabels)

            else:  # there is more than 1 movie
                media.sort(key=self.sortOnTitle)  # Sort the list on Title
                for movie in media:
                    self.evalMovie(movie, tagIDsByLabels)

        if not self.anyMovieRemoved:

            if self.pushover_enabled:
                self.message = self.userPushover.send_message(
                    message="Script - No movies were removed from "
                    "the server",
                    sound=self.pushover_sound
                )

            logging.info(
                "Script - No movies were removed from the server"
            )


if __name__ == '__main__':

    rlp = RLP()
    rlp.run()
    rlp = None
