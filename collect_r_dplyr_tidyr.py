from utilities.llm import *
from utilities.corpus import *
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import subprocess
import string

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
for lib, stop in [
    ["dplyr", "built-in-datasets"],
    # ["tidyr", "data"],
    # ["ggplot2", "data"], # Good idea to skip ggplot2 because it's huge
    # ["stringr", "bundled-data"],
    # ["lubridate", "data"],
    # ["purrr", "superseded"],
]:

    # The page for the Python standard library is easy to scrape for names
    URL = f"https://{lib}.tidyverse.org/reference/index.html"

    # We can retrieve the page's source for BeautifulSoup to parse
    soup = BeautifulSoup(requests.get(URL).content, "html.parser")

    functions = soup.find(id="main").find(id=stop).find_all_previous("a", class_=None)

    # Find functions. In these pages they include ()
    functions = [x.text.replace("()", "") for x in functions if "()" in x.text]

    # Only allow valid functions
    functions = [x for x in functions if set(x) <= set(string.ascii_lowercase + "._")]

    # With all this there will still be a few superseded functions, but there will be
    # very few

    for f in (pbar := tqdm(functions)):
        pbar.set_description(f"Collecting {f:<10}")
        help_command = (
            f"tools:::Rd2txt(utils:::.getHelpFile(as.character(help({f}, {lib}))))"
        )
        corpus.add_word(
            Word(
                word=f,
                language="R",
                type="function",
                category=f"{lib} function",
                # Below I run the help command to get the text. It will also include all R
                # console output. So I use .rpartition() to only keep everything after the
                # command itself.
                doc=subprocess.run(
                    [
                        "R",
                        "-e",
                        help_command,
                    ],
                    capture_output=True,
                    encoding="utf8",
                ).stdout.rpartition(help_command)[2],
            )
        )

# Save the corpus to JSON
corpus.to_json(open(args.output, "w"))
