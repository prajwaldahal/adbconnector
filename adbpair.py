import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import json

cache_file = "adb_cache.json"

root = tk.Tk()
root.title("ADB Pair & Connect")
root.geometry("360x320")
root.configure(bg="#f5f5f5")
root.resizable(False, False)

style = ttk.Style(root)
style.theme_use('clam')
style.configure('TLabel', background='#f5f5f5', font=('Segoe UI', 10))
style.configure('TEntry', padding=5)
style.configure('TButton', font=('Segoe UI Semibold', 11), padding=8)
style.map('TButton', background=[('active', '#0052cc')], foreground=[('active', 'white')])

header = ttk.Label(root, text="ADB Pair & Connect", font=('Segoe UI Semibold', 14), background='#f5f5f5')
header.pack(pady=(15, 10))

content = ttk.Frame(root, padding=20)
content.pack(fill='x')

labels = ["IP Address", "Pairing Port", "Pairing Code", "Connect Port"]
entries = {}

cached_values = {label: "" for label in labels}

if os.path.exists(cache_file):
    try:
        with open(cache_file, "r") as f:
            cached_values.update(json.load(f))
    except Exception:
        pass

def on_enter(event, idx):
    val = event.widget.get().strip()
    if not val:
        messagebox.showerror("Input Required", f"{labels[idx]} cannot be empty.")
        return
    if idx < len(labels) - 1:
        entries[labels[idx+1]].focus_set()
    else:
        start_processing()

for i, label in enumerate(labels):
    lbl = ttk.Label(content, text=label)
    lbl.grid(row=i, column=0, sticky='w', pady=5)
    ent = ttk.Entry(content, width=30)
    ent.insert(0, cached_values.get(label, ""))
    ent.grid(row=i, column=1, pady=5, padx=(10, 0))
    ent.bind('<Return>', lambda e, idx=i: on_enter(e, idx))
    entries[label] = ent

button = ttk.Button(root, text="Pair & Connect", command=lambda: start_processing())
button.pack(pady=(5, 15))

class ADBDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Processing")
        self.geometry("300x140")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.flag_cancel = False
        self.procs = []

        ttk.Label(self, text="Processing...", font=('Segoe UI', 10)).pack(pady=(10, 0))
        self.message = ttk.Label(self, text="", font=('Segoe UI', 10))
        self.message.pack(pady=(5, 0))

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=260, mode='indeterminate')
        self.progress.pack(pady=(5, 0))
        self.cancel_btn = ttk.Button(self, text="Cancel", command=self.on_close)
        self.cancel_btn.pack(pady=(10, 5))
        self.progress.start()

    def on_close(self):
        self.flag_cancel = True
        for p in self.procs:
            try:
                p.kill()
            except Exception:
                pass
        self.parent.destroy()

    def update_message(self, msg):
        self.progress.stop()
        self.message.config(text=msg)
        self.cancel_btn.config(text="Close", command=self.on_close)

def run_adb_commands(dialog, ip, pair_port, code, connect_port):
    pair_address = f"{ip}:{pair_port}"
    connect_address = f"{ip}:{connect_port}"
    try:
        p1 = subprocess.Popen(["adb", "pair", pair_address], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        dialog.procs.append(p1)
        out1, _ = p1.communicate(input=code + "\n")
        if dialog.flag_cancel:
            return
        if "Successfully paired" in out1:
            dialog.after(0, lambda: dialog.update_message(f"Paired with {pair_address}"))
        else:
            dialog.after(0, lambda: dialog.update_message("Pairing Failed"))
            return

        p2 = subprocess.Popen(["adb", "connect", connect_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        dialog.procs.append(p2)
        out2, _ = p2.communicate()
        if dialog.flag_cancel:
            return
        if "connected" in out2.lower():
            dialog.after(0, lambda: dialog.update_message(f"Connected to {connect_address}"))
        else:
            dialog.after(0, lambda: dialog.update_message("Connection Failed"))
    except Exception as e:
        dialog.after(0, lambda: dialog.update_message(f"Error: {e}"))

def start_processing():
    values = {label: entries[label].get().strip() for label in labels}
    if not all(values.values()):
        messagebox.showerror("Missing Info", "All fields are required.")
        return

    try:
        with open(cache_file, "w") as f:
            json.dump(values, f)
    except Exception:
        pass

    ip = values["IP Address"]
    pair_port = values["Pairing Port"]
    code = values["Pairing Code"]
    connect_port = values["Connect Port"]
    connect_address = f"{ip}:{connect_port}"

    try:
        devices = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
        if connect_address in devices:
            messagebox.showinfo("Already Connected", f"Device already connected to {connect_address}")
            return
    except Exception:
        pass

    button.state(['disabled'])
    dialog = ADBDialog(root)
    threading.Thread(target=run_adb_commands, args=(dialog, ip, pair_port, code, connect_port), daemon=True).start()

root.mainloop()
