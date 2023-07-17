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


class DownloadItem(BaseModel):
    filepath: str


class CheckItem(BaseModel):
    filepath: str


class Symlink(BaseModel):
    source: str
    symlink: str


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


@app.post("/download/{file_path:path}")
async def download_file(download: DownloadItem):
    """
    文件下载
    :return:
    """
    file_location = os.path.join(base_dir, download.filepath)
    filename = os.path.basename(file_location)
    if os.path.exists(filename):
        return FileResponse(file_location, filename=filename)
    else:
        return {"status": 400, "msg": "file not found!", "data": {}}


@app.post("/check")
async def check(check_item: CheckItem):
    """
    文件检查
    :return:
    """
    file_location = os.path.join(base_dir, check_item.filepath)
    return {"status": 200, "data": {"exist": os.path.exists(file_location)}, "msg": "success"}


@app.post("/symlink")
def set_symlink(s: Symlink):
    file_location = os.path.join(base_dir, s.source)
    symlink_location = os.path.join(base_dir, s.symlink)
    if os.path.exists(file_location):
        os.symlink(file_location, symlink_location)
        return {"status": 200, "data": {}, "msg": "success"}
    else:
        return {"status": 400, "msg": "file not found!", "data": {}}
