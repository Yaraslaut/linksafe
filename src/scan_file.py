#!/usr/bin/env python3
import re
import logging
from link import scan_links
import threading
import concurrent.futures
import os
from sys import argv
from sys import exit
logging.basicConfig(format='%(levelname)s:%(message)s', level=os.environ.get("LOGLEVEL", "INFO"))

try:

    ignored_links = ["https://example.com", "http://example.com", "http://localhost", "http://localhost"]

    # this link is working, its just the longest web page loading you can experience in this universe
    ignored_links.append("http://unicode.org/emoji/charts/full-emoji-list.html")

    if os.getenv("INPUT_IGNORED_LINKS"):
        user_ignored_links = os.getenv("INPUT_IGNORED_LINKS").replace("\n"," ").split(",")
        for link in user_ignored_links:
            ignored_links.append(link.strip())
    ignored_files = []
    if os.getenv("INPUT_IGNORED_FILES"):
        ignored_files = os.getenv("INPUT_IGNORED_FILES").replace("\n"," ").split(",")

    ignored_dirs = [ "build", ".git", ".cache", ".github"]
    if os.getenv("INPUT_IGNORED_DIRS"):
        user_ignored_dirs = os.getenv("INPUT_IGNORED_DIRS").replace("\n"," ").split(",")
        for d in user_ignored_dirs:
            ignored_dirs.append(d)
except:
    logging.info("Error loading env variables, please check your .github/workflows workflow")
    exit(1)


pattern = re.compile(r"(http|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])")
links = []

# add recursivly all directories in current path
def find_all_subdirs(dir):
    subdirs = []
    for f in os.scandir(dir):
        if f.is_dir():
            if f.name not in ignored_dirs:
                subdirs.append(f.path)
    for dir in list(subdirs):
        sf = find_all_subdirs(dir)
        subdirs.extend(sf)
    return subdirs

directories = ["."]
subdirs = find_all_subdirs(directories[0])
[directories.append(subdir) for subdir in subdirs]
logging.info(f"directories: {directories}")
logging.info(f"list of ignored links: {ignored_links}")
logging.info(f"list of ignored dirs:  {ignored_dirs}")
logging.info(f"list of ignored files: {ignored_files}")


# loop through the directories, e.g. [".", "./src", "./doc"]
def process_directory(directory):
    directory = directory.strip()
    logging.debug(f"Processing directory {directory}")
    if directory != "." and not directory.startswith("./"):
        old_directory = directory
        directory = f"./{directory}"
        logging.debug(f"Directory '{old_directory}' converted to relative filepath '{directory}'")
    try:
        scan = os.scandir(directory)
    except FileNotFoundError:
        logging.info(f"Directory '{directory}' not found, please check the file path (only use relative paths) and spelling")
        exit(78)
    for file_object in scan:
        file = file_object.path
        if file_object.is_file():  # filter out dirs like .git
            if file in ignored_files:
                logging.info(f"{file} skipped due to ignored files")
                # skip the file
                continue
            logging.debug(f"Scanning {file} file")
            # scan file
            try:
                for i, line in enumerate(open(file)):
                    for match in re.finditer(pattern, line):
                        try:
                            re_match = match.group()
                            logging.debug(f"Link found on line {i+1}: {re_match}")
                        except Exception as e:
                            logging.info(e)
                        else:
                            for ignore_link in ignored_links:
                                if ignore_link in re_match:
                                    logging.info(f"Link ignored : {re_match}")
                                    break
                            else:  # if link is not ignored
                                links.append(re_match)
                                logging.debug(f"Link from {file}:{i+1} added for scanning {match.group()}" )
            except UnicodeDecodeError:  # if the file contents can't be read
                logging.debug(f"'{file}' has been skipped as it is not readable!")
                continue  # skip to next file


with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    executor.map(process_directory, directories)


unique_links = []

for link in links:
    if link not in unique_links:
        unique_links.append(link)


logging.info("\n\nLink check starting:\n")
logging.info(f"Total number of links to check {len(links)}")
logging.info(f"Total number of unique links to check {len(unique_links)}")
try:
    scan_links(unique_links)
except Exception as e:
    logging.info(e)
