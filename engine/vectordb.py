import os
import glob

from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_chroma import Chroma
except ImportError:  # older installs
    from langchain_community.vectorstores import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:  # older installs
    from langchain_community.embeddings import HuggingFaceEmbeddings

from .config import KB_DIR, DEFAULT_EMBED_MODEL
from .kb import ensure_kb


def build_retriever(chroma_dir: str, rebuild: bool = False, k: int = 4):
    """Index the policy knowledge base (data/kb/*.txt) into a Chroma store and
    return a retriever. Each run gets its own store under its run folder."""
    ensure_kb()

    kb_files = sorted(glob.glob(os.path.join(KB_DIR, "*.txt")))
    if not kb_files:
        raise ValueError(f"No KB .txt files found in {KB_DIR}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    texts, metas = [], []
    for path in kb_files:
        with open(path, "r", encoding="utf-8") as f:
            for chunk in splitter.split_text(f.read()):
                texts.append(chunk)
                metas.append({"source": os.path.basename(path)})

    os.makedirs(chroma_dir, exist_ok=True)
    if rebuild:
        for fn in os.listdir(chroma_dir):
            try:
                os.remove(os.path.join(chroma_dir, fn))
            except OSError:
                pass

    emb = HuggingFaceEmbeddings(model_name=DEFAULT_EMBED_MODEL)
    vectordb = Chroma.from_texts(texts=texts, embedding=emb, metadatas=metas, persist_directory=chroma_dir)
    return vectordb.as_retriever(search_kwargs={"k": k})
