import os
import shelve
import time
from threading import Thread, RLock
from queue import Queue, Empty
from urllib.parse import urlparse
from utils import get_logger, get_urlhash, normalize
from scraper import is_valid
from collections import defaultdict

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
            self.save['subdomain_frequencies'] = defaultdict[str, int](int)
            self.save['word_frequency'] = defaultdict[str, int](int)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)
        self.stop_words = {"a","about","above","after","again","against","all","am","an","and","any","are","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself","let's","me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"}

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
    
    def log_domain_count(self, url):
        domain = urlparse(url).netloc.lower()

        with self.save_lock:
            self.save['subdomain_frequencies'][domain] += 1
            self.save.sync()
    
    def log_word_frequency(self, words):
        with self.save_lock:
            for word in words:
                if not word in self.stop_words:
                    self.save['word_frequency'][word] += 1
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
