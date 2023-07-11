import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import requests
import logging

app = FastAPI()

base_dir = "./data"


class FetchItem(BaseModel):
    url: str
    filepath: str


@app.post("/fetch")
def fetch(item: FetchItem):
    r = requests.get(url=item.url)
    logging.info(f"start download: {item}")
    if r.ok:
        d = os.path.join(base_dir, os.path.dirname(item.filepath))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, os.path.basename(item.filepath)), 'wb') as f:
            f.write(r.content)
    return {"is_ok": True}


@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    文件下载
    :param file_path:
    :return:
    """
    file_location = os.path.join(base_dir, file_path)
    filename = os.path.basename(file_location)
    return FileResponse(file_location, filename=filename)
