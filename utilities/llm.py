import re
from ollama import generate

MODEL_UTILITY = "llama3.2:3b"#"llama3.1:8b"
CONTEXT_WINDOW_UTILITY = 2048#8192#65536


class LLM:
    def __init__(
        self,
        system="You are a helpful AI assistant.",
        model=MODEL_UTILITY,
        context_window_size=CONTEXT_WINDOW_UTILITY,
    ):
        self.system = system
        self.context = None
        self.model = model
        self.context_window_size = context_window_size

    def gen(self, prompt, context=None):
        if context is None:
            context = self.context
        response = generate(
            model=self.model,
            system=self.system,
            prompt=prompt,
            context=context,
            options={"num_ctx": self.context_window_size},
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
                options={"num_ctx": CONTEXT_WINDOW_UTILITY, "num_predict": 2 + max_len},
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
            + "\n\nPlease summarize this text into a single paragraph."
        )

    def give_clue(self, answer):
        return self.clean_answer(
            f"Please provide me a crossword clue where the answer is {answer}. Make sure that the answer does not appear in the clue."
        )
