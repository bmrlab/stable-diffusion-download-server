sudo docker build -t file-downloader .

sudo docker run --name file-downloader -p 8000:8000 -v /home/azureuser/kang/stable-diffusion-webui-docker:/app/data -d file-downloader:latest