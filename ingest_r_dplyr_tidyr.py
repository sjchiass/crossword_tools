from utilities.llm import *
from utilities.corpus import *
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os.path


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

# If the JSON data file doesn't exist yet, create it
if not os.path.isfile(args.output):
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
        for f in functions:
            corpus.add_word(
                Word(
                    word=f.text,
                    language="R",
                    type="function",
                    category=f"{lib} function",
                    url="https://rdrr.io" + f["href"],
                )
            )

    # Save the corpus to JSON
    corpus.to_json(open(args.output, "w"))

corpus = corpus_from_json(open(args.output, "r"))

for word in (pbar := tqdm(corpus.vocabulary)):
    pbar.set_description(f"Summarizing {word.word}")
    llm = LLM()
    if word.summary is None:
        soup = BeautifulSoup(requests.get(word.url).content, "html.parser")
        doc = "".join([s for s in soup.find("div", id="man-container").strings])
        # There seems to be a limit of input that Ollama can take
        # The Ollama server will crash if it gets too much
        generate = llm.summarize(doc[:50000])
        word.summary = generate
        # Try to prompt the LLM more
        llm.gen("Refer to your summary's information when answering my next question.")
        clue = llm.give_clue(word.word + " " + word.category)
        word.clue_en = clue
    elif word.clue_en is None:
        llm.gen(
            "Read the following:\n\n"
            + word.summary
            + "\n\nRefer to its information when answering my next question."
        )
        clue = llm.give_clue(word.word + " " + word.category)
        word.clue_en = clue
    # save
    corpus.to_json(open(args.output, "w"))

corpus.to_json(open(args.output, "w"))
