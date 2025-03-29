# modified from: https://github.com/sealhuang/pycrossword/blob/main/crossword_puzzle.py
import random
from utilities import corpus as corpus_module
import re
import time
import string
from copy import copy as duplicate
import json
from copy import deepcopy
import argparse

parser = argparse.ArgumentParser(
    prog="Crosswod generator",
    description="Using an input JSON file, generate a crossword.",
)

parser.add_argument(
    "input",
    type=str,
    help="The input JSON file.",
)

parser.add_argument(
    "output",
    type=str,
    help="The output JSON file.",
)

parser.add_argument(
    "height",
    type=int,
    help="The crossword height in number of rows.",
)

parser.add_argument(
    "width",
    type=int,
    help="The crossword width in numbers of columns.",
)

parser.add_argument(
    "--lock",
    action="store_true",
    help="Whether to lock the words used right away. They won't be used to generate crosswords in the future.",
)

parser.add_argument(
    "--min_len",
    type=int,
    default=1,
    help="The minimum amount of characters a word needs before it is used.",
)

parser.add_argument(
    "--max_len",
    type=int,
    default=100,
    help="The maximum amount of characters a word can have before it is omitted.",
)

args = parser.parse_args()


class Crossword(object):
    def __init__(self, cols, rows, empty="-", maxloops=2000, available_words=[]):
        self.cols = cols
        self.rows = rows
        self.empty = empty
        self.maxloops = maxloops
        self.available_words = available_words
        self.randomize_word_list()
        self.current_word_list = []
        self.clear_grid()
        self.debug = 0

    def clear_grid(self):
        """Initialize grid and fill with empty character."""
        self.grid = []
        for i in range(self.rows):
            ea_row = []
            for j in range(self.cols):
                ea_row.append(self.empty)
            self.grid.append(ea_row)

    def randomize_word_list(self):
        """Reset words and sort by length."""
        temp_list = []
        for word in self.available_words:
            if isinstance(word, Word):
                temp_list.append(Word(word_obj=word.obj))
            else:
                temp_list.append(Word(word_obj=word))
        # randomize word list
        random.shuffle(temp_list)
        # sort by length
        temp_list.sort(key=lambda i: len(i.word), reverse=True)
        self.available_words = temp_list

    def compute_crossword(self, time_permitted=1.00, spins=2):
        copy = Crossword(
            self.cols, self.rows, self.empty, self.maxloops, self.available_words
        )

        count = 0
        time_permitted = float(time_permitted)
        start_full = float(time.time())

        # only run for x seconds
        while (float(time.time()) - start_full) < time_permitted or count == 0:
            self.debug += 1
            copy.randomize_word_list()
            copy.current_word_list = []
            copy.clear_grid()

            x = 0
            # spins; 2 seems to be plenty
            while x < spins:
                for word in copy.available_words:
                    if word not in copy.current_word_list:
                        copy.fit_and_add(word)
                x += 1
            # print(copy.solution())
            # print(len(copy.current_word_list), len(self.current_word_list), self.debug)
            # buffer the best crossword by comparing placed words
            if len(copy.current_word_list) > len(self.current_word_list):
                self.current_word_list = copy.current_word_list
                self.grid = copy.grid
            count += 1
        return

    def suggest_coord(self, word):
        # count = 0
        coordlist = []
        glc = -1

        # cycle through letters in word
        for given_letter in word.word:
            glc += 1
            rowc = 0
            # cycle through rows
            for row in self.grid:
                rowc += 1
                colc = 0
                # cycle through letters in rows
                for cell in row:
                    colc += 1
                    # check match letter in word to letters in row
                    if given_letter == cell:
                        # suggest vertical placement
                        try:
                            # make sure we're not suggesting a starting point off the grid
                            if rowc - glc > 0:
                                # make sure word doesn't go off of grid
                                if ((rowc - glc) + word.length) <= self.rows:
                                    coordlist.append(
                                        [colc, rowc - glc, 1, colc + (rowc - glc), 0]
                                    )
                        except:
                            pass

                        # suggest horizontal placement
                        try:
                            # make sure we're not suggesting a starting point off the grid
                            if colc - glc > 0:
                                # make sure word doesn't go off of grid
                                if ((colc - glc) + word.length) <= self.cols:
                                    coordlist.append(
                                        [colc - glc, rowc, 0, rowc + (colc - glc), 0]
                                    )
                        except:
                            pass

        # example: coordlist[0] = [col, row, vertical, col + row, score]
        # print(word.word)
        # print(coordlist)
        new_coordlist = self.sort_coordlist(coordlist, word)
        # print(new_coordlist)

        return new_coordlist

    def sort_coordlist(self, coordlist, word):
        """Give each coordinate a score, then sort."""
        new_coordlist = []
        for coord in coordlist:
            col, row, vertical = coord[0], coord[1], coord[2]
            # checking scores
            coord[4] = self.check_fit_score(col, row, vertical, word)
            # 0 scores are filtered
            if coord[4]:
                new_coordlist.append(coord)
        # randomize coord list; why not?
        random.shuffle(new_coordlist)
        # put the best scores first
        new_coordlist.sort(key=lambda i: i[4], reverse=True)
        return new_coordlist

    def fit_and_add(self, word):
        """Doesn't really check fit except for the first word;
        otherwise just adds if score is good.
        """
        fit = False
        count = 0
        coordlist = self.suggest_coord(word)

        while not fit and count < self.maxloops:
            # this is the first word: the seed
            if len(self.current_word_list) == 0:
                # top left seed of longest word yields best results (maybe override)
                vertical, col, row = random.randrange(0, 2), 1, 1

                """ 
                # optional center seed method, slower and less keyword placement
                if vertical:
                    col = int(round((self.cols+1)/2, 0))
                    row = int(round((self.rows+1)/2, 0)) - int(round((word.length+1)/2, 0))
                else:
                    col = int(round((self.cols+1)/2, 0)) - int(round((word.length+1)/2, 0))
                    row = int(round((self.rows+1)/2, 0))
                # completely random seed method
                col = random.randrange(1, self.cols + 1)
                row = random.randrange(1, self.rows + 1)
                """

                if self.check_fit_score(col, row, vertical, word):
                    fit = True
                    self.set_word(col, row, vertical, word, force=True)

            # a subsquent words have scores calculated
            else:
                try:
                    col, row, vertical = (
                        coordlist[count][0],
                        coordlist[count][1],
                        coordlist[count][2],
                    )
                # no more cordinates, stop trying to fit
                except IndexError:
                    return

                # already filtered these out, but double check
                if coordlist[count][4]:
                    fit = True
                    self.set_word(col, row, vertical, word, force=True)

            count += 1

        return

    def check_fit_score(self, col, row, vertical, word):
        """Return score: 0 signifies no fit, 1 means a fit, 2+ means a cross.
        The more crosses the better.
        """
        if col < 1 or row < 1:
            return 0

        # give score a standard value of 1, will override with 0 if collisions detected
        count, score = 1, 1
        for letter in word.word:
            try:
                active_cell = self.get_cell(col, row)
            except IndexError:
                return 0

            if active_cell == self.empty or active_cell == letter:
                pass
            else:
                return 0

            if active_cell == letter:
                score += 1

            if vertical:
                # check surroundings
                if active_cell != letter:  # don't check surroundings if cross point
                    if not self.check_if_cell_clear(col + 1, row):  # check right cell
                        return 0

                    if not self.check_if_cell_clear(col - 1, row):  # check left cell
                        return 0

                if count == 1:  # check top cell only on first letter
                    if not self.check_if_cell_clear(col, row - 1):
                        return 0

                if count == len(word.word):  # check bottom cell only on last letter
                    if not self.check_if_cell_clear(col, row + 1):
                        return 0
            else:  # else horizontal
                # check surroundings
                if active_cell != letter:  # don't check surroundings if cross point
                    if not self.check_if_cell_clear(col, row - 1):  # check top cell
                        return 0

                    if not self.check_if_cell_clear(col, row + 1):  # check bottom cell
                        return 0

                if count == 1:  # check left cell only on first letter
                    if not self.check_if_cell_clear(col - 1, row):
                        return 0

                if count == len(word.word):  # check right cell only on last letter
                    if not self.check_if_cell_clear(col + 1, row):
                        return 0

            if vertical:  # progress to next letter and position
                row += 1
            else:  # else horizontal
                col += 1

            count += 1

        return score

    def set_word(self, col, row, vertical, word, force=False):
        """Set word in the grid, and adds word to word list."""
        if force:
            word.col = col
            word.row = row
            word.vertical = vertical
            self.current_word_list.append(word)

            for letter in word.word:
                self.set_cell(col, row, letter)
                if vertical:
                    row += 1
                else:
                    col += 1

        return

    def set_cell(self, col, row, value):
        self.grid[row - 1][col - 1] = value

    def get_cell(self, col, row):
        return self.grid[row - 1][col - 1]

    def check_if_cell_clear(self, col, row):
        try:
            cell = self.get_cell(col, row)
            if cell == self.empty:
                return True
        except IndexError:
            pass
        return False

    def solution(self):
        """Return solution grid."""
        outStr = ""
        for r in range(self.rows):
            for c in self.grid[r]:
                outStr += "%s " % c
            outStr += "\n"
        return outStr

    def word_find(self):
        """Return solution grid."""
        outStr = ""
        for r in range(self.rows):
            for c in self.grid[r]:
                if c == self.empty:
                    outStr += (
                        "%s "
                        % string.ascii_lowercase[
                            random.randint(0, len(string.ascii_lowercase) - 1)
                        ]
                    )
                else:
                    outStr += "%s " % c
            outStr += "\n"
        return outStr

    def order_number_words(self):
        """Orders words and applies numbering system to them."""
        # Change: the sorting should make it so the numbering goes left-right first, then to the next row.
        self.current_word_list.sort(key=lambda i: (i.col + self.cols * i.row))
        count, icount = 1, 1
        for word in self.current_word_list:
            word.number = count
            if icount < len(self.current_word_list):
                if (
                    word.col == self.current_word_list[icount].col
                    and word.row == self.current_word_list[icount].row
                ):
                    pass
                else:
                    count += 1
            icount += 1

    def display(self, order=True):
        """Return (and order/number wordlist) the grid minus the words adding the numbers"""
        outStr = ""
        if order:
            self.order_number_words()

        # Change: this needs to be .copy(), otherwise copy is just a refenence to self
        copy = deepcopy(self)

        for word in self.current_word_list:
            copy.set_cell(word.col, word.row, word.number)

        for r in range(copy.rows):
            for c in copy.grid[r]:
                outStr += f"{c:<2}"
            outStr += "\n"

        outStr = re.sub(r"[a-z]", " ", outStr)
        return outStr

    def json_dump(self, outfile, id):
        parent_id = id
        rows = self.rows
        cols = self.cols
        grid = [
            [corpus_module.CrosswordCell(x=x, y=y) for y in range(self.rows)]
            for x in range(self.cols)
        ]
        across = []
        down = []

        for y in range(self.rows):
            for x, c in enumerate(self.grid[y]):
                grid[x][y].final_answer = False
                if c != "-":
                    grid[x][y].letter = c
                else:
                    grid[x][y].letter = None

        # Get numbers
        copy = deepcopy(self)
        for word in self.current_word_list:
            copy.set_cell(word.col, word.row, word.number)
        for y, r in enumerate(range(copy.rows)):
            for x, c in enumerate(copy.grid[r]):
                if isinstance(c, int):
                    grid[x][y].number = str(c)
                else:
                    grid[x][y].number = None

        # Get words
        for index, word in enumerate(
            sorted(self.current_word_list, key=lambda x: x.down_across())
        ):
            if word.down_across() == "across":
                across.append(
                    corpus_module.CrosswordClue(
                        x=word.col,
                        y=word.row,
                        index=index,
                        number=word.number,
                        **word.obj.__dict__,
                    )
                )
            elif word.down_across() == "down":
                down.append(
                    corpus_module.CrosswordClue(
                        x=word.col,
                        y=word.row,
                        index=index,
                        number=word.number,
                        **word.obj.__dict__,
                    )
                )

        crossword_obj = corpus_module.Crossword(
            parent_id=parent_id,
            cols=cols,
            rows=rows,
            grid=grid,
            across=across,
            down=down,
        )

        crossword_obj.to_json(open(outfile, "w", encoding="utf-8"))

    def word_bank(self):
        outStr = ""
        temp_list = duplicate(self.current_word_list)
        # randomize word list
        random.shuffle(temp_list)
        for word in temp_list:
            outStr += "%s\n" % word.word
        return outStr

    def legend(self):
        """Must order first."""
        outStr = ""
        for word in sorted(self.current_word_list, key=lambda x: x.down_across()):
            outStr += "%d. (%d,%d) %s %s\n" % (
                word.number,
                word.col,
                word.row,
                word.down_across(),
                word.word,
            )
        return outStr


class Word(object):
    def __init__(self, word_obj=None):
        self.word = re.sub("[^\w\-_]", "", word_obj.word.upper())
        self.obj = word_obj
        self.length = len(self.word)
        # the below are set when placed on board
        self.row = None
        self.col = None
        self.vertical = None
        self.number = None

    def down_across(self):
        """Return down or across."""
        if self.vertical:
            return "down"
        else:
            return "across"

    def __repr__(self):
        return self.word


corpus = corpus_module.corpus_from_json(open(args.input, "r"))

TIME_LIMIT = 5

# The algorithm doesn't accept duplicate words
word_list = {
    word.word: word
    for word in corpus.vocabulary
    if word.locked is False
    and len(word.word) >= args.min_len
    and len(word.word) <= args.max_len
}
word_list = word_list.values()

a = Crossword(args.width, args.height, "-", 1000000, word_list)
a.compute_crossword(TIME_LIMIT)
print(a.word_bank())
print(a.solution())
print(a.word_find())
print(a.display())
print(a.legend())
print(len(a.current_word_list), "out of", len(word_list))

a.json_dump(args.output, id=corpus.id)
