import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import csv  # Required for quoting constants like csv.QUOTE_NONNUMERIC


class CSVMagicEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV Magic Editor ✨")
        self.geometry("600x500")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.df = None
        self.file_path = None

        style = ttk.Style(self)
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')

        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        load_frame = ttk.LabelFrame(main_frame, text="1. Load CSV File", padding="10 10")
        load_frame.pack(fill=tk.X, pady=5)

        self.load_button = ttk.Button(load_frame, text="Load CSV File", command=self.load_csv)
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))
        self.file_label = ttk.Label(load_frame, text="No file loaded.")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        error_handling_frame = ttk.LabelFrame(main_frame, text="CSV Parsing Options", padding="10 10")
        error_handling_frame.pack(fill=tk.X, pady=5)

        self.error_handling_var = tk.StringVar(value="Strict (fail on error)")
        error_options = ["Strict (fail on error)", "Skip bad lines"]
        self.error_handling_menu = ttk.Combobox(error_handling_frame, textvariable=self.error_handling_var,
                                                values=error_options, state="readonly", width=25)
        self.error_handling_menu.pack(side=tk.LEFT)
        ttk.Label(error_handling_frame, text=" (Choose before loading if errors occur)").pack(side=tk.LEFT, padx=5)

        filter_frame = ttk.LabelFrame(main_frame, text="2. Define Filter Condition", padding="10 10")
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="Filter by Column:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.filter_column_var = tk.StringVar()
        self.filter_column_combo = ttk.Combobox(filter_frame, textvariable=self.filter_column_var, state="disabled",
                                                width=25)
        self.filter_column_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        self.filter_column_combo.bind("<<ComboboxSelected>>", self.update_filter_values)

        ttk.Label(filter_frame, text="Where Value is:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.filter_value_var = tk.StringVar()
        self.filter_value_combo = ttk.Combobox(filter_frame, textvariable=self.filter_value_var, state="disabled",
                                               width=25)
        self.filter_value_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        filter_frame.columnconfigure(1, weight=1)

        update_frame = ttk.LabelFrame(main_frame, text="3. Specify Update", padding="10 10")
        update_frame.pack(fill=tk.X, pady=5)

        ttk.Label(update_frame, text="Column to Update:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.target_column_var = tk.StringVar()
        self.target_column_combo = ttk.Combobox(update_frame, textvariable=self.target_column_var, state="disabled",
                                                width=25)
        self.target_column_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(update_frame, text="Set New Value to:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.new_value_entry = ttk.Entry(update_frame, state="disabled", width=27)
        self.new_value_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        update_frame.columnconfigure(1, weight=1)

        self.process_button = ttk.Button(main_frame, text="Apply Changes & Save As...",
                                         command=self.process_and_save_csv, state="disabled")
        self.process_button.pack(pady=15)

        self.status_var = tk.StringVar(value="Welcome! Load a CSV to begin.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="5")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        self.file_path = file_path
        error_mode = self.error_handling_var.get()

        try:
            self.status_var.set(f"Loading {self.file_path.split('/')[-1]}...")
            self.update_idletasks()

            if error_mode == "Skip bad lines":
                self.df = pd.read_csv(self.file_path, on_bad_lines='skip', engine='python')
                self.status_var.set(f"Loaded {self.file_path.split('/')[-1]} (skipped bad lines if any).")
            else:
                self.df = pd.read_csv(self.file_path)
                self.status_var.set(f"Successfully loaded {self.file_path.split('/')[-1]}.")

            if self.df.empty:
                messagebox.showwarning("Warning", "The loaded CSV is empty or became empty after skipping lines.")
                self.reset_ui_on_error()
                self.status_var.set("Loaded CSV is empty.")
                return

            self.file_label.config(text=self.file_path.split('/')[-1])
            columns = list(self.df.columns)

            self.filter_column_combo.config(values=columns, state="readonly")
            self.target_column_combo.config(values=columns, state="readonly")

            self.filter_column_var.set("")
            self.filter_value_var.set("")
            self.filter_value_combo.config(values=[], state="disabled")
            self.target_column_var.set("")
            self.new_value_entry.delete(0, tk.END)

            self.new_value_entry.config(state="normal")
            self.process_button.config(state="normal")

        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found: {self.file_path}")
            self.status_var.set("Error: File not found.")
            self.reset_ui_on_error()
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", "The CSV file is empty (no columns or data).")
            self.status_var.set("Error: CSV file is empty.")
            self.reset_ui_on_error()
        except pd.errors.ParserError as e:
            messagebox.showerror("CSV Parsing Error",
                                 f"Error parsing CSV file: {e}\n\n"
                                 f"Details: This often means the file has rows with an unexpected number of fields or other structural issues. "
                                 f"Try selecting 'Skip bad lines' from the 'CSV Parsing Options' dropdown and loading the file again.")
            self.status_var.set("Error parsing CSV. Try 'Skip bad lines'.")
            self.reset_ui_on_error()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during loading: {e}")
            self.status_var.set(f"An unexpected error occurred: {e}")
            self.reset_ui_on_error()

    def reset_ui_on_error(self):
        self.df = None
        self.file_label.config(text="No file loaded.")
        self.filter_column_combo.config(values=[], state="disabled")
        self.filter_value_combo.config(values=[], state="disabled")
        self.target_column_combo.config(values=[], state="disabled")
        self.new_value_entry.config(state="disabled")
        self.process_button.config(state="disabled")

        self.filter_column_var.set("")
        self.filter_value_var.set("")
        self.target_column_var.set("")
        if hasattr(self, 'new_value_entry'):
            self.new_value_entry.delete(0, tk.END)

    def update_filter_values(self, event=None):
        if self.df is not None and self.filter_column_var.get():
            selected_col = self.filter_column_var.get()
            try:
                unique_values = sorted(self.df[selected_col].astype(str).unique().tolist())
                self.filter_value_combo.config(values=unique_values, state="readonly")
                if unique_values:
                    self.filter_value_var.set(unique_values[0])
                else:
                    self.filter_value_var.set("")
                self.status_var.set(f"Populated filter values for '{selected_col}'.")
            except Exception as e:
                self.status_var.set(f"Error updating filter values: {e}")
                self.filter_value_combo.config(values=[], state="disabled")
                self.filter_value_var.set("")
        else:
            self.filter_value_combo.config(values=[], state="disabled")
            self.filter_value_var.set("")

    def process_and_save_csv(self):
        if self.df is None:
            messagebox.showwarning("Warning", "No CSV data loaded.")
            self.status_var.set("No data to process. Load a CSV first.")
            return

        filter_col = self.filter_column_var.get()
        filter_val_str = self.filter_value_var.get()
        target_col = self.target_column_var.get()
        new_val_input = self.new_value_entry.get()

        if not filter_col:
            messagebox.showwarning("Input Missing", "Please select a 'Filter by Column'.")
            self.status_var.set("Filter column not selected.")
            return
        if not target_col:
            messagebox.showwarning("Input Missing", "Please select a 'Column to Update'.")
            self.status_var.set("Target column not selected.")
            return

        try:
            modified_df = self.df.copy()
            mask = modified_df[filter_col].astype(str) == filter_val_str

            if not mask.any():
                messagebox.showinfo("No Rows Matched",
                                    f"No rows found where '{filter_col}' (as string) is '{filter_val_str}'. No changes made.")
                self.status_var.set("No rows matched the filter.")
                return

            original_target_dtype = modified_df[target_col].dtype
            converted_new_val = new_val_input

            if new_val_input == "" and not (
                    pd.api.types.is_string_dtype(original_target_dtype) or original_target_dtype == 'object'):
                converted_new_val = pd.NA
            else:
                try:
                    if original_target_dtype != 'object' and converted_new_val is not pd.NA:
                        temp_series = pd.Series([new_val_input])
                        converted_new_val = temp_series.astype(original_target_dtype).iloc[0]
                except ValueError:
                    self.status_var.set(f"Warning: New value for '{target_col}' kept as string due to type mismatch.")
                except Exception:
                    self.status_var.set(
                        f"Warning: New value for '{target_col}' kept as string due to a type conversion issue.")

            modified_df.loc[mask, target_col] = converted_new_val

            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"edited_{self.file_path.split('/')[-1] if self.file_path else 'output.csv'}"
            )

            if save_path:
                # --- KEY CHANGE HERE ---
                # Explicitly set delimiter to comma (though it's default)
                # Change quoting to QUOTE_NONNUMERIC: quotes all fields that are not numbers.
                # This is often more compatible with systems that are picky about CSV formats.
                modified_df.to_csv(
                    save_path,
                    index=False,
                    sep=',',  # Explicitly comma delimiter
                    quoting=csv.QUOTE_NONNUMERIC  # Quote non-numeric fields
                )
                messagebox.showinfo("Success", f"Modified CSV saved to:\n{save_path}")
                self.status_var.set(f"Changes saved to {save_path.split('/')[-1]} (using QUOTE_NONNUMERIC).")
            else:
                self.status_var.set("Save operation cancelled.")

        except KeyError as e:
            messagebox.showerror("Error", f"Column not found: {e}. Please reload the file or check column names.")
            self.status_var.set(f"Error: Column {e} not found.")
        except Exception as e:
            messagebox.showerror("Processing Error", f"An error occurred during processing: {e}")
            self.status_var.set(f"Processing error: {e}")
            import traceback
            print("Error during processing details:", traceback.format_exc())

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit CSV Magic Editor?"):
            self.destroy()


if __name__ == "__main__":
    app = CSVMagicEditor()
    app.mainloop()
