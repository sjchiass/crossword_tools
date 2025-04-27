from utilities.llm import *
from utilities.corpus import *
import argparse
from tqdm import tqdm
from create_summaries import summarize_word
from pathlib import Path
import ollama
from create_summaries import summarize_word

Path("./test_outputs").mkdir(parents=True, exist_ok=True)

LIST_OF_MODELS = [
    "llama3.1:8b",
    # "llama3.2:1b",
    "llama3.2:3b",
    # "gemma2:2b",
    "gemma2:9b",
    # "gemma2:27b",
    # "gemma3:4b",
    "gemma3:12b",
    # "gemma3:27b",
    # "phi4-mini:3.8b",
    "phi4:14b",
    "mistral:7b",
    # "mistral-small:22b",
    # "mistral-nemo:12b",
    # "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen2.5:14b",
    # "hermes3:3b",
    # "hermes3:8b",
    # "qwq:32b",
    # "deepseek-r1:7b",
    # "deepseek-r1:8b",
    # "deepseek-r1:14b",
    # "deepseek-r1:32b",
]

# Check that all models are installed
for m in LIST_OF_MODELS:
    print(f"Pulling {m} ...")
    ollama.pull(m)

parser = argparse.ArgumentParser(
    prog="",
    description="Utility script for finding the best Ollama model",
)

parser.add_argument(
    "input",
    type=str,
    help="The input JSON file.",
)

parser.add_argument("--clues", action="store_true", help="Generate clues for testing")

parser.add_argument(
    "--summaries", action="store_true", help="Generate summaries for testing"
)

args = parser.parse_args()

# One must be selected
if not (args.clues != args.summaries):
    ValueError("Run this script with one of either --clues or --summaries")

for model in LIST_OF_MODELS:
    if Path(
        Path("./test_outputs") / (Path(args.input).stem + model + ".json")
    ).exists():
        data, datatype = infer_from_json(
            open(
                Path("./test_outputs") / (Path(args.input).stem + model + ".json"), "r"
            )
        )
    else:
        data, datatype = infer_from_json(open(args.input, "r"))

    if datatype == "Crossword":
        words = data.get_clues()
    else:
        words = data.vocabulary

    for n, word in enumerate(pbar := tqdm(words)):
        pbar.set_description(f"{model:<15} {word.word:>15}")
        if word.clue_en is None and not word.locked:
            llm = LLM(
                model=model,
                system="You are a helpful AI assistant. You only provide very short and direct answers.",
            )
            if args.clues:
                if word.summary is None:
                    raise ValueError(
                        f"Missing summary for word {word.word}. Please generate summary"
                    )
                summary = (
                    "Read the following:\n\n"
                    + word.summary
                    + "\n\nRefer to its information when answering my next question."
                )
                clue = llm.give_clue(
                    answer=word.word,
                    category=word.category,
                    pre_prompt=summary,
                )
                word.clue_en = clue
            else:
                word = summarize_word(word)
        # save
        data.to_json(open(Path("./test_outputs") / (model + ".json"), "w"))
