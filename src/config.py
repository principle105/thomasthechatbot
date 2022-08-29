from decouple import config

# Storage
storage_dir = config("STORAGE_DIR", default="storage")

# Discord Bot
token = config("TOKEN", default=None)
channel_id = config("CHANNEL_ID", cast=int, default=0)

# General
learn = config("LEARN", cast=bool, default=True)

# Responses
keyword_threshold = config("KEYWORD_THRESHOLD", cast=float, default=0.8)
stopword_threshold = config("STOPWORD_THRESHOLD", cast=float, default=0.5)
mesh_association = config("MESH_ASSOCIATION", cast=float, default=0.5)
