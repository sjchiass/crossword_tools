from utilities.llm import *
from utilities.corpus import *
import argparse
from pandas import DataFrame
import subprocess
from tqdm import tqdm
import os.path

parser = argparse.ArgumentParser(
    prog="Ingest data on pandas DataFrame methods",
    description="This uses the built-in documentation to get information on the pandas DataFrame's methods.",
)

parser.add_argument(
    "output",
    type=str,
    help="The output JSON file.",
)

args = parser.parse_args()

# If the JSON data file doesn't exist yet, create it
if not os.path.isfile(args.output):
    corpus = Corpus()
    # Getting all of the BeautifulSoup HTML parser methods
    for m in dir(DataFrame):
        if m[0].isalpha() and m[0].islower():
            corpus.add_word(
                Word(
                    word=m,
                    imports="from pandas import DataFrame;",
                    invocation="DataFrame." + m,
                    language="python",
                    type="method",
                    category=f"DataFrame method",
                )
            )

    # Save the corpus to JSON
    corpus.to_json(open(args.output, "w"))

corpus = corpus_from_json(open(args.output, "r"))

for word in (pbar := tqdm(corpus.vocabulary)):
    pbar.set_description(f"Summarizing {word.word}")
    llm = LLM()
    if word.summary is None:
        doc = subprocess.run(
            [
                "python",
                "-c",
                f"import pydoc; {word.imports} print(pydoc.plain(pydoc.render_doc({word.invocation})));",
            ],
            capture_output=True,
            encoding="utf8",
        ).stdout
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
