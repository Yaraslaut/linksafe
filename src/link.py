import logging
import requests
import re
import threading
import concurrent.futures
from sys import exit
from os import environ



bad_links = []
warning_links = []
good_link_count = 0
thread_local = threading.local()



def write_summary(payload):
    with open("tmp.txt", "a") as file:
        file.write(f"{payload}\n")


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

def scan_link(link):
    logging.debug(f"Checking link {link}")
    global good_link_count
    try:
        session = get_session()
        if "api.github.com" in link:
            return
        try:
            with session.get(link, timeout=15) as response:
                response = response.status_code
        except requests.exceptions.SSLError:
            logging.debug(f"---> SSL certificate error for link: {link}")
            bad_links.append(link)
        except requests.exceptions.ReadTimeout:
            logging.debug(f"---> Connection timed out for link: {link}")
            bad_links.append(link)
        except requests.exceptions.RequestException as err:
            if "Max retries exceeded with url" in str(err):
                logging.debug(f"Link connection failed, max retries reached: {link}")
                bad_links.append(link)
            else:
                logging.debug(f"---> Connection error: {err} for link: {link}")
                bad_links.append(link)
        except Exception as err:
            logging.debug(f"---> Unexpected exception occurred while making request: {err} for link: {link}")
        else:
            if response == 403:
                logging.debug(f"--> Link validity unkwown with 403 Forbidden return code for link: {link}")
                warning_links.append(link)
            elif response == 406:
                logging.debug(f"--> Link validity unkwown with 406 Not Acceptable return code for link: {link}")
                warning_links.append(link)
            elif response == 504:
                logging.debug(f"----> Error with status code 504 Gateway Timeout for link: {link}")
                bad_links.append(link)
            elif 561 >= response >= 400:
                logging.debug(f"----> Error with status code {response} for link: {link}")
                bad_links.append(link)
            elif response >= 300:  # between 300-400 HTTP REDIRECT
                logging.debug(f"--> Link redirecting with status code {response} for link: {link}")
                warning_links.append(link)
            elif response < 400:
                logging.debug(f"Link valid with status code {response}")
                good_link_count += 1
            elif response == 999:
                logging.debug("--> Linkedin specific return code 999")
                warning_links.append(link)
            else:
                logging.debug(f"--> Unknown return code {response} for link: {link}")
                warning_links.append(link)
    except Exception as e:
        logging.debug(e)


def all_sites(sites):
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(scan_link, sites)


def scan_links(unique_links):
    all_sites(unique_links)
    write_summary("# :link: Summary")
    write_summary(f":white_check_mark: Good links: {good_link_count}")
    write_summary(f":warning: Warning links: {len(warning_links)}")
    write_summary(f":no_entry_sign: Bad links: {len(bad_links)}")
    if warning_links:
        logging.debug("\n==== Links with non-definitive status codes ====")
        for link in warning_links:
            logging.info(f"Non-definitive status code: {link}")
    if bad_links:
        logging.info("Test failed")
        logging.info("\n==== Failed links ====")
        for link in bad_links:
            logging.info(f"FAILED: {link}")
        exit(1)
    else:
        logging.info("All links correct - test passed")
