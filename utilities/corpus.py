import io
import json
import uuid
from dataclasses import dataclass, field


@dataclass
class Word:
    word: str
    imports: str = None
    invocation: str = None
    language: str = None
    type: str = None
    category: str = None
    url: str = None
    readme: str = None
    clue_en: str = None
    summary: str = None


@dataclass
class Corpus:
    id: str = field(default_factory=lambda: str(uuid.uuid1()))
    vocabulary: list[Word] = field(default_factory=lambda: list())

    def to_json(self, file: io.TextIOWrapper):
        json.dump(
            {"id": self.id, "vocabulary": [w.__dict__ for w in self.vocabulary]},
            file,
            indent=4,
        )

    def add_word(self, word: Word):
        self.vocabulary.append(word)


def corpus_from_json(file: io.TextIOWrapper):
    json_data = json.load(file)
    return Corpus(
        id=json_data["id"], vocabulary=[Word(**d) for d in json_data["vocabulary"]]
    )
