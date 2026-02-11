import qrcode, pyperclip, os, re, sys, ctypes, shutil, json
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# --- PYINSTALLER PATH HELPER ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- SYSTEM & DPI ---
if sys.platform.startswith("win"):
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('qr.monitor.final.v2026')
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: ctypes.windll.user32.SetProcessDPIAware()

class QRApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QR Monitor")
        self.root.attributes("-topmost", True)
        
        self.icon_file = resource_path("qr-code.ico")
        try: self.root.iconbitmap(self.icon_file)
        except: pass
        
        # UI & Grid Configuration
        self.APP_W, self.APP_H = 260, 320
        self.CARD_W, self.CARD_H, self.MARGIN = 220, 260, 20
        self.GRID_X, self.GRID_Y = self.CARD_W + self.MARGIN, self.CARD_H + self.MARGIN
        self.MAX_COLS = 5
        self.ORDER_FILE = "qr_order_config.json"

        # Position Main Window (Bottom Right - Draggable)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{self.APP_W}x{self.APP_H}+{sw - self.APP_W - 20}+{sh - self.APP_H - 80}")

        self.is_paused, self.save_dir, self.perm_dir = False, "saved_qrs", "permanent"
        for folder in [self.save_dir, self.perm_dir]: os.makedirs(folder, exist_ok=True)
        
        self.gallery_win, self.canvas = None, None
        self.last_text = pyperclip.paste().strip()
        self.context_menu = tk.Menu(self.root, tearoff=0)
        
        self.setup_ui()
        self.ensure_gallery()
        self.refresh_gallery()
        
        self.check_clipboard()
        self.root.mainloop()

    def setup_ui(self):
        tk.Label(self.root, text="QR MONITOR", font=("Arial", 10, "bold")).pack(pady=15)
        self.status_label = tk.Label(self.root, text="Status: Monitoring", fg="green")
        self.status_label.pack(pady=5)
        tk.Button(self.root, text="Open Gallery", command=self.ensure_gallery, width=22).pack(pady=2)
        tk.Button(self.root, text="Clear Temporary", command=self.clear_saved_qrs, fg="white", bg="#d9534f", width=22).pack(pady=2)
        self.pause_btn = tk.Button(self.root, text="Pause Program", command=self.toggle_pause, width=22)
        self.pause_btn.pack(pady=10)

    def ensure_gallery(self):
        """Creates a gallery sized for 5x3 with extra space on the right side."""
        if self.gallery_win is None or not tk.Toplevel.winfo_exists(self.gallery_win):
            self.gallery_win = tk.Toplevel(self.root)
            self.gallery_win.title("QR Gallery (5x3 View)")
            
            # Added +40 pixels to win_w for extra right-side spacing
            win_w = (5 * self.GRID_X) + 60 
            win_h = (3 * self.GRID_Y) + 20
            self.gallery_win.geometry(f"{win_w}x{win_h}+50+50")
            
            try: self.gallery_win.iconbitmap(self.icon_file)
            except: pass
            
            self.canvas = tk.Canvas(self.gallery_win, bg="#f0f0f0", highlightthickness=0)
            vsb = ttk.Scrollbar(self.gallery_win, orient="vertical", command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True)
            self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def get_logical_coords(self, index):
        row, col = divmod(index, self.MAX_COLS)
        return col * self.GRID_X + 20, row * self.GRID_Y + 20

    def refresh_gallery(self):
        """Strict Sort: Permanent (Gold) first, then Temp. Prevents overlap."""
        for widget in self.canvas.winfo_children(): widget.destroy()
        
        perms = sorted([f for f in os.listdir(self.perm_dir) if f.endswith(".png")])
        temps = sorted([f for f in os.listdir(self.save_dir) if f.endswith(".png")])
        
        saved_order = []
        if os.path.exists(self.ORDER_FILE):
            try:
                with open(self.ORDER_FILE, "r") as f: saved_order = json.load(f)
            except: pass
        
        current_files = perms + temps
        ordered_list = [f for f in saved_order if f in current_files]
        ordered_list += [f for f in current_files if f not in ordered_list]
        
        final_perms = [f for f in ordered_list if f in perms]
        final_temps = [f for f in ordered_list if f in temps]
        final_list = final_perms + final_temps

        for i, filename in enumerate(final_list):
            is_perm = filename in perms
            path = os.path.join(self.perm_dir if is_perm else self.save_dir, filename)
            try:
                img = Image.open(path)
                self.create_card(img, filename, is_perm, i)
            except: pass
        
        self.save_order(final_list)
        self.update_scroll()

    def create_card(self, qr_img, filename, is_perm, index):
        x, y = self.get_logical_coords(index)
        card = tk.Frame(self.canvas, bd=0, bg="white", highlightthickness=2)
        card.config(highlightbackground="gold" if is_perm else "white")
        card.place(x=x, y=y, width=self.CARD_W, height=self.CARD_H)
        card.filename = filename
        
        img_tk = ImageTk.PhotoImage(qr_img.resize((180, 180), Image.Resampling.LANCZOS))
        lbl_img = tk.Label(card, image=img_tk, bg="white")
        lbl_img.image = img_tk; lbl_img.pack(pady=10)
        tk.Label(card, text=filename.replace(".png", "")[:25], font=("Segoe UI", 9, "bold" if is_perm else "normal"), bg="white").pack()

        def on_drag(e):
            card.lift()
            card.place(x=card.winfo_x()+(e.x-card._ox), y=card.winfo_y()+(e.y-card._oy))

        def on_release(e):
            target_col = round((card.winfo_x() - 20) / self.GRID_X)
            target_row = round((card.winfo_y() - 20) / self.GRID_Y)
            target_idx = max(0, (target_row * self.MAX_COLS) + target_col)
            self.reorder_cards(card.filename, target_idx)

        for w in (card, lbl_img):
            w.bind("<Button-1>", lambda e: (setattr(card, '_ox', e.x), setattr(card, '_oy', e.y)))
            w.bind("<B1-Motion>", on_drag)
            w.bind("<ButtonRelease-1>", on_release)
            w.bind("<Button-3>", lambda e, c=card: self.show_context_menu(e, c))

    def reorder_cards(self, moving_file, target_idx):
        if not os.path.exists(self.ORDER_FILE): return
        with open(self.ORDER_FILE, "r") as f: current_order = json.load(f)
        if moving_file in current_order:
            current_order.remove(moving_file)
            target_idx = min(target_idx, len(current_order))
            current_order.insert(target_idx, moving_file)
            with open(self.ORDER_FILE, "w") as f: json.dump(current_order, f)
        self.refresh_gallery()

    def save_order(self, file_list):
        with open(self.ORDER_FILE, "w") as f: json.dump(file_list, f)

    def show_context_menu(self, event, card):
        self.context_menu.delete(0, tk.END)
        self.context_menu.add_command(label="Toggle Permanent (Gold)", command=lambda: self.toggle_perm(card))
        self.context_menu.add_command(label="Delete", command=lambda: self.delete_card(card))
        self.context_menu.post(event.x_root, event.y_root)

    def toggle_perm(self, card):
        src, dst = (self.perm_dir, self.save_dir) if "gold" in card.cget("highlightbackground") else (self.save_dir, self.perm_dir)
        try:
            shutil.move(os.path.join(src, card.filename), os.path.join(dst, card.filename))
            self.refresh_gallery()
        except: pass

    def delete_card(self, card):
        if messagebox.askyesno("Delete", "Remove this QR code?"):
            path = os.path.join(self.perm_dir if "gold" in card.cget("highlightbackground") else self.save_dir, card.filename)
            try: 
                os.remove(path)
                self.refresh_gallery()
            except: pass

    def clear_saved_qrs(self):
        if messagebox.askyesno("Clear", "Delete all temporary (White) QR codes?"):
            for f in os.listdir(self.save_dir):
                try: os.remove(os.path.join(self.save_dir, f))
                except: pass
            self.refresh_gallery()

    def update_scroll(self):
        children = self.canvas.winfo_children()
        max_y = max([w.winfo_y() + self.CARD_H + 40 for w in children]) if children else 850
        # Increased scrollregion width slightly as well
        self.canvas.config(scrollregion=(0, 0, (self.MAX_COLS * self.GRID_X) + 40, max_y))

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        lbl, col = ("Paused", "orange") if self.is_paused else ("Monitoring", "green")
        self.status_label.config(text=f"Status: {lbl}", fg=col)

    def check_clipboard(self):
        if not self.is_paused:
            try:
                curr = pyperclip.paste().strip()
                if curr and curr != self.last_text:
                    self.last_text = curr
                    safe = re.sub(r'\W+', '_', curr)[:30] + ".png"
                    qrcode.make(curr).save(os.path.join(self.save_dir, safe))
                    if self.gallery_win: self.refresh_gallery()
            except: pass
        self.root.after(1000, self.check_clipboard)

if __name__ == "__main__":
    QRApp()
