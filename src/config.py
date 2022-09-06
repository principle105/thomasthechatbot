from decouple import config

# Storage
storage_dir = config("STORAGE_DIR", default="storage")

# Discord Bot
token = config("TOKEN", default=None)
channel_id = config("CHANNEL_ID", cast=int, default=0)

# General
learn = config("LEARN", cast=bool, default=True)

# Responses
min_score = config("MIN_SCORE", cast=float, default=0.7)
score_threshold = config("SCORE_THRESHOLD", cast=float, default=0.7)
mesh_association = config("MESH_ASSOCIATION", cast=float, default=0.6)
