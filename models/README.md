# Models

This directory is reserved for model manifests, version notes, and lightweight configuration needed to reproduce inference.

Rules:
- Do not commit large model weights such as `.pt`, `.pth`, `.onnx`, or generated arrays.
- Record model source, training dataset, intended gases, metrics, and known limits.
- Store deployable weights in controlled external storage or a release artifact system.
- Never include API keys, database passwords, or service credentials in model configs.
