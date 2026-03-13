import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading

import queue
from translator import translate_text
from file_handler import read_txt, read_pdf, read_docx, write_txt

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Bengali": "bn",
    "Marathi": "mr",
    "Urdu": "ur",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml"
}


class TranslatorUI:
    def __init__(self, root):
        self.root = root
        root.title("translator-python")
        root.geometry("900x700")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        self.build_file_tab(notebook)
        self.build_text_tab(notebook)

        self.translation_queue = queue.Queue()
        self.root.after(100, self.process_queue)

    # ================= FILE TAB =================
    def build_file_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="File Translator")

        self.file_path = tk.StringVar()

        ttk.Button(frame, text="Upload File", command=self.upload_file).pack(pady=6)
        ttk.Label(frame, textvariable=self.file_path, wraplength=750).pack(pady=4)

        self.src_lang = ttk.Combobox(frame, values=list(LANGUAGES.keys()), state="readonly")
        self.src_lang.set("English")
        self.src_lang.pack(pady=4)

        self.dst_lang = ttk.Combobox(frame, values=list(LANGUAGES.keys()), state="readonly")
        self.dst_lang.set("Hindi")
        self.dst_lang.pack(pady=4)

        ttk.Button(frame, text="Translate File", command=self.start_translation_thread).pack(pady=10)

        self.progress = ttk.Progressbar(frame, length=500, mode="determinate")
        self.progress.pack(pady=6)

        self.status = ttk.Label(frame, text="", foreground="blue")
        self.status.pack(pady=4)

        self.size_info = ttk.Label(frame, text="", foreground="green")
        self.size_info.pack(pady=4)

    def upload_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Supported files", "*.txt *.pdf *.docx")]
        )
        if path:
            self.file_path.set(path)
            size_kb = os.path.getsize(path) / 1024
            self.size_info.config(text=f"Source file size: {size_kb:.2f} KB")

    def start_translation_thread(self):
        threading.Thread(target=self.translate_file, daemon=True).start()

    def update_progress(self, current, total):
        percent = int((current / total) * 100)
        self.progress["value"] = percent
        self.status.config(text=f"Translating PART {current} / {total}")
        self.root.update_idletasks()
        self.translation_queue.put(("progress", current, total))

    def translate_file(self):
        path = self.file_path.get()
        if not path:
            messagebox.showerror("Error", "Please select a file.")
            return
            return self.translation_queue.put(("error", "Please select a file."))

        self.progress["value"] = 0
        self.status.config(text="Reading file...")
        self.translation_queue.put(("status", "Reading file..."))

        ext = os.path.splitext(path)[1].lower()

        if ext == ".txt":
            text = read_txt(path)
        elif ext == ".pdf":
            text = read_pdf(path)
        elif ext == ".docx":
            text = read_docx(path)
        else:
            messagebox.showerror("Error", "Unsupported file type.")
            return
            return self.translation_queue.put(("error", "Unsupported file type."))

        translated = translate_text(
            text,
            LANGUAGES[self.src_lang.get()],
            LANGUAGES[self.dst_lang.get()],
            self.update_progress
        )

        folder = os.path.dirname(path)
        original_name = os.path.basename(path)
        lang = self.dst_lang.get().lower()

        output_path = os.path.join(
            folder, f"{lang}-translated-{original_name}.txt"
        )

        write_txt(output_path, translated)

        out_size_kb = os.path.getsize(output_path) / 1024

        self.status.config(text="Translation complete ✅")
        self.size_info.config(
            text=f"Saved to: {output_path} | Size: {out_size_kb:.2f} KB"
        )
        self.translation_queue.put(("complete", output_path, out_size_kb))

    def process_queue(self):
        try:
            message = self.translation_queue.get_nowait()
            msg_type = message[0]

            if msg_type == "progress":
                _, current, total = message
                percent = int((current / total) * 100)
                self.progress["value"] = percent
                self.status.config(text=f"Translating PART {current} / {total}")
            elif msg_type == "status":
                _, text = message
                self.status.config(text=text)
            elif msg_type == "error":
                _, error_msg = message
                messagebox.showerror("Error", error_msg)
            elif msg_type == "complete":
                _, output_path, out_size_kb = message
                self.status.config(text="Translation complete ✅")
                self.size_info.config(
                    text=f"Saved to: {output_path} | Size: {out_size_kb:.2f} KB"
                )
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)
    # ================= TEXT TAB =================
    def build_text_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="Text Translator")

        self.input_text = tk.Text(frame, height=10)
        self.input_text.pack(fill="x", pady=6)

        self.src_lang2 = ttk.Combobox(frame, values=list(LANGUAGES.keys()), state="readonly")
        self.src_lang2.set("English")
        self.src_lang2.pack(pady=4)

        self.dst_lang2 = ttk.Combobox(frame, values=list(LANGUAGES.keys()), state="readonly")
        self.dst_lang2.set("Hindi")
        self.dst_lang2.pack(pady=4)

        ttk.Button(frame, text="Translate Text", command=self.translate_text_ui).pack(pady=8)

        self.output_text = tk.Text(frame, height=10)
        self.output_text.pack(fill="x", pady=6)

    def translate_text_ui(self):
        text = self.input_text.get("1.0", tk.END)
        translated = translate_text(
            text,
            LANGUAGES[self.src_lang2.get()],
            LANGUAGES[self.dst_lang2.get()]
        )
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, translated)
