import io
import re
import json
import uuid
from dataclasses import dataclass, field, fields, replace


@dataclass(kw_only=True)
class Word:
    word: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc: str = None
    language: str = None
    type: str = None
    category: str = None
    summary: str = None
    locked: bool = False

    def get_fields(self):
        return fields(self)

    def get_value(self, field_name: str):
        return self.__dict__[field_name]

    # This method could check typing of new_value
    def replace_value(self, field_name: str, new_value: any):
        return replace(self, **{field_name: new_value})


@dataclass
class Corpus:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vocabulary: list[Word] = field(default_factory=lambda: list())

    def validate(self):
        for word in self.vocabulary:
            word.word = re.sub("[^\w\-_]", "", word.word.upper())

    def to_json(self, file: io.TextIOWrapper):
        self.validate()
        json.dump(
            {
                "filetype": "Corpus",
                "id": self.id,
                "vocabulary": [w.__dict__ for w in self.vocabulary],
            },
            file,
            indent=4,
        )

    def add_word(self, word: Word):
        self.vocabulary.append(word)

    def get_fields(self):
        return fields(self)


@dataclass
class CrosswordCell:
    x: int
    y: int
    final_answer: bool = False
    letter: str = None
    number: str = None


@dataclass
class CrosswordClue(Word):
    x: int
    y: int
    index: int
    number: str
    clue_en: str = None
    clue_fr: str = None

    def get_fields(self):
        return fields(self)


@dataclass
class Crossword:
    parent_id: str
    rows: int
    cols: int
    grid: list[list[CrosswordCell]]
    across: list[CrosswordClue]
    down: list[CrosswordClue]

    def to_json(self, file: io.TextIOWrapper):
        json.dump(
            {
                "filetype": "Crossword",
                "parent_id": self.parent_id,
                "rows": self.rows,
                "cols": self.cols,
                "grid": [[cell.__dict__ for cell in row] for row in self.grid],
                "across": [clue.__dict__ for clue in self.across],
                "down": [clue.__dict__ for clue in self.down],
            },
            file,
            indent=4,
        )

    def get_fields(self):
        return fields(self)


#
# Import functions
#


def corpus_from_dict(data: dict):
    return Corpus(id=data["id"], vocabulary=[Word(**d) for d in data["vocabulary"]])


def crossword_from_dict(data: dict):
    return Crossword(
        parent_id=data["parent_id"],
        rows=data["rows"],
        cols=data["cols"],
        grid=[[CrosswordCell(**cell) for cell in row] for row in data["grid"]],
        across=[CrosswordClue(**clue) for clue in data["across"]],
        down=[CrosswordClue(**clue) for clue in data["down"]],
    )


def corpus_from_json(file: io.TextIOWrapper):
    json_data = json.load(file)
    if "filetype" in json_data.keys() and json_data["filetype"] == "Corpus":
        return corpus_from_dict(json_data)
    else:
        raise ValueError(
            "JSON input file does not have 'corpus' value for 'filetype' key"
        )


def crossword_from_json(file: io.TextIOWrapper):
    json_data = json.load(file)
    if "filetype" in json_data.keys() and json_data["filetype"] == "Crossword":
        return crossword_from_dict(json_data)
    else:
        raise ValueError(
            "JSON input file does not have 'Crossword' value for 'filetype' key"
        )


def infer_from_json(file: io.TextIOWrapper):
    json_data = json.load(file)
    if "filetype" in json_data.keys() and json_data["filetype"] == "Corpus":
        return corpus_from_dict(json_data), "Corpus"
    elif "filetype" in json_data.keys() and json_data["filetype"] == "Crossword":
        return crossword_from_dict(json_data), "Crossword"
    else:
        raise ValueError(
            "JSON input file has neither a 'Corpus' nor 'Crossword' value for 'filetype' key"
        )
