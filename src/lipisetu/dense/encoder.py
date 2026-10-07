"""Neural text encoder with onnxruntime (beyond the syllabus: dense retrieval).

Documents and queries become vectors in the same space; relevance = cosine
similarity (the vectors are already normalised, so cosine = dot product).
This is the vector space model from the lectures, but the dimensions are
learned by a multilingual model instead of being vocabulary terms.

e5 models need a prefix: "query: " for queries and "passage: " for passages.
"""
import numpy as np
import onnxruntime
from transformers import AutoTokenizer


class OnnxEncoder:
    def __init__(self, onnx_path, tokenizer_folder, id_map=None, threads=4):
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = threads
        self.session = onnxruntime.InferenceSession(onnx_path, options, providers=["CPUExecutionProvider"])
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_folder)
        # id_map is used by the vocabulary-pruned model: old token id -> new token id
        self.id_map = id_map

    def encode(self, texts, prefix, max_length=256, batch_size=32):
        """Encode a list of texts. Returns a float32 array of shape (len(texts), dim)."""
        # Sort by length so each batch has similar lengths (less padding = faster)
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        vectors = [None] * len(texts)
        for start in range(0, len(texts), batch_size):
            batch_ids = order[start:start + batch_size]
            batch_texts = []
            for i in batch_ids:
                batch_texts.append(prefix + texts[i])
            tokens = self.tokenizer(batch_texts, padding=True, truncation=True,
                                    max_length=max_length, return_tensors="np")
            input_ids = tokens["input_ids"].astype(np.int64)
            if self.id_map is not None:
                input_ids = self.id_map[input_ids]
            output = self.session.run(None, {"input_ids": input_ids,
                                             "attention_mask": tokens["attention_mask"].astype(np.int64)})[0]
            for row in range(len(batch_ids)):
                vectors[batch_ids[row]] = output[row]
        return np.array(vectors, dtype=np.float32)

    def encode_query(self, text):
        return self.encode([text], "query: ", max_length=64, batch_size=1)[0]
