"""Export multilingual-e5-small to ONNX (fp32 + int8) for the dense baseline D0.

Usage: python scripts/export_dense.py
Output: models/e5-small-onnx/model.onnx, model_int8.onnx
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from transformers import AutoModel, AutoTokenizer

from lipisetu import config
from lipisetu.dense.export_onnx import export_onnx, quantize_int8, file_size_mb


def main():
    hf_folder = os.path.join(config.MODEL_DIR, "e5-small")
    if not os.path.exists(os.path.join(hf_folder, "config.json")):
        print("downloading", config.DENSE_MODEL_NAME)
        AutoTokenizer.from_pretrained(config.DENSE_MODEL_NAME).save_pretrained(hf_folder)
        AutoModel.from_pretrained(config.DENSE_MODEL_NAME).save_pretrained(hf_folder)
    out_folder = os.path.join(config.MODEL_DIR, "e5-small-onnx")
    fp32_path = os.path.join(out_folder, "model.onnx")
    int8_path = os.path.join(out_folder, "model_int8.onnx")
    start = time.time()
    model = AutoModel.from_pretrained(hf_folder)
    export_onnx(model, fp32_path)
    quantize_int8(fp32_path, int8_path)
    AutoTokenizer.from_pretrained(hf_folder).save_pretrained(out_folder)
    print("fp32 %.1f MB, int8 %.1f MB, %.0fs" % (file_size_mb(fp32_path), file_size_mb(int8_path), time.time() - start))


if __name__ == "__main__":
    main()
