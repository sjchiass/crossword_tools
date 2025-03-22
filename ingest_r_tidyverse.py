from utilities.llm import *
from utilities.corpus import *
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os.path
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

# If the JSON data file doesn't exist yet, create it
if not os.path.isfile(args.output):
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
    for lib in re.findall(r"[a-zA-Z]{1}[a-zA-Z0-9_\.]+", imports):
        corpus.add_word(
            Word(
                word=lib,
                language="R",
                type="module",
                category="tidyverse packages",
                url=f"https://cran.r-project.org/web/packages/{lib}/index.html",
                readme=f"https://cran.r-project.org/web/packages/{lib}/readme/README.html",
            )
        )

    # Save the corpus to JSON
    corpus.to_json(open(args.output, "w"))

corpus = corpus_from_json(open(args.output, "r"))

for word in (pbar := tqdm(corpus.vocabulary)):
    pbar.set_description(f"Summarizing {word.word}")
    llm = LLM()
    if word.summary is None:
        r = requests.get(word.readme)
        if r.ok:
            soup = BeautifulSoup(r.content, "html.parser")
            doc = "".join([s for s in soup.find("body").strings])
        else:
            soup = BeautifulSoup(requests.get(word.url).content, "html.parser")
            doc = soup.find("p").text
        # There seems to be a limit of input that Ollama can take
        # The Ollama server will crash if it gets too much
        generate = llm.summarize(doc[:50000])
        word.summary = generate
        # Try to prompt the LLM more
        llm.gen("Refer to your summary's information when answering my next question.")
        clue = llm.give_clue(word.word + " R package")
        word.clue_en = clue
    elif word.clue_en is None:
        llm.gen(
            "Read the following:\n\n"
            + word.summary
            + "\n\nRefer to its information when answering my next question."
        )
        clue = llm.give_clue(word.word + " R package")
        word.clue_en = clue
    # save
    corpus.to_json(open(args.output, "w"))

corpus.to_json(open(args.output, "w"))
