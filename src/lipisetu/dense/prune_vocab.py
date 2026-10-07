"""Vocabulary pruning for the multilingual encoder (Abdaoui et al. 2020, "Load What You Need").

multilingual-e5-small has a vocabulary of 250,002 tokens for ~100 languages,
and the embedding table alone holds 96M of its 118M parameters. My corpus and
queries only use a small part of it. So I keep only the token ids that appear
in the corpus and in the TRAIN queries, and build a smaller embedding table.

At search time an id map turns the original tokenizer's ids into the new ids
(unknown ids go to <unk>), so I can keep using the original tokenizer.
"""
import numpy as np
import torch


def collect_token_ids(tokenizer, texts, max_length=256, batch_size=1000):
    """All token ids used by a list of texts."""
    used = set()
    for start in range(0, len(texts), batch_size):
        batch = tokenizer(texts[start:start + batch_size], truncation=True, max_length=max_length)
        for ids in batch["input_ids"]:
            used.update(ids)
    return used


def build_id_map(kept_ids, vocab_size, unk_old_id):
    """Array: old id -> new id. Ids that were dropped map to the new id of <unk>."""
    kept_ids = sorted(kept_ids)
    id_map = np.zeros(vocab_size, dtype=np.int64)
    new_position = {}
    for new_id in range(len(kept_ids)):
        new_position[kept_ids[new_id]] = new_id
    unk_new = new_position[unk_old_id]
    for old_id in range(vocab_size):
        id_map[old_id] = new_position.get(old_id, unk_new)
    return id_map, kept_ids


def prune_model(model, kept_ids):
    """Replace the word embedding table with only the kept rows."""
    old_table = model.embeddings.word_embeddings.weight.data
    new_table = old_table[torch.tensor(kept_ids, dtype=torch.long)].clone()
    new_embedding = torch.nn.Embedding(len(kept_ids), old_table.shape[1])
    new_embedding.weight.data = new_table
    model.embeddings.word_embeddings = new_embedding
    model.config.vocab_size = len(kept_ids)
    return model
