from utilities.llm import *
from utilities.corpus import *
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os.path


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

# If the JSON data file doesn't exist yet, create it
if not os.path.isfile(args.output):
    print("Retrieving web data ...")

    # The page for the Python standard library is easy to scrape for names
    URL = "https://docs.python.org/3/library/index.html"

    # We can retrieve the page's source for BeautifulSoup to parse
    soup = BeautifulSoup(requests.get(URL).content, "html.parser")

    # The library names are all in <code> blocks with the py-mod class
    # The library names are all inner text so you can get them with .text\
    # The URLs to the pages are preditable, which is good.
    corpus = Corpus()
    for lib in soup.find_all(class_="py-mod"):
        corpus.add_word(
            Word(
                word=lib.text,
                language="python",
                type="module",
                category="python standard library",
                url=f"https://docs.python.org/3/library/{lib.parent['href']}",
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
        doc = "".join([s for s in soup.find(class_="body").strings])
        # There seems to be a limit of input that Ollama can take
        # The Ollama server will crash if it gets too much
        generate = llm.summarize(doc[:50000])
        word.summary = generate
        # Try to prompt the LLM more
        llm.gen("Refer to your summary's information when answering my next question.")
        clue = llm.give_clue(word.word + " python module")
        word.clue_en = clue
    elif word.clue_en is None:
        llm.gen(
            "Read the following:\n\n"
            + word.summary
            + "\n\nRefer to its information when answering my next question."
        )
        clue = llm.give_clue(word.word + " python module")
        word.clue_en = clue
    # save
    corpus.to_json(open(args.output, "w"))

corpus.to_json(open(args.output, "w"))
