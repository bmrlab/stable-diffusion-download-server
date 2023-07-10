sudo docker build -t file-downloader .

sudo docker run --name file-downloader -p 8000:8000 -v /opt/data:/app/data -d file-downloader:latest