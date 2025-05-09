import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from PIL import Image
import io

# Diretório padrão
dirpath = os.path.join("C:\\", "Downloads")

# Qualidades disponíveis
qtkbps = {
    "128 kbps": "0",   # FFmpeg: -q:a 0 → ~128 kbps
    "192 kbps": "5",   # -q:a 5 → ~192 kbps
    "320 kbps": "9"    # -q:a 9 → ~320 kbps (valor mais alto = melhor CBR nesse contexto com yt-dlp)
}

# Qualidade padrão
qualidade_selecionada = "192 kbps"

def selectdir():
    global dirpath
    newdirPath = filedialog.askdirectory()
    if newdirPath:
        dirpath = newdirPath
        dirlabel.config(text=f"direct: {dirpath}")

def loadingissue():
    loading = tk.Toplevel(app)
    loading.title("downloading")
    loading.geometry("250x80")
    loading.resizable(False, False)
    loading_label = tk.Label(loading, text="wait...")
    loading_label.pack(expand=True)
    loading.grab_set()
    return loading

def downloadmp3():
    url = entryurl.get().strip()
    if not url:
        messagebox.showwarning("warning", "put the url pls")
        return

    ffmpeg_path = os.path.abspath("./bin/ffmpeg.exe")
    qtvalue = qtkbps[qualidade_menu.get()]
    comando = [
        sys.executable, "-m", "yt_dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", qtvalue,
        "--ffmpeg-location", ffmpeg_path,
        "--embed-thumbnail",
        "--add-metadata",
        "-P", dirpath,
        url
    ]

    # Mostrar tela de carregamento
    loading_window = loadingissue()
    app.update()

    try:
        subprocess.run(comando, check=True)

        # Procurar o último .mp3 baixado
        mp3_file = None
        for file in sorted(os.listdir(dirpath), key=lambda f: os.path.getmtime(os.path.join(dirpath, f)), reverse=True):
            if file.endswith(".mp3"):
                mp3_file = os.path.join(dirpath, file)
                break

        if mp3_file:
            audio = MP3(mp3_file, ID3=ID3)

            # Extrair thumbnail embutida
            if "APIC:" in audio.tags:
                original_apic = audio.tags["APIC:"]
                image = Image.open(io.BytesIO(original_apic.data))

                # Cortar imagem pro centro 1:1
                width, height = image.size
                side = min(width, height)
                left = (width - side) // 2
                top = (height - side) // 2
                cropped_image = image.crop((left, top, left + side, top + side))

                # Salvar imagem como JPEG em memória
                img_bytes = io.BytesIO()
                cropped_image.save(img_bytes, format='JPEG')
                img_bytes.seek(0)

                # Substituir capa
                audio.tags.delall("APIC")
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc=u"Cover",
                        data=img_bytes.read()
                    )
                )
                audio.save()

        loading_window.destroy()
        messagebox.showinfo("yippee", f"Sucess! You can see ur file in:\n{dirpath}")
    except subprocess.CalledProcessError:
        loading_window.destroy()
        messagebox.showerror("ur dumb", "fuck you")

# GUI com tkinter
app = tk.Tk()
app.title("frierenloader smth like that")
app.geometry("470x240")
app.resizable(False, False)

tk.Label(app, text="url").pack(pady=5)
entryurl = tk.Entry(app, width=60)
entryurl.pack()

tk.Button(app, text="dir:", command=selectdir).pack(pady=5)
dirlabel = tk.Label(app, text=f"selected dir: {dirpath}")
dirlabel.pack()

# Menu de qualidade
frame_q = tk.Frame(app)
tk.Label(frame_q, text="mp3 quality:").pack(side=tk.LEFT, padx=5)
qualidade_menu = tk.StringVar(value=qualidade_selecionada)
tk.OptionMenu(frame_q, qualidade_menu, *qtkbps.keys()).pack(side=tk.LEFT)
frame_q.pack(pady=5)

tk.Button(app, text="vambora", command=downloadmp3).pack(pady=15)

app.mainloop()
