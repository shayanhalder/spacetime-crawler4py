import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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

    # check if file size is very large (>2MB); avoid crawling
    if len(resp.raw_response.content) > 2_000_000:
        return [], []

    links = set()
    
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        # check if page has little text; avoid crawling
        text = soup.get_text(separator=' ', strip=True)

        words = text.split()
        words = [w for w in words if re.search(r'[a-zA-Z]', w)] # only count words with letters

        if len(text) < min_text_length:
            return [], words

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

        # skip pagination (can change to allow based on reqs)
        if re.search(r"(page=\d+|p=\d+)", url.lower()):
            return False

        # check for excessive query params
        if parsed.query and len(parsed.query) > 100:
            return False

        # disallow any file types other than html
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv|json"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
