import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os


class CSVEditorApp:
    def __init__(self, master):
        self.master = master
        master.title("CSV Editor")
        master.geometry("650x550")  # Adjusted size for better layout

        self.df = None
        self.modified_df = None
        self.input_file_path_display = tk.StringVar()  # For display
        self.full_input_file_path = None  # For internal use

        self.condition_column = tk.StringVar()
        self.condition_value = tk.StringVar()
        self.target_column = tk.StringVar()
        self.new_value = tk.StringVar()

        # --- UI Elements ---

        # Frame for file operations
        file_frame = ttk.LabelFrame(master, text="1. File Operations")
        file_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(file_frame, text="Load CSV", command=self.load_csv).pack(side=tk.LEFT, padx=5, pady=5)
        self.file_path_label = ttk.Label(file_frame, textvariable=self.input_file_path_display)
        self.file_path_label.pack(side=tk.LEFT, padx=5, pady=5, fill="x", expand=True)
        self.input_file_path_display.set("No file loaded.")

        # Frame for specifying conditions and modifications
        edit_frame = ttk.LabelFrame(master, text="2. Define Changes")
        edit_frame.pack(padx=10, pady=(0, 10), fill="x")  # Reduced pady top

        # Condition Column
        ttk.Label(edit_frame, text="Filter Column (where condition applies):").grid(row=0, column=0, padx=5, pady=5,
                                                                                    sticky="w")
        self.combo_condition_column = ttk.Combobox(edit_frame, textvariable=self.condition_column, state="readonly",
                                                   width=30)
        self.combo_condition_column.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.combo_condition_column.bind("<<ComboboxSelected>>", self.update_condition_values_preview)

        # Condition Value Preview
        ttk.Label(edit_frame, text="Unique values in Filter Column:").grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        listbox_frame = ttk.Frame(edit_frame)  # Frame to hold listbox and scrollbar
        listbox_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.condition_values_listbox = tk.Listbox(listbox_frame, height=5, width=30)  # Height can be adjusted
        self.condition_values_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.condition_values_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.condition_values_listbox.configure(yscrollcommand=scrollbar.set)
        self.condition_values_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        # Condition Value
        ttk.Label(edit_frame, text="Filter Value (e.g., generalPlastics):").grid(row=2, column=0, padx=5, pady=5,
                                                                                 sticky="w")
        self.entry_condition_value = ttk.Entry(edit_frame, textvariable=self.condition_value, width=33)
        self.entry_condition_value.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Target Column
        ttk.Label(edit_frame, text="Target Column (to change values in):").grid(row=3, column=0, padx=5, pady=5,
                                                                                sticky="w")
        self.combo_target_column = ttk.Combobox(edit_frame, textvariable=self.target_column, state="readonly", width=30)
        self.combo_target_column.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # New Value
        ttk.Label(edit_frame, text="New Value (to set in Target Column):").grid(row=4, column=0, padx=5, pady=5,
                                                                                sticky="w")
        self.entry_new_value = ttk.Entry(edit_frame, textvariable=self.new_value, width=33)
        self.entry_new_value.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        edit_frame.grid_columnconfigure(1, weight=1)  # Make comboboxes and entries expand

        # Frame for actions
        action_frame = ttk.LabelFrame(master, text="3. Execute and Save")
        action_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(action_frame, text="Apply Changes to Preview", command=self.apply_changes).pack(side=tk.LEFT, padx=5,
                                                                                                   pady=5)
        ttk.Button(action_frame, text="Save Modified CSV As...", command=self.save_csv).pack(side=tk.LEFT, padx=5,
                                                                                             pady=5)

        # Status Bar
        self.status_bar = ttk.Label(master, text="Status: Ready", relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side=tk.BOTTOM, fill="x", padx=10, pady=5)

    def on_listbox_select(self, event=None):
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            value = widget.get(index)
            # Avoid setting if it's an indicator like "... (and more)"
            if not value.startswith("... (and more"):
                self.condition_value.set(value)

    def update_condition_values_preview(self, event=None):
        self.condition_values_listbox.delete(0, tk.END)
        selected_col = self.condition_column.get()
        if self.df is not None and selected_col:
            try:
                unique_values = self.df[
                    selected_col].dropna().unique()  # dropna to avoid issues with string conversion of NaN
                # Limit the number of unique values displayed
                display_limit = 100
                count = 0
                for val in unique_values:
                    self.condition_values_listbox.insert(tk.END, str(val))
                    count += 1
                    if count >= display_limit and len(unique_values) > display_limit:
                        self.condition_values_listbox.insert(tk.END,
                                                             f"... (and {len(unique_values) - display_limit} more)")
                        break
            except Exception as e:
                self.condition_values_listbox.insert(tk.END, "Error fetching values.")
                self.update_status(f"Error updating preview: {e}")

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if not file_path:
            self.update_status("File selection cancelled.")
            return

        try:
            self.df = pd.read_csv(file_path)
            self.modified_df = self.df.copy()  # Initialize modified_df
            self.full_input_file_path = file_path
            self.input_file_path_display.set(os.path.basename(file_path))
            self.update_status(
                f"Loaded: {os.path.basename(file_path)}. Rows: {len(self.df)}, Columns: {len(self.df.columns)}")

            column_names = list(self.df.columns)
            self.combo_condition_column['values'] = column_names
            self.combo_target_column['values'] = column_names
            if column_names:
                self.condition_column.set(column_names[0])
                self.target_column.set(column_names[0])
                self.update_condition_values_preview()  # Update preview for default selection
            else:  # Empty CSV or headerless
                self.combo_condition_column['values'] = []
                self.combo_target_column['values'] = []
                self.condition_column.set("")
                self.target_column.set("")
                self.condition_values_listbox.delete(0, tk.END)

            messagebox.showinfo("CSV Loaded",
                                f"Successfully loaded '{os.path.basename(file_path)}'.\nPlease select columns and enter values for editing.")
        except Exception as e:
            self.df = None
            self.modified_df = None
            self.full_input_file_path = None
            self.input_file_path_display.set("Failed to load file.")
            self.combo_condition_column['values'] = []
            self.combo_target_column['values'] = []
            self.condition_column.set("")
            self.target_column.set("")
            self.condition_values_listbox.delete(0, tk.END)
            messagebox.showerror("Error", f"Failed to read CSV file: {e}")
            self.update_status(f"Error loading CSV: {e}")

    def apply_changes(self):
        if self.df is None:
            messagebox.showwarning("No CSV Loaded", "Please load a CSV file first.")
            self.update_status("Apply failed: No CSV loaded.")
            return

        cond_col = self.condition_column.get()
        cond_val_str = self.condition_value.get()
        target_col = self.target_column.get()
        new_val_str = self.new_value.get()

        if not all([cond_col, target_col]):  # cond_val_str can be empty, new_val_str can be empty
            messagebox.showwarning("Missing Information", "Please select both a Filter Column and a Target Column.")
            self.update_status("Apply failed: Missing column selections.")
            return

        # Make a fresh copy from the original for each "Apply"
        self.modified_df = self.df.copy()
        original_target_col_dtype = self.modified_df[target_col].dtype  # Store original dtype

        # --- Condition Value Typing ---
        condition_value_typed = cond_val_str
        if cond_col and cond_val_str:  # Only attempt conversion if value is not empty
            try:
                col_dtype = self.modified_df[cond_col].dtype
                # Handle numeric types (int, float)
                if pd.api.types.is_numeric_dtype(col_dtype) and not pd.api.types.is_bool_dtype(col_dtype):
                    try:
                        # Try to convert to the specific type of the column (e.g. int64, float64)
                        condition_value_typed = pd.Series([cond_val_str]).astype(col_dtype).iloc[0]
                    except ValueError:
                        self.update_status(
                            f"Warning: Condition value '{cond_val_str}' not valid for numeric column '{cond_col}'. Using string match.")
                        condition_value_typed = cond_val_str  # Fallback
                # Handle boolean types
                elif pd.api.types.is_bool_dtype(col_dtype):
                    if cond_val_str.lower() in ['true', '1', 't']:
                        condition_value_typed = True
                    elif cond_val_str.lower() in ['false', '0', 'f']:
                        condition_value_typed = False
                    else:
                        self.update_status(
                            f"Warning: Condition value '{cond_val_str}' not boolean for '{cond_col}'. Using string match.")
                        condition_value_typed = cond_val_str  # Fallback
                # For object/string, no conversion needed usually, direct string is fine
            except Exception as e:
                self.update_status(f"Note: Type conversion for condition value failed: {e}. Using string match.")
                condition_value_typed = cond_val_str

        # --- New Value Typing ---
        new_value_typed = new_val_str  # Default to string
        if target_col:
            try:
                target_col_series = self.modified_df[target_col]
                if new_val_str == "":  # Handling empty string input for new value
                    if pd.api.types.is_string_dtype(target_col_series.dtype) or pd.api.types.is_object_dtype(
                            target_col_series.dtype):
                        new_value_typed = ""  # Keep as empty string for string/object columns
                    else:
                        new_value_typed = pd.NA  # Use pandas NA for missing value in numeric/bool/datetime etc.
                else:
                    # Attempt to convert to original column type if possible
                    try:
                        new_value_typed = pd.Series([new_val_str]).astype(original_target_col_dtype).iloc[0]
                    except (ValueError, TypeError):
                        # If direct cast fails, try more general numeric/bool, then fallback to string
                        if pd.api.types.is_integer_dtype(original_target_col_dtype):
                            try:
                                new_value_typed = int(float(new_val_str))  # float first for "60.0"
                            except ValueError:
                                self.update_status(
                                    f"Warning: New value '{new_val_str}' for int column '{target_col}' is invalid. Using string.")
                        elif pd.api.types.is_float_dtype(original_target_col_dtype):
                            try:
                                new_value_typed = float(new_val_str)
                            except ValueError:
                                self.update_status(
                                    f"Warning: New value '{new_val_str}' for float column '{target_col}' is invalid. Using string.")
                        elif pd.api.types.is_bool_dtype(original_target_col_dtype):
                            if new_val_str.lower() in ['true', '1', 't']:
                                new_value_typed = True
                            elif new_val_str.lower() in ['false', '0', 'f']:
                                new_value_typed = False
                            else:
                                self.update_status(
                                    f"Warning: New value '{new_val_str}' for bool column '{target_col}' is invalid. Using string.")
                        # else, it remains new_val_str (string)
            except Exception as e:
                self.update_status(f"Error determining type for new value: {e}. Using input string '{new_val_str}'.")

        try:
            # Create mask for rows that match the condition
            mask = pd.Series([False] * len(self.modified_df))  # Default to no matches
            if cond_col:  # Only apply mask if a condition column is selected
                # Try direct comparison first
                try:
                    mask = (self.modified_df[cond_col] == condition_value_typed)
                    # For NA values in condition column, `==` behaves differently.
                    # If condition_value_typed is also NA-like, handle that.
                    if pd.isna(condition_value_typed):  # If user wants to match NA values
                        mask = self.modified_df[cond_col].isna()

                except TypeError:  # If direct comparison fails due to mixed types
                    self.update_status("Warning: Type mismatch in condition filter. Comparing as strings.")
                    mask = (self.modified_df[cond_col].astype(str) == str(condition_value_typed))
            else:  # If no condition column, implies change all rows (or we should prevent this)
                # For this app, a condition is implied. If cond_col is empty, we do nothing.
                # The check `if not all([cond_col, target_col]):` handles this.
                pass

            num_rows_matched = mask.sum()

            if num_rows_matched > 0:
                self.modified_df.loc[mask, target_col] = new_value_typed
                msg = f"Applied: {num_rows_matched} row(s) in '{target_col}' set to '{new_val_str}' where '{cond_col}' was '{cond_val_str}'."
                messagebox.showinfo("Changes Applied (Preview)", msg + "\n\nClick 'Save Modified CSV As...' to save.")
                self.update_status(msg)
            else:
                msg = f"No rows found where '{cond_col}' is '{cond_val_str}'. No changes applied to preview."
                messagebox.showinfo("No Matches", msg)
                self.update_status(msg)
        except Exception as e:
            messagebox.showerror("Error Applying Changes",
                                 f"An error occurred: {e}\n\nModifications have been reverted in preview.")
            self.update_status(f"Error applying changes: {e}")
            self.modified_df = self.df.copy()  # Revert to original on error

    def save_csv(self):
        if self.modified_df is None:
            messagebox.showwarning("No Data to Save",
                                   "Please load and apply changes to a CSV file first, or load a file if no changes are needed for saving.")
            self.update_status("Save failed: No data.")
            return
        if self.df is not None and self.modified_df.equals(self.df) and self.full_input_file_path is not None:
            if not messagebox.askyesno("No Changes Detected",
                                       "No changes have been applied to the data since loading. Do you still want to save it (possibly to a new location)?"):
                self.update_status("Save cancelled: No changes.")
                return

        output_file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            title="Save Modified CSV As",
            initialfile=f"modified_{os.path.basename(self.full_input_file_path)}" if self.full_input_file_path else "modified_output.csv"
        )

        if not output_file_path:
            self.update_status("Save cancelled by user.")
            return

        try:
            self.modified_df.to_csv(output_file_path, index=False)
            messagebox.showinfo("Save Successful", f"Modified CSV saved to:\n{output_file_path}")
            self.update_status(f"Saved to: {output_file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save CSV file: {e}")
            self.update_status(f"Error saving CSV: {e}")

    def update_status(self, message):
        self.status_bar.config(text=f"Status: {message}")


def main():
    root = tk.Tk()
    app = CSVEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()