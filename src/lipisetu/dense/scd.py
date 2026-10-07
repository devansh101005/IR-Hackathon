"""Script-Consistency Distillation (SCD): helpers for training the student query encoder.

Idea (based on Reimers & Gurevych, EMNLP 2020, which used it for translations):
    teacher = the original e5-small, frozen
    student = a copy of e5-small that I train
    For every TRAIN query q written in Devanagari, and every Roman version v of it:
        loss = 1 - cosine( student(v), teacher(q) )
    plus the Devanagari query itself, so the student doesn't forget it:
        loss = 1 - cosine( student(q), teacher(q) )
After training, a Roman query lands where its Devanagari version lands, so it
finds the same passages. The passage vectors don't change at all (they come
from the teacher), so I don't need to re-encode the corpus.
"""
import random

import torch

from lipisetu.dense.export_onnx import PooledEncoder


def make_pairs(train_topics, forms, casual_versions):
    """List of (input text, qid). The target for each pair is teacher(Devanagari of qid)."""
    pairs = []
    for qid in train_topics:
        pairs.append((train_topics[qid], qid))
        for form in forms:
            if qid in form:
                pairs.append((form[qid], qid))
        for version in casual_versions:
            if qid in version:
                pairs.append((version[qid], qid))
    return pairs


def encode_with(model, tokenizer, texts, max_length=64):
    """Pooled, normalised embeddings from a PyTorch model (keeps gradients if training)."""
    tokens = tokenizer(["query: " + t for t in texts], padding=True, truncation=True,
                       max_length=max_length, return_tensors="pt")
    return PooledEncoder(model)(tokens["input_ids"], tokens["attention_mask"])


def teacher_targets(teacher, tokenizer, topics, batch_size=64):
    """Teacher vector of the Devanagari query, for every qid."""
    targets = {}
    qids = list(topics.keys())
    teacher.eval()
    with torch.no_grad():
        for start in range(0, len(qids), batch_size):
            batch_qids = qids[start:start + batch_size]
            vectors = encode_with(teacher, tokenizer, [topics[q] for q in batch_qids])
            for i in range(len(batch_qids)):
                targets[batch_qids[i]] = vectors[i]
    return targets


def consistency_loss(student_vectors, target_vectors):
    """Average of (1 - cosine). Vectors are already normalised, so cosine = dot product."""
    cosines = (student_vectors * target_vectors).sum(dim=1)
    return (1.0 - cosines).mean()


def train_epoch(student, tokenizer, pairs, targets, optimizer, batch_size, seed):
    student.train()
    rng = random.Random(seed)
    order = list(range(len(pairs)))
    rng.shuffle(order)
    total = 0.0
    steps = 0
    for start in range(0, len(order), batch_size):
        batch = [pairs[i] for i in order[start:start + batch_size]]
        texts = [text for text, _ in batch]
        target = torch.stack([targets[qid] for _, qid in batch])
        loss = consistency_loss(encode_with(student, tokenizer, texts), target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total += loss.item()
        steps += 1
        if steps % 50 == 0:
            print("    step %d  loss %.4f" % (steps, total / steps), flush=True)
    return total / max(steps, 1)


def evaluate_pairs(model, tokenizer, pairs, targets, batch_size=64):
    """Average cosine between model(text) and the teacher's Devanagari vector."""
    model.eval()
    cosines = []
    with torch.no_grad():
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start:start + batch_size]
            vectors = encode_with(model, tokenizer, [text for text, _ in batch])
            target = torch.stack([targets[qid] for _, qid in batch])
            cosines.extend((vectors * target).sum(dim=1).tolist())
    return sum(cosines) / max(len(cosines), 1)
