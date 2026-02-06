import shelve

SHELVE_FILE = "frontier.shelve"
save = shelve.open(SHELVE_FILE)
def num_unique_pages():
    print("Number of unique pages: ", len(save.keys()) - 3)

def longest_page():
    print("Longest page: ", save['longest_page'])

def most_common_words(limit=50):
    print(f"{limit} most common words: ")
    n = 0
    word_frequencies = save['word_frequency'].items()
    for k, v in word_frequencies:
        if n == limit: break
        print(f"{k}: {v}  ", end='')
        n += 1
    print()

def subdomains():
    print(f"{len(save['subdomain_frequencies'].keys())} subdomains found: ")
    print(save['subdomain_frequencies'])

if __name__ == "__main__":
    num_unique_pages()
    longest_page()
    most_common_words()
    subdomains()

