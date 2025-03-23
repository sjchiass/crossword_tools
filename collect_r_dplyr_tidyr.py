from utilities.llm import *
from utilities.corpus import *
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


parser = argparse.ArgumentParser(
    prog="Ingest data on the dplyr and tidyr R packages.",
    description="This uses online data to generate information on all of the dplyr and tidyr functions.",
)

parser.add_argument(
    "output",
    type=str,
    help="The output JSON file.",
)

args = parser.parse_args()

print("Retrieving web data ...")

corpus = Corpus()

# To start, only do the two big main data wrangling packages
for lib in ["dplyr", "tidyr"]:

    # The page for the Python standard library is easy to scrape for names
    URL = f"https://rdrr.io/cran/{lib}/man/"

    # We can retrieve the page's source for BeautifulSoup to parse
    soup = BeautifulSoup(requests.get(URL).content, "html.parser")

    functions = soup.find("table").find_all("a")

    # One approach is using the CRAN pages for descriptions, but these can be really sparse
    for f in (pbar := tqdm(functions)):
        pbar.set_description(f"Collecting {f.text:<10}")
        corpus.add_word(
            Word(
                word=f.text,
                language="R",
                type="function",
                category=f"{lib} function",
                doc="".join(
                    [
                        s
                        for s in BeautifulSoup(
                            requests.get("https://rdrr.io" + f["href"]).content,
                            "html.parser",
                        )
                        .find("div", id="man-container")
                        .strings
                    ]
                ),
            )
        )

# Save the corpus to JSON
corpus.to_json(open(args.output, "w"))
