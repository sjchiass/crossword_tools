from utilities.llm import *
from utilities.corpus import *
import argparse
from tqdm import tqdm


def summarize_word(word):
    llm = LLM()
    doc = word.doc
    generate = llm.summarize(doc, word.word)
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

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Whether to overwrite existing summaries with new ones.",
    )

    args = parser.parse_args()

    corpus = corpus_from_json(open(args.input, "r"))

    for word in (pbar := tqdm(corpus.vocabulary)):
        pbar.set_description(f"Summarizing {word.word:<15}")
        if word.summary is None or args.overwrite:
            word = summarize_word(word)
            # Save our work
            corpus.to_json(open(args.input, "w"))
