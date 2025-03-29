from utilities.llm import *
from utilities.corpus import *
import argparse
from tqdm import tqdm


def summarize_word(word):
    llm = LLM()
    doc = word.doc
    generate = llm.summarize(doc)
    word.summary = generate
    return word


if __name__ == "__main__":
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
        if word.summary is None:
            word = summarize_word(word)
            # Save our work
            corpus.to_json(open(args.input, "w"))
