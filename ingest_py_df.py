from utilities.llm import *
from utilities.corpus import *
import argparse
from pandas import DataFrame
import subprocess
from tqdm import tqdm


parser = argparse.ArgumentParser(
    prog="Ingest data on pandas DataFrame methods",
    description="This uses the built-in documentation to get information on the pandas DataFrame's methods.",
)

parser.add_argument(
    "output",
    type=str,
    help="The output JSON file.",
)

args = parser.parse_args()

corpus = Corpus()
# Getting all of the BeautifulSoup HTML parser methods
methods = [m for m in dir(DataFrame) if m[0].isalpha() and m[0].islower()]
for m in (pbar := tqdm(methods)):
    pbar.set_description(f"Collecting {m:<10}")
    corpus.add_word(
        Word(
            word=m,
            doc=subprocess.run(
                [
                    "python",
                    "-c",
                    f"import pydoc; from pandas import DataFrame; print(pydoc.plain(pydoc.render_doc(DataFrame.{m})));",
                ],
                capture_output=True,
                encoding="utf8",
            ).stdout,
            language="python",
            type="method",
            category=f"DataFrame method",
        )
    )

# Save the corpus to JSON
corpus.to_json(open(args.output, "w"))
