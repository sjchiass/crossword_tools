from utilities.llm import *
from utilities.corpus import *
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re


parser = argparse.ArgumentParser(
    prog="Ingest data on all of the tidyverse packages.",
    description="This uses online data to generate information on all of the tidyverse packages.",
)

parser.add_argument(
    "output",
    type=str,
    help="The output JSON file.",
)

args = parser.parse_args()

print("Retrieving web data ...")

# The page for the Python standard library is easy to scrape for names
URL = "https://cran.r-project.org/web/packages/tidyverse/index.html"

# We can retrieve the page's source for BeautifulSoup to parse
soup = BeautifulSoup(requests.get(URL).content, "html.parser")

imports = (
    soup.find(lambda tag: tag.name == "td" and "Imports:" in tag.text)
    .find_next_sibling("td")
    .text
)

package_names = re.findall(r"[a-zA-Z]{1}[a-zA-Z0-9_\.]+", imports)

# One approach is using the CRAN pages for descriptions, but these can be really sparse
corpus = Corpus()
for lib in (pbar := tqdm(re.findall(r"[a-zA-Z]{1}[a-zA-Z0-9_\.]+", imports))):
    pbar.set_description(f"Collecting {lib:<10}")
    r = requests.get(
        f"https://cran.r-project.org/web/packages/{lib}/readme/README.html"
    )
    if r.ok:
        soup = BeautifulSoup(r.content, "html.parser")
        doc = "".join([s for s in soup.find("body").strings])
    else:
        soup = BeautifulSoup(
            requests.get(
                f"https://cran.r-project.org/web/packages/{lib}/index.html"
            ).content,
            "html.parser",
        )
        doc = soup.find("p").text
    corpus.add_word(
        Word(
            word=lib,
            language="R",
            type="module",
            category="tidyverse packages",
            doc=doc,
        )
    )

# Save the corpus to JSON
corpus.to_json(open(args.output, "w"))
