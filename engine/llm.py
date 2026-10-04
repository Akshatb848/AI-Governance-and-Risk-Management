"""Local open-weights LLM used by the RAG audit agent.

Loads in 4-bit on a CUDA GPU when bitsandbytes is available, fp16 on GPU
otherwise, and fp32 on CPU. Generation is greedy so audit runs are repeatable.
"""


def load_local_llm(model_id: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)

    if torch.cuda.is_available():
        try:
            from transformers import BitsAndBytesConfig
            import bitsandbytes  # noqa: F401  (only to check it is installed)

            quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
            mdl = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", quantization_config=quant)
            mode = "cuda-4bit"
        except Exception:
            mdl = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype=torch.float16)
            mode = "cuda-fp16"
    else:
        mdl = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
        mode = "cpu-fp32"

    mdl.generation_config.max_length = None  # length is set per call via max_new_tokens
    gen = pipeline("text-generation", model=mdl, tokenizer=tok)
    return gen, mode


def generate(gen, prompt: str, max_new_tokens: int = 220) -> str:
    """Run one prompt through the model's chat template and return only the reply."""
    tok = gen.tokenizer
    if getattr(tok, "chat_template", None):
        text = tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True)
    else:
        text = prompt
    out = gen(text, max_new_tokens=max_new_tokens, do_sample=False, return_full_text=False,
              pad_token_id=tok.eos_token_id)
    return out[0]["generated_text"].strip()
