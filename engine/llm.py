import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

def load_local_llm(model_id: str):
    tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    mode = "fp16"

    # Try 4-bit (fast on GPU); fallback to fp16
    try:
        mdl = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            load_in_4bit=True,
            torch_dtype=torch.float16
        )
        mode = "4bit"
    except Exception:
        mdl = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.float16
        )
        mode = "fp16"

    gen = pipeline("text-generation", model=mdl, tokenizer=tok, device_map="auto")
    return gen, mode

def generate(gen, prompt: str, max_new_tokens: int = 220):
    out = gen(prompt, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.2, top_p=0.9, repetition_penalty=1.1)[0]["generated_text"]
    return out[len(prompt):].strip()
