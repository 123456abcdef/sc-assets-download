FROM python:3-alpine

COPY sc_assets_download.py /app/sc_assets_download.py

ENTRYPOINT [ "python", "/app/sc_assets_download.py", "--output", "/data" ]
