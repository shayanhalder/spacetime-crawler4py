from datetime import date
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

SEEN_EXACT_HASHES = set()
SEEN_SIMHASHES = set()
SIMHASH_DIFF_THRESHOLD = 6

def scraper(url, resp):
    links, words = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)], words

def tokenize(text: str) -> list[str]:
    tokens = []
    seen = set()
    current_token = []
    
    i = 0
    while i < len(text): 
        char = text[i]
        if not char:
            if current_token:
                final_token = (''.join(current_token)).lower()
                if final_token in seen: 
                    current_token = []
                    i += 1
                    continue
                tokens.append(final_token)
                seen.add(final_token)
                current_token = []
            break
        
        if (char and not char.isalnum() or not char.isascii()):
            if current_token:
                final_token = (''.join(current_token)).lower()
                if final_token in seen: 
                    current_token = []
                    i += 1
                    continue
                tokens.append(final_token)
                seen.add(final_token)
                current_token = []
        else:
            current_token.append(char)
        
        i += 1
    
    return tokens

def extract_next_links(url, resp, min_text_length=200):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    
    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        return [], []

    # check if file is not html
    content_type = resp.raw_response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        return [], []
    
    # check if file size is very large (>2MB); avoid crawling
    if len(resp.raw_response.content) > 2_000_000:
        return [], []

    links = set()
    
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        # check if page has little text; avoid crawling
        text = soup.get_text(separator=' ', strip=True)

        words = tokenize(text)

        # words = text.split()
        # words = [w for w in words if re.search(r'[a-zA-Z]', w)] # only count words with letters

        if len(text) < min_text_length:
            return [], words

        if exact_duplicate(text):
            return [], words

        # document_fingerprint = compute_simhash(words)
        # if near_duplicate(document_fingerprint):
        #     return [], words

        a_tags = soup.find_all('a', href=True)
        for anchor in a_tags:
            href = anchor['href']
            absolute_url = urljoin(resp.url, href)
            
            # remove fragments
            absolute_url = absolute_url.split('#')[0]

            if absolute_url:
                links.add(absolute_url)
        
        return list(links), words
    
    except Exception as e:
        print(f"Error extracting links from {url}: {e}")
        
    return [], words

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # check if domain is one of the allowed UCI domains
        allowed_domains = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]
        netloc_lower = parsed.netloc.lower()
        if not any(netloc_lower.endswith(domain) or netloc_lower == domain[1:] for domain in allowed_domains):
            return False
        
        ### Check and avoid infinite traps ###
        # url too long
        if len(url) > 300:
            return False

        # check for trap keywords
        if re.search(r"(calendar|login|signup|reply|share)", url.lower()):
            return False
        
        # hardcoded traps 
        traps = ["wiki.ics.uci.edu/doku.php", "grape.ics.uci.edu/wiki", "/events", "/event", "/~eppstein/junkyard", "/~dechter/publications"]
        for trap in traps: 
            if trap in url.lower(): 
                return False

        date_patterns = [
            r"\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b",   # 2023-05-22, 2023/05/22, 2023.05.22
            r"\b\d{8}\b",  # 20230522
            r"\b\d{4}[-/\.]\d{1,2}\b"  # 2023-05, 2023/05, 2023.05
        ]
        # check if any query parameter values contain any dates (ex: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD)
        if parsed.query:
            # date_patterns = [
            #     r"\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b",   # 2023-05-22, 2023/05/22, 2023.05.22
            #     r"\b\d{8}\b"  # 20230522
            # ]
            query_lower = parsed.query.lower()
            for pat in date_patterns:
                if re.search(pat, query_lower):
                    return False
            # check if "date" or "dates" appears as query keys or values
            query_params = query_lower.split('&')
            for param in query_params:
                if "date" in param or "dates" in param or "ical" in param:
                    return False
        
        # check if any dates are in the path
        if parsed.path:
            for pat in date_patterns:
                if re.search(pat, parsed.path):
                    return False

        # skip pagination (can change to allow based on reqs)
        if re.search(r"(page=\d+|p=\d+)", url.lower()):
            return False

        # check for excessive query params
        if parsed.query and len(parsed.query) > 100:
            return False

        # disallow any file types other than html
        return (not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv|json"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()) and not
            re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv|json"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.query.lower())
            )

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def exact_duplicate(text):
    # Duplicate detection using normalized text (all lowercase, extra spacing removed).
    # Uses a checksum-style polynomial rolling hash.

    normalized = re.sub(r"\s+", " ", text.lower()).strip()

    h = 0
    base = 31
    mod = 2**64  # limit hash to 64 bits

    for ch in normalized:
        h = (h * base + ord(ch)) % mod

    if h in SEEN_EXACT_HASHES:
        return True

    SEEN_EXACT_HASHES.add(h)
    return False

def hash_word(word):
    # Generates a deterministic hash value for a word using
    # a polynomial rolling hash.

    hash_value = 0
    base = 131

    for character in word:
        hash_value = hash_value * base + ord(character)

    return hash_value & ((1 << 64) - 1)

def compute_simhash(word_list, fingerprint_size=64):
    # Computes a SimHash fingerprint for a document
    # Words are treated as features weighted by frequency
    feature_weights = {}
    for word in word_list:
        feature_weights[word] = feature_weights.get(word, 0) + 1
    
    similarity_vector = [0] * fingerprint_size

    for word, weight in feature_weights.items():
        word_hash = hash_word(word)  # fixed-length hash value for the word

        for bit_position in range(fingerprint_size):
            bit_mask = 1 << bit_position

            if word_hash & bit_mask:
                similarity_vector[bit_position] += weight
            else:
                similarity_vector[bit_position] -= weight

    fingerprint = 0
    for bit_position in range(fingerprint_size):
        if similarity_vector[bit_position] > 0:
            fingerprint |= (1 << bit_position)

    return fingerprint

def count_bit_differences(hash1, hash2):
    # Counts how many bit positions differ between two fingerprints.
    diff = hash1 ^ hash2  # XOR highlights differing bits
    count = 0

    while diff:
        count += diff & 1
        diff >>= 1

    return count

def near_duplicate(simhash):
    # Returns True if a similar fingerprint has already been seen.
    for seen_hash in SEEN_SIMHASHES:
        if count_bit_differences(simhash, seen_hash) <= SIMHASH_DIFF_THRESHOLD:
            return True

    SEEN_SIMHASHES.add(simhash)
    return False

