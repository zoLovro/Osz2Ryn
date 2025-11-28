import tkinter as tk
from tkinter import filedialog, messagebox
import os
import zipfile
import shutil
import tempfile
import json

class OskConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OSK / OSZ Converter")
        self.root.geometry("450x250")

        self.osk_path = None

        self.upload_btn = tk.Button(root, text="Upload .osk / .osz file", command=self.upload_osk)
        self.upload_btn.pack(pady=20)

        self.start_btn = tk.Button(root, text="Start Conversion", command=self.start_conversion)
        self.start_btn.pack(pady=10)

        self.status_label = tk.Label(root, text="No file selected")
        self.status_label.pack(pady=10)

    def upload_osk(self):
        path = filedialog.askopenfilename(
            title="Select .osk or .osz file",
            filetypes=[
                ("OSU Skin / Beatmap", "*.osk *.osz"),
                ("ZIP files", "*.zip"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.osk_path = path
            self.status_label.config(text=f"Loaded: {os.path.basename(path)}")

    def start_conversion(self):
        if not self.osk_path:
            messagebox.showwarning("No File", "Upload a .osk/.osz file first.")
            return

        temp_dir = tempfile.mkdtemp()

        # folder name logic
        original_folder_name = os.path.splitext(os.path.basename(self.osk_path))[0]
        new_folder_name = original_folder_name + "_Ryn"

        maps_root = os.path.join(os.getcwd(), "maps")
        os.makedirs(maps_root, exist_ok=True)

        output_dir = os.path.join(maps_root, new_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        # unzip
        try:
            with zipfile.ZipFile(self.osk_path, "r") as z:
                z.extractall(temp_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Error unzipping file:\n{e}")
            return

        # collect files
        osu_files = []
        image_files = []
        audio_files = []

        for root_dir, dirs, files in os.walk(temp_dir):
            for file in files:
                lower = file.lower()

                if lower.endswith(".osu"):
                    osu_files.append(os.path.join(root_dir, file))

                elif lower.endswith((".mp3", ".ogg", ".wav")):
                    audio_files.append(os.path.join(root_dir, file))

                elif lower.endswith((".jpg", ".jpeg", ".png")):
                    image_files.append(os.path.join(root_dir, file))

        # copy audio → song.<ext>
        audio_rel = ""
        if audio_files:
            src = audio_files[0]
            ext = os.path.splitext(src)[1]
            song_name = "song" + ext
            dest = os.path.join(output_dir, song_name)
            shutil.copy2(src, dest)
            audio_rel = f"maps/{new_folder_name}/{song_name}"

        # copy image → background.jpg
        background_rel = ""
        if image_files:
            src = image_files[0]
            dest = os.path.join(output_dir, "background.jpg")
            shutil.copy2(src, dest)
            background_rel = f"maps/{new_folder_name}/background.jpg"

        # lane map
        lane_map = {64: 0, 192: 1, 320: 2, 448: 3}

        # combined note file
        note_path = os.path.join(output_dir, "noteFile.txt")

        title = ""
        artist = ""

        # Parse ONLY the first .osu for metadata
        if osu_files:
            first_osu = osu_files[0]
            with open(first_osu, "r", encoding="utf-8") as f:
                in_meta = False
                for line in f:
                    s = line.strip()
                    if s == "[Metadata]":
                        in_meta = True
                        continue
                    if s.startswith("[") and s != "[Metadata]":
                        in_meta = False
                    if in_meta:
                        if s.startswith("Title:"):
                            title = s[6:].strip()
                        elif s.startswith("Artist:"):
                            artist = s[7:].strip()

        # convert ALL .osu into one noteFile.txt
        with open(note_path, "w", encoding="utf-8") as out:
            for osu in osu_files:
                with open(osu, "r", encoding="utf-8") as inp:
                    in_hit = False
                    for line in inp:
                        s = line.strip()

                        if s == "[HitObjects]":
                            in_hit = True
                            continue
                        if s.startswith("[") and s != "[HitObjects]":
                            in_hit = False

                        if not in_hit:
                            continue
                        if not s:
                            continue

                        parts = s.split(",")
                        if len(parts) < 5:
                            continue

                        try:
                            x = int(parts[0])
                            t_ms = int(parts[2])
                            ty = int(parts[3])
                        except:
                            continue

                        if x not in lane_map:
                            continue

                        lane = lane_map[x]
                        t_s = t_ms / 1000.0

                        # tap
                        if ty == 1:
                            out.write(f"note, {t_s:.3f}f, {lane};\n")

                        # hold
                        elif ty == 128:
                            if len(parts) < 6:
                                continue
                            end_raw = parts[5].split(":")[0]
                            try:
                                end_ms = int(end_raw)
                            except:
                                continue
                            end_s = end_ms / 1000.0
                            out.write(f"note, {t_s:.3f}f, {end_s:.3f}f, {lane};\n")

        # create ONE json file
        json_path = os.path.join(output_dir, "info.json")

        json_data = {
            "title": title,
            "artist": artist,
            "bpm": 100,
            "audio": audio_rel,
            "audioTrimmed": f"maps/{new_folder_name}/song_trimmed.mp3",
            "background": background_rel,
            "noteFile": f"maps/{new_folder_name}/noteFile.txt"
        }

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(json_data, jf, ensure_ascii=False, indent=2)

        messagebox.showinfo("Done", f"Finished.\nOutput folder:\n{output_dir}")

def main():
    root = tk.Tk()
    app = OskConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
