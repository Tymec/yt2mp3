from __future__ import unicode_literals
from urllib import request
import requests
from bs4 import BeautifulSoup as BS
import youtube_dl
import argparse
import os
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

parser = argparse.ArgumentParser()
parser.add_argument(
    '--yt',
    type=str,
    required=True,
    help="Link to the YouTube video",
    metavar="link",
    dest="yt"
    )
parser.add_argument(
    '--sc',
    type=str,
    required=True,
    help="Link to the SoundCloud song",
    metavar="link",
    dest="sc"
    )
args = parser.parse_args()


class Song:
    def __init__(self, title, artist):
        self.title = title
        self.artist = artist
        self.album = title.split('(')[0]
        self.cover = "{} - {}.jpg".format(artist, title)
        self.mp3 = "{} - {}.mp3".format(artist, title)


def download_yt(yt, info):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': info.mp3[:-4] + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([yt])


def download_sc(sc, info):
    html = request.urlopen(sc).read()
    soup = BS(html, 'html.parser')
    for link in soup.find_all('div'):
        for img in link.find_all('img'):
            new_link = img.get("src")
            if new_link.find('gif') != -1:
                continue
            request.urlretrieve(new_link, info.cover)


def get_info(sc):
    html = request.urlopen(sc).read()
    soup = BS(html, 'html.parser')

    song_info = soup.title.text.split('|')[0]

    title = song_info.split('by')[0][:-1]
    artist = song_info.split('by')[1][1:-1]

    song = Song(title, artist)
    return song


def get_sc(info):
    url = "https://soundcloud.com/search?q={}%20-%20{}"\
        .format(
            info.artist.replace(' ', '%20'),
            info.title.replace(' ', '%20')
        )
    html = requests.get(url)
    with open('html', 'w', encoding='UTF-8') as site:
        site.write(html.text)


def tags(info):
    image = open(info.cover, 'rb').read()

    audio = EasyID3(info.mp3)
    audio['artist'] = info.artist
    audio['title'] = info.title
    audio['album'] = info.album
    audio['albumartist'] = info.artist
    audio.save(v2_version=3)

    audio = ID3(info.mp3)
    audio.add(APIC(3, 'image/jpeg', 3, 'Front cover', image))
    audio.save(v2_version=3)


def finish(info):
    os.remove(info.cover)


if type(args.yt) and type(args.sc) == str:
    info = get_info(args.sc)
    get_sc(info)
    # download_sc(args.sc, info)
    # download_yt(args.yt, info)
    # tags(info)
    # finish(info)
else:
    print("Wrong input")
    exit()

