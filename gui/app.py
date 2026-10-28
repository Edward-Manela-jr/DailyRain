
"""RainfallDigitizer GUI — human review of whole-image OCR results.

Displays flagged cells (review = orange, empty = red) so a human can
verify or correct OCR values before exporting the final rainfall CSV.
"""

import csv
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

# Allow imports from the parent project.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from templates.chikuni import MONTHS, YEAR_BY_MONTH, STATION_ID, TABLE_BOUNDS


FLAG_COLORS = {
    "review": "#ffeb3b",   # yellow — value detected, verify
    "empty":  "#ff5252",   # red — no value detected, fill in
    "ok":     "#69f0ae",   # green — accepted
}


def compute_grid_boundaries(table):
    """Compute 33 horizontal and 14 vertical boundary positions."""
    x1 = table["x1"]
    y1 = table["y1"]
    x2 = table["x2"]
    y2 = table["y2"]
    horizontal_lines = [y1 + (y2 - y1) * i / 32 for i in range(33)]
    vertical_lines = [x1 + (x2 - x1) * i / 13 for i in range(14)]
    return horizontal_lines, vertical_lines


def load_records(csv_path):
    """Load rainfall records from CSV."""
    records = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def save_records(csv_path, records):
    """Save rainfall records back to CSV."""
    if not records:
        return
    fieldnames = list(records[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


class ReviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RainfallDigitizer — Human Review")
        self.root.geometry("1200x800")

        self.image_path = None
        self.records = []
        self.csv_path = None
        self.selected_index = None
        self.photo = None
        self.scale = 1.0

        self._build_ui()

    def _build_ui(self):
        # Top toolbar.
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Load Sheet Image", command=self.load_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load Review CSV", command=self.load_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Run Whole-Image OCR", command=self.run_ocr).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(toolbar, text="Save Final CSV", command=self.save_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Export Review CSV", command=self.export_review).pack(side=tk.LEFT, padx=2)

        # Status bar.
        self.status = ttk.Label(self.root, text="No data loaded.", anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        # Main paned window: image on left, review list on right.
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left: image canvas.
        left = ttk.Frame(paned)
        paned.add(left, weight=2)

        self.canvas = tk.Canvas(left, bg="gray90", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Right: review list + editor.
        right = ttk.Frame(paned)
        paned.add(right, weight=1)

        ttk.Label(right, text="Flagged Cells (review = yellow, empty = red)").pack(anchor=tk.W, padx=5, pady=2)

        # Treeview of flagged cells.
        columns = ("month", "day", "year", "rainfall", "flag")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", height=15)
        for col, text, width in (
            ("month", "Month", 90),
            ("day", "Day", 50),
            ("year", "Year", 60),
            ("rainfall", "Rainfall", 90),
            ("flag", "Flag", 70),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)

        scrollbar = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Editor panel.
        editor = ttk.LabelFrame(right, text="Edit Cell")
        editor.pack(fill=tk.X, padx=5, pady=5)

        self.lbl_cell = ttk.Label(editor, text="No cell selected")
        self.lbl_cell.pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(editor, text="Value:").pack(anchor=tk.W, padx=5)
        self.var_value = tk.StringVar()
        self.entry_value = ttk.Entry(editor, textvariable=self.var_value, width=20)
        self.entry_value.pack(anchor=tk.W, padx=5, pady=2)
        self.entry_value.bind("<Return>", lambda e: self.accept_value())

        btns = ttk.Frame(editor)
        btns.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btns, text="Accept", command=self.accept_value).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Correct", command=self.correct_value).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Skip", command=self.skip_cell).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text="Mark OK", command=self.mark_ok).pack(side=tk.LEFT, padx=2)

        # Cell image preview.
        preview = ttk.LabelFrame(right, text="Cell Preview")
        preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_label = ttk.Label(preview, text="Select a cell to preview")
        self.preview_label.pack(expand=True)

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Select rainfall sheet image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff"), ("All files", "*.*")]
        )
        if not path:
            return
        self.image_path = path
        self.display_image()
        self.status.config(text=f"Image loaded: {os.path.basename(path)}")

    def display_image(self):
        """Load and display the full sheet image on the canvas."""
        if not self.image_path:
            return
        try:
            image = Image.open(self.image_path)
        except Exception as exc:
            messagebox.showerror("Image error", f"Could not open image: {exc}")
            return

        # Scale to fit canvas (max 900x700).
        max_w, max_h = 900, 700
        w, h = image.size
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        self.scale = scale
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.config(width=image.width, height=image.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)


    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select review CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        self.csv_path = path
        self.records = load_records(path)
        self.populate_tree()
        self.status.config(text=f"Loaded {len(self.records)} records from {os.path.basename(path)}")

    def run_ocr(self):
        """Run whole-image OCR on the loaded image."""
        if not self.image_path:
            messagebox.showwarning("No image", "Please load a sheet image first.")
            return

        try:
            from whole_image_ocr.extract import extract_sheet, write_outputs
        except ImportError as exc:
            messagebox.showerror("Import error", f"Could not import whole_image_ocr: {exc}")
            return

        self.status.config(text="Running whole-image OCR (1 API call)...")
        self.root.update()

        try:
            result = extract_sheet(self.image_path)
            out_dir = "output_gui"
            records_path, review_path, summary_path = write_outputs(out_dir, result, self.image_path)

            self.csv_path = records_path
            self.records = load_records(records_path)
            self.populate_tree()
            self.status.config(
                text=f"OCR complete: {result['stats']['accepted']} accepted, "
                     f"{result['stats']['review']} review. CSV: {records_path}"
            )
            messagebox.showinfo(
                "OCR Complete",
                f"Total cells: {result['stats']['total_cells']}\n"
                f"Values detected: {result['stats']['ocr_cells']}\n"
                f"Auto-accepted: {result['stats']['accepted']}\n"
                f"Need review: {result['stats']['review']}"
            )
        except Exception as exc:
            messagebox.showerror("OCR error", str(exc))
            self.status.config(text="OCR failed.")

    def populate_tree(self):
        """Populate the treeview with flagged cells."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Tag colors.
        self.tree.tag_configure("review", background=FLAG_COLORS["review"])
        self.tree.tag_configure("empty", background=FLAG_COLORS["empty"])
        self.tree.tag_configure("ok", background=FLAG_COLORS["ok"])

        for idx, row in enumerate(self.records):
            flag = row.get("flag", "")
            rainfall = row.get("RAINFALL", "")
            values = (row.get("month", ""), row.get("day", ""), row.get("year", ""), rainfall, flag)
            tag = flag if flag in FLAG_COLORS else ""
            self.tree.insert("", tk.END, iid=str(idx), values=values, tags=(tag,))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        self.selected_index = idx
        row = self.records[idx]

        month = row.get("month", "")
        day = row.get("day", "")
        year = row.get("year", "")
        rainfall = row.get("RAINFALL", "")
        flag = row.get("flag", "")

        self.lbl_cell.config(text=f"{month.capitalize()} day {day} ({year}) — flag: {flag}")
        self.var_value.set(rainfall)

        # Show cell preview cropped from the main image.
        self.show_cell_preview(idx)

    def show_cell_preview(self, idx):
        """Crop and display the cell from the main image."""
        if not self.image_path:
            return
        row = self.records[idx]
        month = row.get("month", "")
        day = int(row.get("day", "0"))

        try:
            from PIL import Image as PILImage
            image = PILImage.open(self.image_path)
        except Exception:
            return

        horizontal, vertical = compute_grid_boundaries(TABLE_BOUNDS)

        # Find column index for month.
        try:
            month_index = MONTHS.index(month.lower())
        except ValueError:
            return

        row_index = day  # day 1 -> horizontal[1], etc.
        col_index = month_index + 1

        if row_index + 1 >= len(horizontal) or col_index + 1 >= len(vertical):
            return

        y1 = int(horizontal[row_index])
        y2 = int(horizontal[row_index + 1])
        x1 = int(vertical[col_index])
        x2 = int(vertical[col_index + 1])

        cell = image.crop((x1, y1, x2, y2))

        # Scale up for preview.
        scale = 4
        cell = cell.resize((cell.width * scale, cell.height * scale), PILImage.LANCZOS)

        self.photo = ImageTk.PhotoImage(cell)
        self.preview_label.config(image=self.photo, text="")

    def accept_value(self):
        """Accept current value and mark OK."""
        if self.selected_index is None:
            return
        row = self.records[self.selected_index]
        row["RAINFALL"] = self.var_value.get().strip()
        row["flag"] = "ok"
        self.records[self.selected_index] = row
        self.populate_tree()
        self.tree.selection_set(str(self.selected_index))
        self.status.config(text=f"Cell {self.selected_index} marked OK.")

    def correct_value(self):
        """Correct the value (same as accept but keeps flag for re-review)."""
        if self.selected_index is None:
            return
        row = self.records[self.selected_index]
        row["RAINFALL"] = self.var_value.get().strip()
        row["flag"] = "review"
        self.records[self.selected_index] = row
        self.populate_tree()
        self.tree.selection_set(str(self.selected_index))
        self.status.config(text=f"Cell {self.selected_index} corrected.")

    def skip_cell(self):
        """Skip this cell (leave as-is)."""
        if self.selected_index is None:
            return
        self.status.config(text=f"Cell {self.selected_index} skipped.")
        self.tree.selection_remove(str(self.selected_index))
        self.selected_index = None
        self.lbl_cell.config(text="No cell selected")
        self.var_value.set("")
        self.preview_label.config(image="", text="Select a cell to preview")
        self.photo = None

    def mark_ok(self):
        """Mark cell as OK without changing value."""
        if self.selected_index is None:
            return
        row = self.records[self.selected_index]
        row["flag"] = "ok"
        self.records[self.selected_index] = row
        self.populate_tree()
        self.tree.selection_set(str(self.selected_index))
        self.status.config(text=f"Cell {self.selected_index} marked OK.")

    def save_csv(self):
        """Save the final rainfall CSV."""
        if not self.csv_path:
            messagebox.showwarning("No CSV", "No data loaded to save.")
            return
        save_records(self.csv_path, self.records)
        self.status.config(text=f"Saved {len(self.records)} records to {self.csv_path}")
        messagebox.showinfo("Saved", f"Final CSV saved to:\n{self.csv_path}")

    def export_review(self):
        """Export only flagged cells to a review CSV."""
        if not self.records:
            messagebox.showwarning("No data", "No records to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export review CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        flagged = [r for r in self.records if r.get("flag") in ("review", "empty")]
        if not flagged:
            messagebox.showinfo("No flagged cells", "No cells need review.")
            return

        fieldnames = list(flagged[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flagged)

        self.status.config(text=f"Exported {len(flagged)} flagged cells to {path}")
        messagebox.showinfo("Exported", f"{len(flagged)} flagged cells exported to:\n{path}")


def main():
    root = tk.Tk()
    app = ReviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
