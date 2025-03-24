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
    if word.clue_en is None:
        llm.gen(
            "Read the following:\n\n"
            + word.summary
            + "\n\nRefer to its information when answering my next question."
        )
        print(word.word, "\n---")
        print(word.summary + "\n")
        while True:
            clue = llm.give_clue(word.word + " " + word.category)
            user_input = input(
                "\n" + clue + "\nDo you accept this clue? Y/n or E to edit > "
            ).lower()
            if user_input in ["y", ""]:
                break
            elif user_input == "e":
                clue = input("Write your own clue and press ENTER to save. > ")
                break
        word.clue_en = clue
    # save
    corpus.to_json(open(args.input, "w"))
