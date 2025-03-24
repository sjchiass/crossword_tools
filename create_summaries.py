from utilities.llm import *
from utilities.corpus import *
import argparse
from tqdm import tqdm

parser = argparse.ArgumentParser(
    prog="",
    description="T",
)

parser.add_argument(
    "input",
    type=str,
    help="The input JSON file.",
)

args = parser.parse_args()

corpus = corpus_from_json(open(args.input, "r"))

for word in (pbar := tqdm(corpus.vocabulary)):
    pbar.set_description(f"Summarizing {word.word}")
    llm = LLM()
    if word.summary is None:
        doc = word.doc
        # There seems to be a limit of input that Ollama can take
        # The Ollama server will crash if it gets too much
        generate = llm.summarize(doc[:5000])
        word.summary = generate
        # Save our work
        corpus.to_json(open(args.input, "w"))
