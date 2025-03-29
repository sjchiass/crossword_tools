# Setup

`conda create -n crossword -c conda-forge python=3.11 python-slugify levenshtein pillow jinja2 bs4 requests tqdm python-dotenv`

`conda activate crossword`


For ollama:

`pip install ollama`

For OpenAI:

`pip install openai`

# Overview

## Collecting data

I've created a few scripts to help you build cross word banks:

  * [./ingest_r_dplyr_tidyr.py](./ingest_r_dplyr_tidyr.py) for getting all of the functions in the `dplyr` and `tidyr` R packages
  * [./ingest_r_tidyverse.py](./ingest_r_tidyverse.py) for getting all of the packages in the tidyverse
  * [./ingest_py_builtins.py](./ingest_py_builtins.py) for getting built-in Python functions, string methods, list methods and dictionary methods
  * [./ingest_py_stlib.py](./ingest_py_stlib.py) for getting all of the functions in the Python standard library
  * [./ingest_py_df.py](./ingest_py_df.py) an example of getting all methods pandas's DataFrame class (you will have to install pandas before being able to use this)

These use a mixture of online data and built-in documentation.

## Creating summaries and clues automatically

Once data is collected, you can use LLMs to summarize each word's documentation. The summaries should be fairly reliable and only a few sentences long, making them a useful quick refresher on what each word means.

Generating crossword requires a decent amount of words and some trial and error. Clues are of higher quality when the LLM has a chance to read documentation first. You also can't use the mini models because their outputs are usually incoherent. With all that said, generating a crossword with clues using `gpt-4o` should cost at least 25 cents. Please let me know of your experiences.

If you have a GPU, generating clues with Ollama is free. Without a GPU it is pretty slow.

## Editing data

Once you've generated data, you can use the `edit_data.py` script to tweak values. Use the `--lock` flag to make it easier to lock words so that they aren't used in crosswords.

# Background

This is a very rough project. It makes crosswords with a modified script from here: https://github.com/sealhuang/pycrossword For rendering HTML crosswords it takes elements from here: https://www.sitepoint.com/how-built-pure-css-crossword-puzzle/

The general idea:

  - You supply `generate_clues.py` with a word list.
  - You supply `crossword_puzzle.py` the JSON data.
  - You use either `render_png.py` or `render_html.py`, giving them a background image, some text and other details.
