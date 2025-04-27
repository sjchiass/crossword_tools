import pathlib
from string import ascii_uppercase
from utilities.corpus import *
from random import sample
import argparse

parser = argparse.ArgumentParser(
    prog="",
    description="Utility script for finding the best Ollama model",
)

parser.add_argument("--clues", action="store_true", help="Generate clues for testing")

parser.add_argument(
    "--summaries", action="store_true", help="Generate summaries for testing"
)

args = parser.parse_args()

# One must be selected
if not (args.clues != args.summaries):
    ValueError("Run this script with one of either --clues or --summaries")

DELAY = 10
INTERVAL = 2

model_data = {}
models = []
losers = []
summaries = []

for datafile in pathlib.Path("./test_outputs").glob("*.json"):
    data, datatype = infer_from_json(open(datafile, "r"))
    models.append(datafile.stem)
    if datatype == "Crossword":
        words = data.get_clues()
    else:
        words = data.vocabulary
    if args.clues:
        model_data[datafile.stem] = {
            word.word: word.clue_en for word in words if not word.locked
        }
    else:
        model_data[datafile.stem] = {
            word.word: word.summary for word in words if not word.locked
        }

# Assuming all files have the same summaries
summaries = {w.word: w.summary for w in data.vocabulary}

letters = list(ascii_uppercase[: len(models)])
scores = {model: 0 for model in models}

all_words = []
for model in model_data.values():
    for word in model.keys():
        all_words.append(word)

all_words = set(all_words)

for n, word in enumerate(all_words):
    if len(models) == 0:
        print("Competition ended in a tie, from worse to best:")
        for loser in losers:
            print(loser)
        print("Thanks for playing!")
        quit()
    elif len(models) == 1:
        print("Competition done, from worse to best:")
        for loser in losers:
            print(loser)
        print(f"WINNER! {models[0]}")
        print("Thanks for playing!")
        quit()

    if args.clues:
        # Print the summary to assist
        print("\n---\n", summaries[word], "\n---\n", word, "\n---\n")
    else:
        # Printing the whole doc would be too much
        print("\n---\n", word, "\n---\n")

    candidates = {
        letter: {"word": model_data[model][word], "model": model}
        for model, letter in zip(models, sample(letters, len(letters)))
    }
    for letter in letters:
        print(f"{letter.upper()}) {candidates[letter]['word']}")

    good = input("Enter all of the letters that are GOOD > ").upper()
    for letter in list(good):
        if letter in candidates.keys():
            scores[candidates[letter]["model"]] += 1

    # Print again, without good choices
    print("\n---\n", word, "\n---\n")
    for letter in letters:
        if letter not in list(good):
            print(f"{letter}) {candidates[letter]['word']}")

    bad = input("Enter all of the letters that are BAD > ").upper()
    for letter in list(bad):
        if letter in candidates.keys():
            scores[candidates[letter]["model"]] -= 1
    print(scores)
    if n + 1 >= DELAY:
        if (n + 1 - DELAY) % INTERVAL == 0:
            # last_place = min(scores, key=scores.get)
            last_place = min(scores.values())
            for m in models:
                if scores[m] == last_place:
                    print(f"ROUND {n+1}: eliminate {m}")
                    losers.append(m)
            models = [m for m in models if m not in losers]
            scores = {k: v for k, v in scores.items() if k not in losers}
            letters = list(ascii_uppercase[: len(models)])

print("Competition done, models eliminated, from worse to best:")
for loser in losers:
    print(loser)
print("Remaining competitors:")
print(scores)
print(f"In the lead: {max(scores, key=scores.get)}")
