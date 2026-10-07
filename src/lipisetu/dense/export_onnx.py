"""Export an encoder to ONNX and quantise it to int8 (beyond the syllabus: model compression).

The exported graph does the whole job: token ids -> transformer -> mean pooling
-> L2 normalisation. So at search time I only need onnxruntime + the tokenizer.

Dynamic int8 quantisation stores the weights of the big matrix multiplications
(and optionally the embedding table) as 8-bit integers instead of 32-bit floats:
about 4x smaller, and faster on a CPU.
"""
import os

import torch
from onnxruntime.quantization import quantize_dynamic, QuantType


class PooledEncoder(torch.nn.Module):
    """Wrap a Hugging Face encoder so it returns one normalised vector per text."""

    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, input_ids, attention_mask):
        output = self.model(input_ids=input_ids, attention_mask=attention_mask)
        hidden = output.last_hidden_state
        mask = attention_mask.unsqueeze(-1).to(hidden.dtype)
        summed = (hidden * mask).sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1e-9)
        pooled = summed / counts
        return torch.nn.functional.normalize(pooled, p=2, dim=1)


def export_onnx(model, onnx_path):
    """Export a PyTorch encoder to ONNX with a dynamic batch size and length."""
    model.eval()
    wrapper = PooledEncoder(model)
    dummy_ids = torch.ones((2, 16), dtype=torch.long)
    dummy_mask = torch.ones((2, 16), dtype=torch.long)
    os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
    torch.onnx.export(
        wrapper,
        (dummy_ids, dummy_mask),
        onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["embedding"],
        dynamic_axes={"input_ids": {0: "batch", 1: "length"},
                      "attention_mask": {0: "batch", 1: "length"},
                      "embedding": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )


def quantize_int8(onnx_path, int8_path, quantize_embeddings=True):
    """Dynamic int8 quantisation of an ONNX model."""
    op_types = ["MatMul", "Gemm"]
    if quantize_embeddings:
        op_types.append("Gather")
    quantize_dynamic(onnx_path, int8_path, weight_type=QuantType.QInt8, op_types_to_quantize=op_types)


def file_size_mb(path):
    total = os.path.getsize(path)
    data_path = path + ".data"
    if os.path.exists(data_path):
        total += os.path.getsize(data_path)
    return total / (1024.0 * 1024.0)
