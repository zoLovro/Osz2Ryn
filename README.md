### Osz2Ryn Converter

This tool converts osu! `.osz` beatmap files into the folder structure used by the rhythm game **Ryn**.  
It extracts audio, background images, metadata, and Mania note data from all `.osu` files and converts them into Ryn-compatible formats.

The program outputs a ready-to-use directory under `maps/<BeatmapName_Ryn>/` containing:

- `song.<ext>`  
- `background.jpg`  
- one `.txt` note file per `.osu`  
- a single `info.json` describing the map

Place the generated folder into your Ryn `maps` directory to play the beatmap.
