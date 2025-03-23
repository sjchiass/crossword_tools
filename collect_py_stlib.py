from utilities.llm import *
from utilities.corpus import *
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


parser = argparse.ArgumentParser(
    prog="Ingest data on built-in Python modules",
    description="This uses the built-in documentation to get information on the modules part of the Standard Python library.",
)

parser.add_argument(
    "output",
    type=str,
    help="The output JSON file.",
)

args = parser.parse_args()

print("Retrieving web data ...")

# The page for the Python standard library is easy to scrape for names
URL = "https://docs.python.org/3/library/index.html"

# We can retrieve the page's source for BeautifulSoup to parse
soup = BeautifulSoup(requests.get(URL).content, "html.parser")

# The library names are all in <code> blocks with the py-mod class
# The library names are all inner text so you can get them with .text\
# The URLs to the pages are preditable, which is good.
corpus = Corpus()
for lib in (pbar := tqdm(soup.find_all(class_="py-mod"))):
    pbar.set_description(f"Collecting {lib.text:<10}")
    corpus.add_word(
        Word(
            word=lib.text,
            language="python",
            type="module",
            category="python standard library",
            doc="".join(
                [
                    s
                    for s in BeautifulSoup(
                        requests.get(
                            f"https://docs.python.org/3/library/{lib.parent['href']}"
                        ).content,
                        "html.parser",
                    )
                    .find(class_="body")
                    .strings
                ]
            ),
        )
    )

# Save the corpus to JSON
corpus.to_json(open(args.output, "w"))
