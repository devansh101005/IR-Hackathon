"""Train the SCD student query encoder, then prune its vocabulary and quantise it.

Uses ONLY the train split (dev is the test set). 10% of the train queries are
held out to check that the student really generalises to unseen queries.

Usage: python scripts/train_scd.py               (train, then export + prune)
       python scripts/train_scd.py --prune-only  (only redo the export + vocabulary pruning)
Output: models/scd-student/ (PyTorch), models/scd-student-onnx/ (int8, pruned int8, id map)
        results/scd_training.json (losses, held-out cosines, model sizes)
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from lipisetu import config
from lipisetu.data import read_topics, read_query_tsv
from lipisetu.text.romanize import romanize, casual_romanize, make_rng
from lipisetu.dense.scd import make_pairs, teacher_targets, train_epoch, evaluate_pairs
from lipisetu.dense.export_onnx import export_onnx, quantize_int8, file_size_mb
from lipisetu.dense.prune_vocab import collect_token_ids, build_id_map, prune_model

EPOCHS = 3
BATCH_SIZE = 32
LEARNING_RATE = 2e-5
CASUAL_SEEDS = [101, 102, 103, 104]
HELD_OUT_FRACTION = 0.1


def split_train(topics):
    qids = sorted(topics.keys())
    rng = random.Random(config.SEED)
    rng.shuffle(qids)
    cut = int(len(qids) * HELD_OUT_FRACTION)
    held_out = set(qids[:cut])
    train_part = {}
    held_part = {}
    for qid in topics:
        if qid in held_out:
            held_part[qid] = topics[qid]
        else:
            train_part[qid] = topics[qid]
    return train_part, held_part


def casual_versions(topics):
    versions = []
    for seed in CASUAL_SEEDS:
        rng = make_rng(seed)
        version = {}
        for qid in sorted(topics.keys()):
            version[qid] = casual_romanize(topics[qid], rng, 0.3)
        versions.append(version)
    return versions


def roman_only_pairs(pairs, topics):
    """Pairs whose input is not the Devanagari query itself."""
    result = []
    for text, qid in pairs:
        if text != topics[qid]:
            result.append((text, qid))
    return result


def export_and_prune(student_folder, report, topics, f2, versions):
    """Export the student (full and pruned vocabulary) to ONNX fp32 and int8."""
    tokenizer = AutoTokenizer.from_pretrained(student_folder)
    student = AutoModel.from_pretrained(student_folder)
    onnx_folder = os.path.join(config.MODEL_DIR, "scd-student-onnx")
    full_fp32 = os.path.join(onnx_folder, "model.onnx")
    full_int8 = os.path.join(onnx_folder, "model_int8.onnx")
    export_onnx(student, full_fp32)
    quantize_int8(full_fp32, full_int8)
    tokenizer.save_pretrained(onnx_folder)

    # Vocabulary pruning: keep the token ids used by the corpus, the corpus written in
    # Roman script (my romaniser), and the TRAIN queries in every form. No dev data is used.
    texts = []
    with open(config.CORPUS_FILE, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            texts.append(doc["title"] + ". " + doc["text"])
    roman_texts = []
    for text in texts:
        roman_texts.append(romanize(text))
    query_texts = list(topics.values()) + list(f2.values())
    for version in versions:
        query_texts.extend(version.values())
    kept = collect_token_ids(tokenizer, texts)
    kept = kept | collect_token_ids(tokenizer, roman_texts)
    kept = kept | collect_token_ids(tokenizer, ["query: " + t for t in query_texts])
    kept.update(tokenizer.all_special_ids)
    id_map, kept_ids = build_id_map(kept, len(tokenizer), tokenizer.unk_token_id)
    np.save(os.path.join(onnx_folder, "id_map.npy"), id_map)
    pruned = prune_model(AutoModel.from_pretrained(student_folder), kept_ids)
    pruned_fp32 = os.path.join(onnx_folder, "model_pruned.onnx")
    pruned_int8 = os.path.join(onnx_folder, "model_pruned_int8.onnx")
    export_onnx(pruned, pruned_fp32)
    quantize_int8(pruned_fp32, pruned_int8)

    report["vocab_full"] = len(tokenizer)
    report["vocab_pruned"] = len(kept_ids)
    report["params_full"] = int(sum(p.numel() for p in student.parameters()))
    report["params_pruned"] = int(sum(p.numel() for p in pruned.parameters()))
    report["size_mb"] = {
        "full_fp32": file_size_mb(full_fp32), "full_int8": file_size_mb(full_int8),
        "pruned_fp32": file_size_mb(pruned_fp32), "pruned_int8": file_size_mb(pruned_int8),
    }
    return report


def main():
    prune_only = "--prune-only" in sys.argv
    torch.manual_seed(config.SEED)
    torch.set_num_threads(int(os.environ.get("TRAIN_THREADS", "4")))
    start = time.time()
    teacher_folder = os.path.join(config.MODEL_DIR, "e5-small")
    student_folder = os.path.join(config.MODEL_DIR, "scd-student")
    report_path = os.path.join(config.RESULTS_DIR, "scd_training.json")
    topics = read_topics(config.TOPICS_TRAIN)
    f2 = read_query_tsv(os.path.join(config.QUERY_DIR, "train_F2.tsv"))
    versions = casual_versions(topics)

    if prune_only:
        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)
    else:
        tokenizer = AutoTokenizer.from_pretrained(teacher_folder)
        teacher = AutoModel.from_pretrained(teacher_folder)
        student = AutoModel.from_pretrained(teacher_folder)
        for parameter in teacher.parameters():
            parameter.requires_grad = False
        train_topics, held_topics = split_train(topics)
        train_pairs = make_pairs(train_topics, [f2], versions)
        held_pairs = roman_only_pairs(make_pairs(held_topics, [f2], versions[:1]), topics)
        print("train pairs:", len(train_pairs), " held-out roman pairs:", len(held_pairs))
        targets = teacher_targets(teacher, tokenizer, topics)
        report = {"held_out_cosine_before": evaluate_pairs(student, tokenizer, held_pairs, targets)}
        print("held-out cosine before training: %.4f" % report["held_out_cosine_before"])
        optimizer = torch.optim.AdamW(student.parameters(), lr=LEARNING_RATE)
        report["epochs"] = []
        for epoch in range(EPOCHS):
            loss = train_epoch(student, tokenizer, train_pairs, targets, optimizer, BATCH_SIZE, config.SEED + epoch)
            cosine = evaluate_pairs(student, tokenizer, held_pairs, targets)
            print("epoch %d  train loss %.4f  held-out cosine %.4f" % (epoch + 1, loss, cosine))
            report["epochs"].append({"epoch": epoch + 1, "train_loss": loss, "held_out_cosine": cosine})
        student.save_pretrained(student_folder)
        tokenizer.save_pretrained(student_folder)
        report["train_seconds"] = time.time() - start

    report = export_and_prune(student_folder, report, topics, f2, versions)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
