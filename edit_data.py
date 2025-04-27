from utilities.corpus import *
import argparse
from string import ascii_uppercase
import os
from math import ceil

# Fields that cannot be edited
READ_ONLY = ["id", "word", "doc", "x", "y", "index", "number"]

parser = argparse.ArgumentParser(
    prog="Data editor",
    description="A simple text interface for editing corpus and crossword data.",
)

parser.add_argument(
    "input",
    type=str,
    help="The input JSON file.",
)

parser.add_argument(
    "--lock",
    action="store_true",
    help="Enter a mode of toggling locked status on/off. Makes it much easier and quicker to remove unwanted words.",
)

parser.add_argument(
    "--hide",
    action="store_true",
    help="Do not display any locked items.",
)

args = parser.parse_args()


# Function for editing a data point
def edit_datapoint(datapoint):
    print(datapoint)
    # Get all fields that are not read only
    field_choices = [f for f in datapoint.get_fields() if f.name not in READ_ONLY]
    # Print out all of the fields
    for n, field in enumerate(field_choices):
        print(f"{ascii_uppercase[n]}) {field.name} : {datapoint.__dict__[field.name]}")
    # Capture the user's choice
    field_choice = input(f"Please choose a field to edit > ").upper().strip()
    if field_choice != "Q":
        field_choice = int(ascii_uppercase.index(field_choice))
        field = field_choices[field_choice].name
        datapoint = edit_field(datapoint, field)
    return datapoint


def edit_field(datapoint, field):
    if field == "locked":
        if datapoint.locked:
            status = "locked"
        else:
            status = "unlocked"
        print(f"{datapoint.word} is currently {status}.")
        lock = input("Do you want it to be locked? y/n, or enter Q to quit > ")
        if lock.lower() == "y":
            datapoint = datapoint.replace_value(field, True)
        elif lock.lower() == "n":
            datapoint = datapoint.replace_value(field, False)
    else:
        new_value = input("Please enter the new value, or enter Q to quit > ").strip()
        if new_value.lower() != "q":
            datapoint = datapoint.replace_value(field, new_value)
    return datapoint


def lock_datapoint(datapoint):
    if datapoint.locked:
        datapoint = datapoint.replace_value("locked", False)
    else:
        datapoint = datapoint.replace_value("locked", True)
    return datapoint


while True:
    # Read in the JSON file, determining what type it is
    datafile, datatype = infer_from_json(open(args.input, "r"))

    # Generate a multiple choices prompt
    to_print = []
    if datatype == "Corpus":
        dataset = datafile.vocabulary
        for n, word in enumerate(dataset):
            status = ""
            if word.locked:
                if args.hide:
                    continue
                status = "LOCKED"
            to_print.append(f"{n:<3}) {word.word} [{word.category}] {status}")
    elif datatype == "Crossword":
        # Normally this would work fine since lists hold references;
        # however, it looks like my use of functions breaks the references...
        # I'll have to test further.
        dataset = datafile.down + datafile.across
        to_print.append("DOWN")
        for n, word in enumerate(dataset):
            if n == len(datafile.down):
                to_print.append("ACROSS")
            status = ""
            if word.locked:
                if args.hide:
                    continue
                status = "LOCKED"
            to_print.append(f"{n:<3}) {word.word} [{word.category}] {status}")
    # Print out the choices in columns on the console, to make more compact
    width, height = os.get_terminal_size()
    max_len = max([len(x) for x in to_print]) + 1  # For padding
    max_cols = max(1, width // max_len)
    max_rows = ceil(len(to_print) / max_cols)
    print(width, height, max_len, max_cols, max_rows)
    # Print out in columns
    for n, row in enumerate(range(max_rows)):
        for m, col in enumerate(range(max_cols)):
            if n + m * max_rows < len(to_print):
                print(f"{to_print[n + m * max_rows]:<{max_len}}", end="")
        print()
    word_choice = input(
        "Please enter the number of the word you would like to edit, or enter Q to quit > "
    )
    if word_choice.lower() == "q":
        quit()

    # Once a word is chosen, launch the editing interface
    word_choices = [int(x) for x in word_choice.strip().split() if x.isdigit()]
    for word_choice in word_choices:
        if word_choice in set(range(len(dataset))):
            datapoint = dataset[word_choice]
            # If in lock/unlock mode, skip and simply toggle lock status
            if args.lock:
                datapoint = lock_datapoint(datapoint)
            else:
                datapoint = edit_datapoint(datapoint)

        # Propagate changes backwards to the original file
        dataset[word_choice] = datapoint
        if datatype == "Corpus":
            datafile.vocabulary = dataset
        else:
            datafile.down = dataset[: len(datafile.down)]
            datafile.across = dataset[len(datafile.down) :]
        datafile.to_json(open(args.input, "w"))
