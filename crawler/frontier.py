import os
import shelve
import time
from threading import Thread, RLock
from queue import Queue, Empty
from urllib.parse import urlparse
from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        
        # Thread-safe structures
        self.domain_last_access = {}
        self.domain_lock = RLock()
        self.frontier_lock = RLock()  # Lock for frontier operations
        self.save_lock = RLock()  # Lock for shelve operations
        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
            self.save['longest_page'] = (None, 0)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        with self.frontier_lock:
            try:
                return self.to_be_downloaded.pop()
            except IndexError:
                return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        with self.save_lock:
            if urlhash not in self.save:
                self.save[urlhash] = (url, False)
                self.save.sync()
                with self.frontier_lock:
                    self.to_be_downloaded.append(url)
    
    def mark_url_complete(self, url, word_count):
        urlhash = get_urlhash(url)
        with self.save_lock:
            if urlhash not in self.save:
                # This should not happen.
                self.logger.error(
                    f"Completed url {url}, but have not seen it before.")
            
            if word_count > self.save['longest_page'][1]:
                self.save['longest_page'] = (url, word_count)
                
            self.save[urlhash] = (url, True)
            self.save.sync()
    
    def wait_for_politeness(self, url):
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            return
        sleep_time = 0
        with self.domain_lock:
            now = time.time()
            available_at = self.domain_last_access.get(domain, 0)

            if now < available_at:
                sleep_time = available_at - now
            self.domain_last_access[domain] = max(now, available_at) + self.config.time_delay    
      
        if sleep_time > 0:
            self.logger.info(f"Politeness delay: sleeping {sleep_time:.2f}s for {domain}")
            time.sleep(sleep_time)
    
    def record_domain_access(self, url):
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            return
        
        with self.domain_lock:
            self.domain_last_access[domain] = time.time()
