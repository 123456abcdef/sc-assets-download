# sc-assets-download

Python script to download latest assets of your Supercell game.

## Installation
Optional: If you want to use `sc_assets_download.py` inside a container
```console
docker build --pull -t sc-assets-download .
```

## Usage
```console
usage: sc_assets_download.py [-h] [-g {bs,coc,cr,hd}] [-t] [-o] [-e]

Download latest assets for your Supercell game.

optional arguments:
  -h, --help
                        show this help message and exit
  -g, --game {bs,coc,cr,hd}
                        select your game, default: cr
  -t, --threads
                        number of downloader threads, default: 4
  -o, --output
                        output directory
  -e, --extensions
                        only download file with specific file extension, default: all
```
Here an example on how to use the container
```console
docker run --rm -it --volume "$PWD":/data --user="$(id -u):$(id -g)" sc-assets-download
```

## Update
With every game or asset update the content hashes and version numbers defined in the Python script will change.
To update these fields yourself download the APK manually.
You can look up the `contentHash`, `majorVersion`, and `build` in the `fingerprint.json` inside the game's APK.
Download the APK and find the file in the following directory `<path-to-apk>/assets`.
The needed values are listed at the end.
```
{
  "files": [
    ...
  ],
  "sha": "a241cb6a716506dfc59517a75e7236ce93d56206", # contentHash
  "version": "32.171.1" # majorVersion.build.x
}
```

### Advanced
You can also capture the first packet send by the client.
The message structure should be as follows.
```json
{
  "id": 10100,
  "name": "ClientHello",
  "fields": [
    {"name": "protocol", "type": "INT"},
    {"name": "keyVersion", "type": "INT"},
    {"name": "majorVersion", "type": "INT"},
    {"name": "minorVersion", "type": "INT"},
    {"name": "build", "type": "INT"},
    {"name": "contentHash", "type": "STRING"},
    {"name": "deviceType", "type": "INT"},
    {"name": "appStore", "type": "INT"}
  ]
}
```
For some games it is possible to get the latest assets without knowing the exact `contentHash`.
The response with the updated `fingerprint.json` should be as follows.

**Boom Beach**
```json
{
  "id": 20103,
  "name": "Fingerprint",
  "fields": [
    {"name": "type", "type": "INT"},
    {"name": "fingerprint", "type": "STRING"},
    {"type": "STRING"},
    {"type": "STRING"},
    {"type": "STRING"},
    {"type": "STRING"},
    {"type": "BYTE"},
    {"type": "INT"},
    {"name": "assetsUrls", "type": "STRING[]"},
    {"name": "eventAssetsUrls", "type": "STRING[]"}
  ]
}
```

**Brawl Stars**
    
tbd

**Clash of Clans**
    
Hidden behind session encryption.

**Clash Royale**
```json
{
  "id": 20103,
  "name": "Fingerprint",
  "fields": [
    {"name": "id", "type": "VARINT" },
    {"type": "STRING"},
    {"type": "STRING"},
    {"name": "updateUrl", "type": "STRING"},
    {"type": "STRING"},
    {"type": "VARINT"},
    {"type": "VARINT"},
    {"type": "STRING"},
    {"type": "VARINT"},
    {"name": "assetsUrl", "type": "STRING"},
    {"name": "cdnUrl", "type": "STRING"},
    {"type": "STRING"},
    {"type": "VARINT"},
    {"name": "fingerprint", "type": "ZIP_STRING"}
  ]
}
```

**Hay Day**
    
tbd

## Credits
- [Galaxy1036/Sc-Assets-Downloader](https://github.com/Galaxy1036/Sc-Assets-Downloader/)
