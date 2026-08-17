# AI Vehicle Damage Inspection

This repository contains code and assets for a proof-of-concept (POC) system to detect vehicle exterior damage using computer vision models.

## Project overview

The goal of this project is to identify common types of vehicle damage from images (e.g., dents, scratches, broken glass, bumper damage). The repository includes an ML workspace for dataset preparation, model training and weights, and tools to run inference on images.

## Key POC classes

- 0: dent
- 1: scratch
- 2: broken_glass
- 3: bumper_damage

## Repository layout (high-level)

- ml/ — ML workspace: dataset, training scripts, model weights, and outputs
  - ml/dataset/
    - images/
      - train/
      - val/
      - test/
    - labels/
      - train/
      - val/
      - test/
  - ml/README.md — dataset format and quick notes
- (other folders) — add code, notebooks, web app, or deployment artifacts here

Each image in the dataset should have a matching YOLO-format `.txt` label file with the following line format:

```
class_id center_x center_y width height
```

Coordinates are normalized between 0 and 1.

## Getting started

1. Clone the repository:

```bash
git clone https://github.com/AkshitaRathore2026/AI_Vehicle_Damage_Inspection.git
cd AI_Vehicle_Damage_Inspection
```

2. Inspect the `ml/` folder for dataset layout and training materials.

3. Prepare your Python environment (this repo is primarily Python):

```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt  # if a requirements file exists
```

## Training & evaluation (high-level)

- Place labeled images under `ml/dataset/images/{train,val,test}` and labels under `ml/dataset/labels/{train,val,test}`.
- Use the repository's training scripts (see `ml/` for scripts or notebooks) to train a model on the training split and evaluate on validation/test splits.
- Save trained weights and exported artifacts into an appropriate `ml/weights` or `ml/output` directory.

## Inference

- Use the trained model weights and an inference script (not included here) to run damage detection on new images.
- Ensure any inference script expects YOLO-format labels if doing evaluation or visualization.

## Contributing

Contributions are welcome. Typical contributions include:
- Improving dataset quality and label coverage
- Adding training scripts and experiment tracking
- Adding model evaluation, visualization, and deployment examples
- Writing tests and improving documentation

Please open issues or pull requests describing your proposed changes.

## License & contact

Add or update a LICENSE file at the repository root to state the project's license.

For questions or collaboration, open an issue or contact the repository owner.
