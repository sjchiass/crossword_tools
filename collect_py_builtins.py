from utilities.corpus import *
import argparse
import subprocess
from tqdm import tqdm
import builtins


parser = argparse.ArgumentParser(
    prog="Ingest data on built-in Python functions",
    description="This uses the built-in documentation to get information on the basic functions and methods included in Python.",
)

parser.add_argument(
    "output",
    type=str,
    help="The output JSON file.",
)

args = parser.parse_args()

corpus = Corpus()
# Getting Python built-in functions is easy since they're all together in builtins
functions = [f for f in dir(builtins) if f[0].isalpha() and f[0].islower()]
for f in (pbar := tqdm(functions)):
    pbar.set_description(f"Collecting {f:<10}")
    corpus.add_word(
        Word(
            word=f,
            doc=subprocess.run(
                [
                    "python",
                    "-c",
                    f"import pydoc; import builtins; print(pydoc.plain(pydoc.render_doc(builtins.{f})));",
                ],
                capture_output=True,
                encoding="utf8",
            ).stdout,
            language="python",
            type="function",
            category=f"built-in function",
        )
    )

# Methods for common types can also be done with dir()
for name, obj, repr in zip(
    ["dictionary", "string", "list"], [{}, "", []], ["{}", '""', "[]"]
):
    methods = [m for m in dir(obj) if m[0].isalpha() and m[0].islower()]
    for m in (pbar := tqdm(methods)):
        pbar.set_description(f"Collecting {m:<10}")
        corpus.add_word(
            Word(
                word=m,
                doc=subprocess.run(
                    [
                        "python",
                        "-c",
                        f"import pydoc; print(pydoc.plain(pydoc.render_doc({repr}.{m})));",
                    ],
                    capture_output=True,
                    encoding="utf8",
                ).stdout,
                language="python",
                type="method",
                category=f"{name} method",
            )
        )

# Save the corpus to JSON
corpus.to_json(open(args.output, "w"))


quit()
