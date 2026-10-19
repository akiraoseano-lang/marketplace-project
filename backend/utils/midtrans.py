import os
from pathlib import Path

import midtransclient
from dotenv import load_dotenv

ENV_PATH =  Path(__file__).resolve().parent.parent / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")

if not SERVER_KEY or not CLIENT_KEY:
    raise ValueError(
        f"Key Midtrans belum terbaca. Tolong periksa file: {ENV_PATH}"
    )

snap = midtransclient.Snap(
    is_production=False,
    server_key=SERVER_KEY,
    client_key=CLIENT_KEY
)