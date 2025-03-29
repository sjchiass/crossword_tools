from utilities.llm import *
from utilities.corpus import *
import argparse
from tqdm import tqdm
from create_summaries import summarize_word
from pathlib import Path

Path("/test_outputs").mkdir(parents=True, exist_ok=True)

LIST_OF_MODELS = [
    "llama3.1:8b",
    "llama3.2:1b",
    "llama3.2:3b",
    "gemma2:2b",
    "gemma2:9b",
    "gemma3:4b",
    "gemma3:12b",
    "phi4-mini",
    "phi4:14b",
]


parser = argparse.ArgumentParser(
    prog="",
    description="Utility script for finding the best Ollama model",
)

parser.add_argument(
    "input",
    type=str,
    help="The input JSON file.",
)

args = parser.parse_args()

data, datatype = infer_from_json(open(args.input, "r"))

if datatype == "Crossword":
    words = data.get_clues()
else:
    words = data.vocabulary

for model in LIST_OF_MODELS:
    for n, word in enumerate(words):
        if word.clue_en is None and not word.locked:
            print(f"Generating clue {n+1} of {len(words)} : {word.word} ...")
            llm = LLM(model=model)
            if word.summary is None:
                raise ValueError(
                    f"Missing summary for word {word.word}. Please generate summary"
                )
            summary = (
                "Read the following:\n\n"
                + word.summary
                + "\n\nRefer to its information when answering my next question."
            )
            print(word.word, "\n---")
            print(word.summary + "\n")
            clue = llm.give_clue(
                word.word + " " + word.category,
                pre_prompt=summary,
            )
            word.clue_en = clue
        # save
        data.to_json(
            open(Path("./test_outputs") / Path(args.input).name + model / ".json", "w")
        )
