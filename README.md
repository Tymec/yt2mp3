# yt2mp3
## Converts a youtube video to a mp3 file with ID3 tags

*Arguments:*
- **"--yt"** - Youtube link (**REQUIRED**)
- **"--sc"** - Soundcloud link (**OPTIONAL**)
- **"-m"** - Manual tags (**OPTIONAL**)
  - **"-a"** - Artist
  - **"-t"** - Title
  - **"-c"** - Cover image path

*Example usage:*
```
python yt2mp3 --yt <youtube link> -m -a <Artist> -t <title> -c <cover image path>
```

*Installation:*
```
pip install -r requirements.txt
```

*To do:*
- Implement SoundCloud API (currently new API keys are not available)
- Add album name as a separate manual tag
- Make cover image tag accept url as input
- Get rid of soundcloud link argument (not reliable)
- Create a way to bulk convert from a text file
- Create a UI
- Remove virtualenv folder
- Create a requirements.txt
