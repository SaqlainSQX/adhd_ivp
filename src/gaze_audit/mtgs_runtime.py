"""Minimal frozen MTGS runtime, without importing its training data or logger stack."""

import importlib.util
import sys
import types
from pathlib import Path

MODEL_SETTINGS = {
    "image_size": 448,
    "patch_size": 14,
    "decoder_feature_dim": 128,
    "decoder_use_bn": True,
    "temporal_context": 2,
}
MEAN = [0.44232, 0.40506, 0.36457]
STD = [0.28674, 0.27776, 0.27995]


def load_model(mtgs_root: Path, dino_root: Path, checkpoint: Path, device="cuda"):
    import torch

    # Namespace setup avoids upstream __init__ imports of training loggers/data modules.
    for name, path in [
        ("mtgs", mtgs_root / "mtgs"),
        ("mtgs.networks", mtgs_root / "mtgs/networks"),
        ("mtgs.utils", mtgs_root / "mtgs/utils"),
    ]:
        package = types.ModuleType(name)
        package.__path__ = [str(path.resolve())]
        sys.modules[name] = package
    spec = importlib.util.spec_from_file_location(
        "mtgs.utils.utils", mtgs_root / "mtgs/utils/utils.py"
    )
    utilities = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utilities)
    sys.modules["mtgs.utils.utils"] = utilities
    for name in ["pair", "build_2d_sincos_posemb"]:
        setattr(sys.modules["mtgs.utils"], name, getattr(utilities, name))
    from mtgs.networks.mtgs_net import MTGS

    original_load = torch.hub.load

    def pinned_dino(repository, model, *args, **kwargs):
        if repository != "facebookresearch/dinov2" or model != "dinov2_vitb14":
            raise ValueError("Unexpected upstream torch.hub dependency")
        # The complete encoder weights are already in the hash-pinned MTGS state.
        return original_load(str(dino_root.resolve()), model, source="local", pretrained=False)

    torch.hub.load = pinned_dino
    try:
        model = MTGS(**MODEL_SETTINGS)
    finally:
        torch.hub.load = original_load
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    state = {key.removeprefix("model."): value for key, value in state.items()}
    model.load_state_dict(state, strict=True)
    model.eval().to(device)
    return model, utilities.square_bbox


def prune_unused_heatmap(model):
    """Skip an independent auxiliary output; native LAH/LAEO computation is unchanged."""
    import torch

    class EmptyHeatmap(torch.nn.Module):
        def forward(self, image_layers, person_layers, image_shape):
            bt, people, _ = person_layers[0].shape
            return person_layers[0].new_zeros(bt, people, 1, 1)

    model.gaze_hm_decoder_new = EmptyHeatmap()


def prepare_window(
    anchor,
    frame_rows: dict,
    person_rows: dict,
    image_loader,
    square_bbox,
    *,
    device="cuda",
    prepared_loader=None,
):
    """Public geometry only; fixed real-track slots plus one zero placeholder.

    Missing neighbors/tracks have zero tensors. No augmentation, reference gaze,
    class labels, eligibility flags or oracle values enter this input.
    """
    import torch
    import torchvision.transforms.functional as tf

    anchor_people = person_rows[anchor["frame_id"]]
    person_ids = sorted(anchor_people)
    count = len(person_ids) + 1
    images, heads, boxes = [], [], []
    valid_counts = []
    for offset in [-6, -3, 0, 3, 6]:
        key = (anchor["clip_id"], int(anchor["original_frame_index"]) + offset)
        row = frame_rows.get(key)
        head = torch.zeros(count, 3, 224, 224)
        box = torch.zeros(count, 4)
        if row is None:
            image = torch.zeros(3, 448, 448)
            valid_counts.append(0)
        else:
            if prepared_loader is not None:
                image, prepared_heads, prepared_boxes = prepared_loader(row["frame_id"])
                valid_counts.append(sum(pid in prepared_heads for pid in person_ids))
                for slot, pid in enumerate(person_ids, start=1):
                    if pid in prepared_heads:
                        head[slot] = prepared_heads[pid]
                        box[slot] = prepared_boxes[pid]
                images.append(image)
                heads.append(head)
                boxes.append(box)
                continue
            pil = image_loader(row["annotation_path"]).convert("RGB")
            width, height = pil.size
            image = tf.normalize(
                tf.to_tensor(tf.resize(pil, [448, 448], antialias=True)), MEAN, STD
            )
            current = person_rows[row["frame_id"]]
            valid_counts.append(sum(pid in current for pid in person_ids))
            for slot, pid in enumerate(person_ids, start=1):
                if pid not in current:
                    continue
                normalized = torch.tensor(current[pid], dtype=torch.float32)
                pixel = normalized * torch.tensor([width, height, width, height])
                squared = square_bbox(pixel.unsqueeze(0), width, height)[0]
                crop = pil.crop(squared.int().tolist())
                head[slot] = tf.normalize(
                    tf.to_tensor(tf.resize(crop, [224, 224], antialias=True)), MEAN, STD
                )
                box[slot] = squared / torch.tensor([width, height, width, height])
        images.append(image)
        heads.append(head)
        boxes.append(box)
    return {
        "image": torch.stack(images).unsqueeze(0).to(device),
        "heads": torch.stack(heads).unsqueeze(0).to(device),
        "head_bboxes": torch.stack(boxes).unsqueeze(0).to(device),
        "num_valid_people": torch.tensor(valid_counts, device=device),
    }, person_ids


def prepare_public_frame(row, person_rows, image_loader, square_bbox):
    """Cacheable public preprocessing, identical to prepare_window's uncached path."""
    import torch
    import torchvision.transforms.functional as tf

    pil = image_loader(row["annotation_path"]).convert("RGB")
    width, height = pil.size
    image = tf.normalize(tf.to_tensor(tf.resize(pil, [448, 448], antialias=True)), MEAN, STD)
    heads, boxes = {}, {}
    for pid, bbox in person_rows[row["frame_id"]].items():
        normalized = torch.tensor(bbox, dtype=torch.float32)
        pixel = normalized * torch.tensor([width, height, width, height])
        squared = square_bbox(pixel.unsqueeze(0), width, height)[0]
        crop = pil.crop(squared.int().tolist())
        heads[pid] = tf.normalize(
            tf.to_tensor(tf.resize(crop, [224, 224], antialias=True)), MEAN, STD
        )
        boxes[pid] = squared / torch.tensor([width, height, width, height])
    return image, heads, boxes
