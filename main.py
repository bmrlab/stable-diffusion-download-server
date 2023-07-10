import os
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import logging

app = FastAPI()

base_dir = "./data"


class DownloadItem(BaseModel):
    url: str
    filepath: str


@app.post("/download")
def read_root(item: DownloadItem):
    r = requests.get(url=item.url)
    logging.info(f"start download: {item}")
    if r.ok:
        d = os.path.join(base_dir, os.path.dirname(item.filepath))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, os.path.basename(item.filepath)), 'wb') as f:
            f.write(r.content)
    return {"is_ok": True}
