"""
ml.models
=========
Person 2 model code.

  features.py        CampusGraph column layout, encode/decode helpers
  gnn_encoder.py     message-passing encoder (PyTorch + NumPy forward)
  layout_decoder.py  embedding + latent noise → bounded (x, y, rotation)
  campus_model.py    encoder → decoder, checkpoint load/save
"""
