import re
import os
from dotenv import load_dotenv

load_dotenv()

if os.environ.get("OPENAI_API_KEY") is None:
    from ollama import generate

    class LLM:
        def __init__(
            self,
            system="You are a helpful AI assistant.",
            model=os.environ.get("MODEL_UTILITY"),
            context_window_size=int(os.environ.get("CONTEXT_WINDOW_UTILITY")),
        ):
            self.system = system
            self.context = None
            self.model = model
            self.context_window_size = context_window_size

        # There seems to be a limit of input that Ollama can take
        # The Ollama server will crash if it gets too much
        def gen(self, prompt, context=None, limit=5000, max_len=150):
            if context is None:
                context = self.context
            response = generate(
                model=self.model,
                system=self.system,
                prompt=prompt[:limit],
                context=context,
                options={
                    "num_ctx": self.context_window_size,
                    "num_predict": max_len,
                },
            )
            self.context = response.context
            return response.response

        def clean_answer(
            self,
            prompt,
            min_len=10,
            max_len=50,
            letters_only=False,
        ):
            for _ in range(5):
                if prompt == "":
                    return ""
                response = generate(
                    model=self.model,
                    system="You are a helpful AI assistant and you put your answers in curly brackets {}. Keep your answers as short as possible.",
                    prompt=prompt,
                    options={
                        "num_ctx": self.context_window_size,
                        "num_predict": 2 + max_len,
                    },
                    context=self.context,
                )
                match = re.search(r"\{(.*?)\}", response.response)
                if match is not None:
                    text = match.group(1).strip()
                    if len(text) >= min_len:
                        # self.context = response.context
                        if letters_only:
                            return re.sub(r"[^\w]", "", text)
                        return text
            return response.response

        def summarize(self, text):
            return self.gen(
                "Please summarize the following text into a single paragraph:\n\n"
                + text
                + "\n\nPlease summarize the previous text into a single paragraph."
            )

        def give_clue(self, answer, pre_prompt=""):
            if pre_prompt is not None:
                self.gen(pre_prompt)
            return self.clean_answer(
                f"Please provide me a very short crossword clue where the answer is {answer}. Make sure that the answer does not appear in the clue."
            ).strip("\"'")

else:
    from openai import OpenAI

    class LLM:
        def __init__(self):
            self.client = OpenAI()

        def gen(self, prompt):
            return self.client.responses.create(
                model=os.environ.get("OPENAI_MODEL"),
                input=prompt,
            ).output_text

        def clean_answer(
            self,
            prompt,
            min_len=10,
            max_len=50,
            letters_only=False,
        ):
            response = self.client.responses.create(
                model=os.environ.get("OPENAI_MODEL"),
                instructions="You are a helpful AI assistant that keeps its answers as short as possible.",
                input=prompt,
            ).output_text
            return response

        def summarize(self, text):
            return self.gen(
                "Please summarize the following text into a single paragraph:\n\n"
                + text
                + "\n\nPlease summarize this text into a single paragraph."
            )

        def give_clue(self, answer, pre_prompt=""):
            # The pre-prompt is necessary here because the OpenAI API has no
            # way of using context. Pasting text at the front of the prompt
            # does something similar.
            return self.clean_answer(
                pre_prompt
                + f"Please provide me a very short crossword clue where the answer is {answer}. Make sure that the answer does not appear in the clue. Only provide the text of the clue."
            ).strip("\"'")
