# yt2mp3
## Converts a youtube video to a mp3 file with ID3 tags

*Arguments:*
- **"--yt"** - Youtube link
- **"-a"** - Artist
- **"-t"** - Title
- **"-c"** - Cover image path
- **"-b"** - Album (OPTIONAL)

*Example usage:*
```
python yt2mp3 --yt <youtube link> -a <Artist> -t <title> -c <cover image path>
```

*Installation:*
```
pip install -r requirements.txt
```

*To do:*
- Implement SoundCloud API (currently new API keys are not available)
- Implement Spotify API
- Implement YouTube API
- Implement bulk downloading
- Fix READ.ME
- Create a requirements.txt
- Fix memory leaks
