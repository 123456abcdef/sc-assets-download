#!/usr/bin/env python3

import argparse
import io
import json
import os
import pathlib
import socket
import urllib.parse
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed

SC_GAME = {
    "bb": {
        "address": ("game.boombeachgame.com", 9339),
        "assetsUrl": "http://game-assets.boombeach.com",
        "protocol": 0,
        "keyVersion": 0,
        "majorVersion": 43,
        "minorVersion": 0,
        "build": 87,
        "contentHash": "ac990d14d8e2bc3daae758d45f865f0b51e081ec",
    },
    "bs": {
        "address": ("game.brawlstarsgame.com", 9339),
        "assetsUrl": "http://game-assets.brawlstarsgame.com",
        "protocol": 2,
        "keyVersion": 19,
        "majorVersion": 32,
        "minorVersion": 0,
        "build": 170,
        "contentHash": "a241cb6a716506dfc59517a75e7236ce93d56206",
    },
    "cr": {
        "address": ("game.clashroyaleapp.com", 9339),
        "assetsUrl": "http://game-assets.clashroyaleapp.com",
        "protocol": 2,
        "keyVersion": 31,
        "majorVersion": 3,
        "minorVersion": 0,
        "build": 2465,
        "contentHash": "e49eab889ba99cdf0e40d98b8b3e38b5ff443d38",
    },
    "coc": {
        "address": ("gamea.clashofclans.com", 9339),
        "assetsUrl": "http://game-assets.clashofclans.com",
        "protocol": 3,
        "keyVersion": 100,
        "majorVersion": 13,
        "minorVersion": 0,
        "build": 675,
        "contentHash": "df960a35d591b610bf7aa6f37f9380bc28cda683",
    },
    "hd": {
        "address": ("game.haydaygame.com", 9339),
        "assetsUrl": "http://game-assets.haydaygame.com",
        "protocol": 0,
        "keyVersion": 0,
        "majorVersion": 1,
        "minorVersion": 0,
        "build": 49,
        "contentHash": "32b1a85e0122a62f2dca8f46e5479cec47b0ea96",
    },
}


def handshake(game):
    payload = b""
    payload += game["protocol"].to_bytes(4, byteorder="big")
    payload += game["keyVersion"].to_bytes(4, byteorder="big")
    payload += game["majorVersion"].to_bytes(4, byteorder="big")
    payload += game["minorVersion"].to_bytes(4, byteorder="big")
    payload += game["build"].to_bytes(4, byteorder="big")
    payload += b"\xff\xff\xff\xff"  # contentHash
    payload += (2).to_bytes(4, byteorder="big")  # deviceType
    payload += (2).to_bytes(4, byteorder="big")  # appStore

    header = b""
    header += (10100).to_bytes(2, byteorder="big")
    header += len(payload).to_bytes(3, byteorder="big")
    header += (0).to_bytes(2, byteorder="big")

    return header + payload


def client_handshake(game):
    def recv_until(sock, size):
        buf = b""
        while len(buf) != size:
            buf += sock.recv(size - len(buf))
        return io.BytesIO(buf)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(SC_GAME[game]["address"])
    msg_handshake = handshake(SC_GAME[game])
    s.send(msg_handshake)

    header = recv_until(s, 7)
    id = int.from_bytes(header.read(2), byteorder="big")
    length = int.from_bytes(header.read(3), byteorder="big")
    header.read(2)

    payload = recv_until(s, length)
    # with open(f"/data/{game}_{id}.bin", "wb") as f:
    #     f.write(header.getvalue())
    #     f.write(payload.getvalue())

    if game == "bb":
        return handle_bb(id, payload)
    elif game == "cr":
        return handle_cr(id, payload)

    return None, None


def handle_bb(id, payload):
    msg_type = int.from_bytes(payload.read(1), byteorder="big")
    if id != 20103 or msg_type != 7:
        print("Boom Beach client version outdated!")
        return None, None

    fingerprint_length = int.from_bytes(payload.read(4), byteorder="big")
    fingerprint = payload.read(fingerprint_length).decode("utf-8")

    payload.read(25)

    assets_url_length = int.from_bytes(payload.read(4), byteorder="big")
    assets_url = payload.read(assets_url_length).decode("utf-8")

    return assets_url, json.loads(fingerprint)


def handle_cr(id, payload):
    msg_type = int.from_bytes(payload.read(1), byteorder="big")
    if id != 20103 or msg_type != 7:
        print("Clash Royale client version outdated!")
        return None, None

    payload.read(23)

    assets_url_length = int.from_bytes(payload.read(4), byteorder="big")
    assets_url = payload.read(assets_url_length).decode("utf-8")

    length = int.from_bytes(payload.read(4), byteorder="big")
    payload.read(length + 5)

    compressed_length = int.from_bytes(payload.read(4), byteorder="big")
    zlength = int.from_bytes(payload.read(4), byteorder="little")
    zstring = payload.read(compressed_length - 4)
    fingerprint = zlib.decompress(zstring, 15, zlength).decode("utf-8")

    return assets_url, json.loads(fingerprint)


def dowload_fingerprint(game):
    url = (
        SC_GAME[game]["assetsUrl"]
        + "/"
        + SC_GAME[game]["contentHash"]
        + "/fingerprint.json"
    )
    with urllib.request.urlopen(url, timeout=10) as conn:
        data = conn.read()

    return json.loads(data)


def download_asset(assets_url, file, output_dir):
    url = assets_url + "/" + file
    with urllib.request.urlopen(url, timeout=10) as conn:
        data = conn.read()

    sub_dirs, file_name = os.path.split(file)
    output_dir = os.path.join(output_dir, sub_dirs)
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(data)


def main(game, thread_count, output_dir, extensions):
    assets_url = fingerprint = None

    if game in ["bb", "cr"]:
        assets_url, fingerprint = client_handshake(game)
    if not assets_url or not fingerprint:
        assets_url = SC_GAME[game]["assetsUrl"]
        fingerprint = dowload_fingerprint(game)

    output_dir = os.path.join(output_dir, fingerprint["sha"])
    try:
        os.mkdir(output_dir)
    except FileExistsError:
        pass

    with open(os.path.join(output_dir, "fingerprint.json"), "w") as f:
        f.write(json.dumps(fingerprint, indent=2))

    assets_url = urllib.parse.urljoin(assets_url, fingerprint["sha"])

    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = {}
        for fp in fingerprint["files"]:
            file = fp["file"]
            file_extension = os.path.splitext(file)[-1][1:]
            if len(extensions) == 0 or file_extension in extensions:
                futures[
                    executor.submit(download_asset, assets_url, file, output_dir)
                ] = file

        print(f"Downloading {len(futures)} assets from {assets_url}")

        for future in as_completed(futures, timeout=10):
            file = futures[future]
            try:
                future.result()
                print(f"  {file}")
            except Exception as e:
                print(f"  Error: {file} {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download latest assets for your Supercell game."
    )
    parser.add_argument(
        "-g",
        "--game",
        help="select your game",
        choices=["bb", "bs", "coc", "cr", "hd"],
        type=str,
        default="cr",
    )
    parser.add_argument(
        "-t", "--threads", help="number of downloader threads", type=int, default=4
    )
    parser.add_argument("-o", "--output", help="output directory", type=pathlib.Path)
    parser.add_argument(
        "-e",
        "--extensions",
        help="only download file with specific file extension",
        nargs="+",
        type=str,
        default=[],
    )
    args = parser.parse_args()

    output_dir = args.output if args.output else os.path.dirname(__file__)

    main(args.game, args.threads, output_dir, args.extensions)
