import re
import os
from dotenv import load_dotenv

load_dotenv()

if os.environ.get("OPENAI_API_KEY") is None:
    from ollama import generate

    class LLM:
        def __init__(
            self,
            system="You are a helpful AI assistant. You only provide direct answers to questions.",
            model=os.environ.get("MODEL_UTILITY"),
            context_window_size=int(os.environ.get("CONTEXT_WINDOW_UTILITY")),
        ):
            self.system = system
            self.context = None
            self.model = model
            self.context_window_size = context_window_size
            # Reasoning models can be detected by their responses that start with <think>
            self.reasoning = False
            # But it's quicker to hardcode them in, rather than test at runtime
            if "qwq" in self.model or "deepseek-r" in self.model:
                self.reasoning = True

        # There seems to be a limit of input that Ollama can take
        # The Ollama server will crash if it gets too much
        def gen(self, prompt, context=None, limit=None, max_len=150):
            if context is None:
                context = self.context
            if limit is None:
                limit = self.context_window_size * 2
            # Remove limit from reasoning models
            if self.reasoning:
                max_len = None
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
            response = re.sub(
                r"<think>.*?</think>\n?", "", response.response, flags=re.DOTALL
            )
            return response

        def summarize(self, text, word):
            # Output as long as there are no newlines
            for _ in range(5):
                output = self.gen(
                    f"Please summarize the following text about {word} into a single paragraph, making sure to focus on {word}:\n\n"
                    + text
                    + f"\n\nPlease summarize the previous text about {word} into a single paragraph."
                )
                if "\n" not in output:
                    return output
                else:
                    self.gen(
                        "Your previous answer was not a single paragraph. Only return a single paragraph as the answer when I ask for a summary."
                    )
            return output

        @staticmethod
        def clue_cleanup(clue):
            output = (
                re.sub("\([^A-Za-z]+\)", " ", clue)
                .replace("\n", " ")
                .replace("  ", " ")
                .strip()
            )
            # Sometimes LLMs put the answer in quotes
            if output[0] == '"' and output[-1] == '"':
                output = output[1:-1]
            return output

        def give_clue(self, answer, category, pre_prompt=""):
            if pre_prompt is not None:
                self.gen(pre_prompt)
            for _ in range(5):
                output = self.clue_cleanup(
                    self.gen(
                        f"Please provide me a very short crossword clue where the answer is {answer} ({category}). Please respond only with a single sentence, the clue, and make sure not to include the answer in your response.",
                        max_len=30,
                    )
                )
                if answer.lower() not in output.lower():
                    return output
                else:
                    self.gen(
                        "You put the answer of the crossword clue in your previous answer. When answering me, please make sure not to include their answers in them. Answer with a single sentence, the clue."
                    )
            return output

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
