"""
bmi_gui_enhanced.py

Enhanced BMI Calculator & Tracker
- Tkinter GUI with dark/light theme
- Profile photo upload (Pillow)
- Animated progress bar during calculation
- Tabs: Calculator + Tips
- SQLite storage + matplotlib plotting
- Export CSV, delete records

Run:
python bmi_gui_enhanced.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import PhotoImage
import sqlite3
from datetime import datetime
import math
import csv
import os
from PIL import Image, ImageTk  # pillow

# Matplotlib for plotting
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_FILE = "bmi_data.db"

# ----------------------
# Data layer
# ----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            units TEXT NOT NULL,
            bmi REAL NOT NULL,
            category TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_record(username, weight, height, units, bmi, category):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO records (username, weight, height, units, bmi, category, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, weight, height, units, bmi, category, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_user_list():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT username FROM records ORDER BY username")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def get_records_for_user(username):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT timestamp, weight, height, units, bmi, category FROM records WHERE username=? ORDER BY timestamp", (username,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_user_records(username):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM records WHERE username=?", (username,))
    conn.commit()
    conn.close()

# ----------------------
# BMI logic / utils
# ----------------------
def calc_bmi_metric(weight_kg, height_m):
    if height_m <= 0:
        return None
    return weight_kg / (height_m * height_m)

def calc_bmi_imperial(weight_lb, height_in):
    if height_in <= 0:
        return None
    return 703 * weight_lb / (height_in * height_in)

def categorize_bmi(bmi):
    if bmi is None:
        return "Invalid"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obesity"

def validate_inputs(username, weight_str, height_str, units):
    if not username.strip():
        return False, "Please enter a name."
    try:
        weight = float(weight_str)
    except ValueError:
        return False, "Weight must be a number."
    try:
        height = float(height_str)
    except ValueError:
        return False, "Height must be a number."
    if units == "metric":
        if weight <= 0 or weight > 500:
            return False, "Enter weight in kg between 0 and 500."
        if height <= 0 or height > 3:
            return False, "Enter height in meters (e.g., 1.75)."
    else:
        if weight <= 0 or weight > 1100:
            return False, "Enter weight in pounds between 0 and 1100."
        if height <= 0 or height > 120:
            return False, "Enter height in inches (e.g., 69)."
    return True, ""

# ----------------------
# UI / App
# ----------------------
class BMIGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator & Tracker (Enhanced)")
        self.geometry("1024x680")
        self.resizable(False, False)
        init_db()

        # Style
        self.style = ttk.Style(self)
        self.dark_mode = tk.BooleanVar(value=False)
        self.apply_theme()

        # Top bar
        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", padx=10, pady=6)
        ttk.Label(top_bar, text="BMI Calculator & Tracker", font=("Helvetica", 16, "bold")).pack(side="left")
        ttk.Checkbutton(top_bar, text="Dark Mode", variable=self.dark_mode, command=self.toggle_theme).pack(side="right")

        # Main frame (left/right)
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=6)

        # Left panel
        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0,10))

        # Profile photo area
        pframe = ttk.LabelFrame(left, text="Profile", padding=8)
        pframe.pack(fill="x")
        self.photo_label = ttk.Label(pframe, text="No Photo", width=18, anchor="center", background="#ddd")
        self.photo_label.pack(padx=6, pady=6)
        ttk.Button(pframe, text="Upload Photo", command=self.upload_photo).pack(fill="x", padx=6, pady=(0,6))

        # Input card
        card = ttk.LabelFrame(left, text="BMI Input", padding=8)
        card.pack(fill="x", pady=(8,0))

        ttk.Label(card, text="Name:").pack(anchor="w", pady=(2,0))
        self.name_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.name_var).pack(fill="x", pady=2)

        self.unit_var = tk.StringVar(value="metric")
        uframe = ttk.Frame(card)
        uframe.pack(fill="x", pady=6)
        ttk.Radiobutton(uframe, text="Metric (kg, m)", variable=self.unit_var, value="metric").pack(side="left", padx=2)
        ttk.Radiobutton(uframe, text="Imperial (lb, in)", variable=self.unit_var, value="imperial").pack(side="left", padx=2)

        ttk.Label(card, text="Weight:").pack(anchor="w", pady=(4,0))
        self.weight_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.weight_var).pack(fill="x", pady=2)

        ttk.Label(card, text="Height:").pack(anchor="w", pady=(4,0))
        self.height_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.height_var).pack(fill="x", pady=2)

        # Buttons and progress
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill="x", pady=8)
        ttk.Button(btn_frame, text="Calculate BMI", command=self.on_calculate_with_animation).pack(fill="x")
        ttk.Button(btn_frame, text="Save Record", command=self.on_save).pack(fill="x", pady=(6,0))
        ttk.Button(btn_frame, text="Export CSV", command=self.on_export).pack(fill="x", pady=(6,0))

        self.progress = ttk.Progressbar(card, mode="indeterminate")
        self.progress.pack(fill="x", pady=(8,0))

        # Results
        res_frame = ttk.LabelFrame(left, text="Result", padding=8)
        res_frame.pack(fill="x", pady=(8,0))
        self.result_bmi_var = tk.StringVar(value="BMI: -")
        self.result_cat_var = tk.StringVar(value="Category: -")
        ttk.Label(res_frame, textvariable=self.result_bmi_var, font=("Helvetica", 12, "bold")).pack(anchor="w")
        ttk.Label(res_frame, textvariable=self.result_cat_var).pack(anchor="w")

        # Users & history list
        hist_frame = ttk.LabelFrame(left, text="Users / History", padding=8)
        hist_frame.pack(fill="both", expand=True, pady=(8,0))
        self.user_listbox = tk.Listbox(hist_frame, height=8)
        self.user_listbox.pack(fill="x")
        self.user_listbox.bind("<<ListboxSelect>>", self.on_user_select)
        ttk.Button(hist_frame, text="Refresh Users", command=self.refresh_users).pack(fill="x", pady=(6,0))
        ttk.Button(hist_frame, text="Delete User Records", command=self.on_delete_user).pack(fill="x", pady=(6,0))

        # Right panel with tabs (calculator main tab + tips)
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        # Tab: Main visualization / history
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Tracker")

        # Plot area
        plot_frame = ttk.LabelFrame(main_tab, text="BMI Trend", padding=8)
        plot_frame.pack(fill="x", padx=6, pady=(8,6))
        self.figure = Figure(figsize=(8,3.0), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("BMI over Time")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("BMI")
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # History table
        hist_table_frame = ttk.LabelFrame(main_tab, text="History (selected user)", padding=8)
        hist_table_frame.pack(fill="both", expand=True, padx=6, pady=(6,6))
        self.tree = ttk.Treeview(hist_table_frame, columns=("ts","weight","height","units","bmi","cat"), show="headings", height=8)
        for col, head in [("ts","Time"), ("weight","Weight"), ("height","Height"), ("units","Units"), ("bmi","BMI"), ("cat","Category")]:
            self.tree.heading(col, text=head)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Stats
        stats_frame = ttk.Frame(main_tab)
        stats_frame.pack(fill="x", padx=6, pady=(0,6))
        self.stat_text = tk.StringVar(value="Stats: -")
        ttk.Label(stats_frame, textvariable=self.stat_text).pack(anchor="w")

        # Tab: Tips & Info
        tips_tab = ttk.Frame(notebook)
        notebook.add(tips_tab, text="BMI Tips")
        self.build_tips_tab(tips_tab)

        # initial
        self.profile_image = None
        self.refresh_users()

    # theme
    def apply_theme(self):
        # Basic light/dark palette
        if getattr(self, "dark_mode", None) and self.dark_mode.get():
            self.style.configure(".", background="#2b2b2b", foreground="#e6e6e6", fieldbackground="#3a3a3a")
            self.style.configure("Treeview", background="#2f2f2f", fieldbackground="#2f2f2f", foreground="#e6e6e6")
            self.configure(background="#252525")
        else:
            self.style.configure(".", background="#f0f0f0", foreground="#111111", fieldbackground="#ffffff")
            self.style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#111111")
            self.configure(background="#eeeeee")

    def toggle_theme(self):
        self.apply_theme()

    # ----------------------
    # Photo
    # ----------------------
    def upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Image files","*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if not path:
            return
        try:
            img = Image.open(path)
            img = img.convert("RGBA")
            img.thumbnail((150,150), Image.LANCZOS)
            self.profile_image = ImageTk.PhotoImage(img)
            self.photo_label.configure(image=self.profile_image, text="")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open image: {e}")

    # ----------------------
    # Actions
    # ----------------------
    def on_calculate_with_animation(self):
        # Start progress animation and call actual calculation after delay
        self.progress.start(10)  # small step speed
        # simulate a short operation (0.6s)
        self.after(650, self._calculate_and_stop_progress)

    def _calculate_and_stop_progress(self):
        self.progress.stop()
        self.on_calculate()

    def on_calculate(self):
        username = self.name_var.get().strip()
        weight_s = self.weight_var.get().strip()
        height_s = self.height_var.get().strip()
        units = self.unit_var.get()
        ok, msg = validate_inputs(username, weight_s, height_s, units)
        if not ok:
            messagebox.showerror("Invalid input", msg)
            return
        weight = float(weight_s)
        height = float(height_s)
        if units == "metric":
            bmi = calc_bmi_metric(weight, height)
        else:
            bmi = calc_bmi_imperial(weight, height)
        if bmi is None or math.isinf(bmi) or math.isnan(bmi):
            messagebox.showerror("Calculation error", "Could not compute BMI with given values.")
            return
        bmi_r = round(bmi, 2)
        cat = categorize_bmi(bmi)
        self.result_bmi_var.set(f"BMI: {bmi_r}")
        self.result_cat_var.set(f"Category: {cat}")
        self._last = (username, weight, height, units, bmi_r, cat)

    def on_save(self):
        if not hasattr(self, "_last"):
            messagebox.showinfo("Info", "First calculate BMI, then save.")
            return
        username, weight, height, units, bmi, cat = self._last
        save_record(username, weight, height, units, bmi, cat)
        messagebox.showinfo("Saved", "Record saved to local database.")
        self.refresh_users()

    def refresh_users(self):
        users = get_user_list()
        self.user_listbox.delete(0, tk.END)
        for u in users:
            self.user_listbox.insert(tk.END, u)
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.ax.set_title("BMI over Time")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("BMI")
        self.canvas.draw()
        self.stat_text.set("Stats: -")

    def on_user_select(self, event=None):
        sel = self.user_listbox.curselection()
        if not sel:
            return
        username = self.user_listbox.get(sel[0])
        recs = get_records_for_user(username)
        self.tree.delete(*self.tree.get_children())
        times = []
        bmis = []
        for row in recs:
            ts, weight, height, units, bmi, cat = row
            display_ts = ts.replace("T", " ")[:19]
            self.tree.insert("", tk.END, values=(display_ts, weight, height, units, bmi, cat))
            try:
                times.append(datetime.fromisoformat(ts))
                bmis.append(float(bmi))
            except Exception:
                pass
        # plot
        self.ax.clear()
        self.ax.set_title(f"BMI over Time — {username}")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("BMI")
        if times and bmis:
            self.ax.plot(times, bmis, marker='o', linestyle='-', color="#1f77b4")
            self.ax.annotate(f"{bmis[-1]:.1f}", (times[-1], bmis[-1]))
            self.ax.set_ylim(min(bmis) - 2, max(bmis) + 2)
            self.figure.autofmt_xdate()
            self.canvas.draw()
            avg = sum(bmis) / len(bmis)
            mn = min(bmis)
            mx = max(bmis)
            self.stat_text.set(f"Stats: avg={avg:.2f}, min={mn:.2f}, max={mx:.2f}, samples={len(bmis)}")
        else:
            self.canvas.draw()
            self.stat_text.set("Stats: no data")

    def on_delete_user(self):
        sel = self.user_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a user first.")
            return
        username = self.user_listbox.get(sel[0])
        if messagebox.askyesno("Confirm", f"Delete all records for {username}?"):
            delete_user_records(username)
            self.refresh_users()

    def on_export(self):
        sel = self.user_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a user to export.")
            return
        username = self.user_listbox.get(sel[0])
        recs = get_records_for_user(username)
        if not recs:
            messagebox.showinfo("Info", "No records to export.")
            return
        default = f"{username}_bmi_history.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default, filetypes=[("CSV files","*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp","weight","height","units","bmi","category"])
                for r in recs:
                    writer.writerow(r)
            messagebox.showinfo("Exported", f"Exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export: {e}")

    # ----------------------
    # Tips tab content
    # ----------------------
    def build_tips_tab(self, parent):
        frm = ttk.Frame(parent, padding=12)
        frm.pack(fill="both", expand=True)
        title = ttk.Label(frm, text="BMI Tips & Guidance", font=("Helvetica", 14, "bold"))
        title.pack(anchor="w")
        txt = tk.Text(frm, wrap="word", height=16, padx=8, pady=8)
        txt.pack(fill="both", expand=True, pady=(8,0))
        content = (
            "What is BMI?\n"
            "BMI (Body Mass Index) is a rough estimate of healthy body weight for an adult.\n\n"
            "Categories:\n"
            "- Underweight: BMI < 18.5\n"
            "- Normal: 18.5 ≤ BMI < 25\n"
            "- Overweight: 25 ≤ BMI < 30\n"
            "- Obesity: BMI ≥ 30\n\n"
            "Tips:\n"
            "- Aim for a balanced diet with vegetables, lean protein, and whole grains.\n"
            "- Stay active — at least 150 minutes of moderate exercise per week.\n"
            "- Consult a healthcare professional for personalized guidance.\n"
            "- BMI is a simple measure; it doesn't account for muscle mass or distribution.\n\n"
            "Using the app:\n"
            "- Enter name, weight & height and choose units.\n"
            "- Click 'Calculate BMI' to compute; use 'Save Record' to save history.\n"
            "- Use the 'Tracker' tab to view history and graphs. Export CSV if needed."
        )
        txt.insert("1.0", content)
        txt.config(state="disabled")

# ----------------------
# Run app
# ----------------------
if __name__ == "__main__":
    init_db()
    app = BMIGUI()
    app.mainloop()



