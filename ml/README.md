# ML Workspace

This folder contains dataset, training, weights, and output artifacts for the vehicle damage detection model.

The POC target classes are:

```text
0 dent
1 scratch
2 broken_glass
3 bumper_damage
```

## Dataset Structure

```text
ml/dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

Each image should have a matching `.txt` label file with YOLO annotations:

```text
class_id center_x center_y width height
```

Coordinates are normalized between `0` and `1`.
