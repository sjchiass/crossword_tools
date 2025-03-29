from utilities.llm import *
from utilities.corpus import *
import argparse
from tqdm import tqdm
from create_summaries import summarize_word


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
    "--direct",
    action="store_true",
    help="Will skip generating summaries before generating clues.",
)

parser.add_argument(
    "--interactive",
    action="store_true",
    help="Will let you choose to accept or reject generated clues, or edit them yourself. Recommended.",
)

args = parser.parse_args()

data, datatype = infer_from_json(open(args.input, "r"))

if datatype == "Crossword":
    words = data.get_clues()
else:
    words = data.vocabulary

for n, word in enumerate(words):
    if word.clue_en is None and not word.locked:
        print(f"Generating clue {n+1} of {len(words)} : {word.word} ...")
        llm = LLM()
        if args.direct:
            summary = ""
        else:
            if word.summary is None:
                print(f"Generating summary for {word.word} ...")
                word = summarize_word(word)
            summary = (
                "Read the following:\n\n"
                + word.summary
                + "\n\nRefer to its information when answering my next question."
            )
            print(word.word, "\n---")
            print(word.summary + "\n")
        while True:
            clue = llm.give_clue(
                word.word + " " + word.category,
                pre_prompt=summary,
            )
            if args.interactive:
                user_input = input(
                    "\n"
                    + clue
                    + "\nDo you accept this clue?"
                    + "\n Y : yes (default)"
                    + "\n N : no, retry"
                    + "\n W : write your own"
                    + "\n L : lock the word"
                    + "\n S : skip to the next word"
                    + "\n > "
                ).lower()
                if user_input in ["y", ""]:
                    break
                elif user_input == "w":
                    clue = input("Write your own clue and press ENTER to save. > ")
                    break
                elif user_input == "l":
                    clue = None
                    word.locked = True
                    break
                elif user_input == "s":
                    clue = None
                    break
            else:
                break
        word.clue_en = clue
    # save
    data.to_json(open(args.input, "w"))
