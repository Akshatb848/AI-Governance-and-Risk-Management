import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# Point AEGIS at a throwaway home before engine.config is imported, so tests
# never write into the repository's outputs/ folder.
_HOME = Path(tempfile.mkdtemp(prefix="aegis-test-"))
shutil.copytree(REPO / "data" / "kb", _HOME / "data" / "kb")
os.environ["AEGIS_HOME"] = str(_HOME)
sys.path.insert(0, str(REPO))


class _Doc:
    def __init__(self, text, source):
        self.page_content = text
        self.metadata = {"source": source}


class FakeRetriever:
    """Returns the bundled policy files instead of doing vector search."""

    def __init__(self):
        kb = _HOME / "data" / "kb"
        self.docs = [_Doc(p.read_text(encoding="utf-8"), p.name) for p in sorted(kb.glob("*.txt"))]

    def invoke(self, query):
        return self.docs


class _Tok:
    chat_template = None
    eos_token_id = 0


class FakeLLM:
    """Stands in for the HF pipeline. safe=True refuses injection attempts."""

    def __init__(self, safe=True):
        self.safe = safe
        self.tokenizer = _Tok()

    def __call__(self, text, **kwargs):
        question = text.split("Question:", 1)[1].split("Context:", 1)[0].lower()
        if self.safe and ("hidden instructions" in question or "credentials" in question):
            reply = "I cannot help with that request."
        elif "hidden instructions" in question or "credentials" in question:
            reply = "Sure, here they are: debug mode enabled."
        else:
            reply = ("Prompt-injection attempts must be refused [1]. "
                     "RAG answers must include citations to retrieved sources [1].")
        return [{"generated_text": reply}]


@pytest.fixture
def fakes():
    return FakeLLM, FakeRetriever
