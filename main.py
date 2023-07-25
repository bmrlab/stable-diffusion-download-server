import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
import requests
import logging
import shutil
import psutil
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime

app = FastAPI()

# 定义 SQLAlchemy 数据库模型
Base = declarative_base()
engine = create_engine('sqlite:///./data.db')
SessionLocal = sessionmaker(bind=engine)


# Define the Task model
class AccessRecord(Base):
    __tablename__ = "access_record"
    path = Column(String, primary_key=True, index=True)
    file_size = Column(Integer)
    access_time = Column(DateTime, default=datetime.datetime.now())


# Create the database tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------


base_dir = "./data"


class FetchItem(BaseModel):
    url: str
    filepath: str


class DownloadItem(BaseModel):
    filepath: str


class CheckItem(BaseModel):
    filepath: str


class RemoveItem(BaseModel):
    filepath: str


class Symlink(BaseModel):
    source: str
    symlink: str


class CopyItem(BaseModel):
    source: str
    target: str


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
    # 记录check记录: 时间点 文件大小 文件路径
    file_location = os.path.join(base_dir, check_item.filepath)
    exist = os.path.exists(file_location)
    if exist:
        db = next(get_db())
        await _save_or_update_record(db, file_location)
        await _gc(db)
    exist = os.path.exists(file_location)

    result = {
        "status":
            200, "data":
            {
                "exist": exist
            },
        "msg": "success"
    }
    return result


async def _save_or_update_record(db, file_location):
    record = db.query(AccessRecord).filter(AccessRecord.path == file_location).first()
    if record:
        record.access_time = datetime.datetime.now()
    else:
        record = AccessRecord(path=file_location, file_size=os.path.getsize(file_location))
        db.add(record)
    db.commit()


async def _gc(db):
    disk_info = psutil.disk_usage(base_dir)
    # 当磁盘剩余空间少于20G时 开始清空磁盘 清空到剩余空间大于20G
    total_free_size = 0
    while disk_info.free / (1024 ** 3) < 20:
        records = db.query(AccessRecord).order_by(AccessRecord.access_time.desc()).limit(5).all()
        for record in records:
            total_free_size += record.file_size
            os.remove(record.path)
            db.delete(record)
        if len(records) == 0:
            break
        db.commit()
    logging.info(f"释放空间: {total_free_size / (1024 ** 3):.2f}G")


@app.post("/copy")
def copy_file(item: CopyItem):
    """
    创建copy
    :param item:
    :return:
    """
    src = os.path.join(base_dir, item.source)
    target = os.path.join(base_dir, item.target)
    if os.path.exists(src):
        if os.path.exists(target) or os.path.islink(target):
            os.remove(target)
        shutil.copy(src, target)
    return {"status": 200, "data": {}, "msg": "success"}


@app.post("/symlink")
def set_symlink(s: Symlink):
    """
    创建软连接
    :param s:
    :return:
    """
    file_location = os.path.join(base_dir, s.source)
    symlink_location = os.path.join(base_dir, s.symlink)
    if os.path.exists(file_location):
        if os.path.exists(symlink_location) or os.path.islink(symlink_location):
            os.remove(symlink_location)
        os.symlink(file_location, symlink_location)
        return {"status": 200, "data": {}, "msg": "success"}
    else:
        return {"status": 400, "msg": "file not found!", "data": {}}


@app.delete("/remove")
def rm_file(item: RemoveItem):
    """
    文件删除
    :param item:
    :return:
    """
    file_location = os.path.join(base_dir, item.filepath)
    if os.path.exists(file_location):
        os.remove(file_location)
    return {"status": 200, "data": {}, "msg": "success"}


if __name__ == "__main__":
    import uvicorn

    # 启动服务
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
