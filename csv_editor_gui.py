import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import pandas as pd

# Varsayılan görünüm modu ve renk teması
ctk.set_appearance_mode("System")  # "Light", "Dark", "System"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"


class CSVEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gelişmiş Kümülatif CSV Düzenleyici v2")  # Versiyon ekleyebiliriz
        self.geometry("950x750")  # Pencere boyutunu biraz daha ayarlayabiliriz

        self.original_df = None  # Yüklenen orijinal DataFrame
        self.view_df = None  # Filtrelenmiş, görüntülenen DataFrame

        # Ana Çerçeve
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=15, padx=15, fill="both", expand=True)

        # --- Dosya İşlemleri Çerçevesi ---
        file_ops_frame = ctk.CTkFrame(main_frame)
        file_ops_frame.pack(pady=(10, 5), padx=10, fill="x")

        self.load_button = ctk.CTkButton(file_ops_frame, text="CSV Yükle", command=self.load_csv)
        self.load_button.pack(side="left", padx=5, pady=5)

        self.loaded_file_label = ctk.CTkLabel(file_ops_frame, text="Yüklü dosya: Yok", anchor="w")
        self.loaded_file_label.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # --- Veri Önizleme Çerçevesi ---
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(pady=5, padx=10, fill="both", expand=True)

        self.preview_label = ctk.CTkLabel(preview_frame, text="Veri Önizleme:", anchor="w")
        self.preview_label.pack(pady=(0, 5), fill="x")

        # Treeview için stil ve renk ayarları
        style = ttk.Style()
        try:
            style.theme_use("clam")  # Daha modern bir görünüm için 'clam', 'alt', 'default' denenebilir
        except Exception:
            print("Clam teması bulunamadı, varsayılan ttk teması kullanılıyor.")

        # CustomTkinter tema renklerini al
        bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        # Header rengi için fg_color tuple dönebilir (normal, hover), ilkini alalım
        header_bg_tuple = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        header_bg_color = header_bg_tuple[0] if isinstance(header_bg_tuple, (list, tuple)) else header_bg_tuple
        header_active_bg_color = header_bg_tuple[1] if isinstance(header_bg_tuple, (list, tuple)) and len(
            header_bg_tuple) > 1 else header_bg_color

        style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, borderwidth=0,
                        rowheight=25)
        style.map('Treeview', background=[('selected', header_bg_color)],
                  foreground=[('selected', text_color)])  # Seçili satır
        style.configure("Treeview.Heading", background=header_bg_color, foreground=text_color, relief="flat",
                        padding=(5, 5), font=('TkDefaultFont', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', header_active_bg_color)])

        self.tree_frame = ctk.CTkFrame(preview_frame)
        self.tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.tree_frame, show="headings", style="Treeview")
        self.tree_vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)  # ttk.Scrollbar
        self.tree_hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)  # ttk.Scrollbar
        self.tree.configure(yscrollcommand=self.tree_vsb.set, xscrollcommand=self.tree_hsb.set)

        self.tree_vsb.pack(side="right", fill="y")
        self.tree_hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # --- Kontrol Paneli Çerçevesi (Filtre, Değiştir, Kaydet bir arada daha düzenli) ---
        controls_outer_frame = ctk.CTkFrame(main_frame)
        controls_outer_frame.pack(pady=5, padx=10, fill="x")

        # --- Filtreleme Paneli ---
        filter_panel = ctk.CTkFrame(controls_outer_frame)
        filter_panel.pack(side="left", padx=(0, 5), pady=5, fill="y", expand=True)

        ctk.CTkLabel(filter_panel, text="Filtreleme", font=ctk.CTkFont(weight="bold")).pack(pady=(5, 5), anchor="w",
                                                                                            padx=5)

        filter_options_frame = ctk.CTkFrame(filter_panel, fg_color="transparent")
        filter_options_frame.pack(fill="x", padx=5)
        ctk.CTkLabel(filter_options_frame, text="Kolon:").pack(side="left", padx=(0, 2))
        self.filter_column_combo = ctk.CTkComboBox(filter_options_frame, values=[], state="disabled", width=130)
        self.filter_column_combo.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(filter_options_frame, text="Değer:").pack(side="left", padx=(0, 2))
        self.filter_value_entry = ctk.CTkEntry(filter_options_frame, placeholder_text="Değer veya [DOLU]/[BOŞ]",
                                               state="disabled")
        self.filter_value_entry.pack(side="left", padx=(0, 5), expand=True, fill="x")

        filter_buttons_frame = ctk.CTkFrame(filter_panel, fg_color="transparent")
        filter_buttons_frame.pack(fill="x", pady=(5, 5), padx=5)
        self.apply_filter_button = ctk.CTkButton(filter_buttons_frame, text="Filtreyi Uygula/Daralt",
                                                 command=self.apply_cumulative_filter, state="disabled")
        self.apply_filter_button.pack(side="left", padx=(0, 5))
        self.reset_filters_button = ctk.CTkButton(filter_buttons_frame, text="Tüm Filtreleri Sıfırla",
                                                  command=self.reset_all_filters, state="disabled")
        self.reset_filters_button.pack(side="left")

        # --- Değer Değiştirme Paneli ---
        modify_panel = ctk.CTkFrame(controls_outer_frame)
        modify_panel.pack(side="left", padx=5, pady=5, fill="y", expand=True)

        ctk.CTkLabel(modify_panel, text="Değer Değiştirme", font=ctk.CTkFont(weight="bold")).pack(pady=(5, 5),
                                                                                                  anchor="w", padx=5)

        modify_options_frame = ctk.CTkFrame(modify_panel, fg_color="transparent")
        modify_options_frame.pack(fill="x", padx=5)
        ctk.CTkLabel(modify_options_frame, text="Kolon:").pack(side="left", padx=(0, 2))
        self.modify_column_combo = ctk.CTkComboBox(modify_options_frame, values=[], state="disabled", width=130)
        self.modify_column_combo.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(modify_options_frame, text="Yeni Değer:").pack(side="left", padx=(0, 2))
        self.new_value_entry = ctk.CTkEntry(modify_options_frame, placeholder_text="Yeni değer", state="disabled")
        self.new_value_entry.pack(side="left", padx=(0, 5), expand=True, fill="x")

        modify_buttons_frame = ctk.CTkFrame(modify_panel, fg_color="transparent")
        modify_buttons_frame.pack(fill="x", pady=(5, 5), padx=5, anchor="s")  # anchor s
        self.apply_modify_button = ctk.CTkButton(modify_buttons_frame, text="Değişikliği Uygula",
                                                 command=self.apply_modification, state="disabled")
        self.apply_modify_button.pack(side="left")

        # --- Kaydetme Paneli ---
        save_panel = ctk.CTkFrame(controls_outer_frame)
        save_panel.pack(side="left", padx=(5, 0), pady=5, fill="y", expand=True)

        ctk.CTkLabel(save_panel, text="Kaydetme", font=ctk.CTkFont(weight="bold")).pack(pady=(5, 5), anchor="w", padx=5)

        save_options_frame = ctk.CTkFrame(save_panel, fg_color="transparent")
        save_options_frame.pack(fill="x", padx=5)
        ctk.CTkLabel(save_options_frame, text="Satır Sonu:").pack(side="left", padx=(0, 2))
        self.line_ending_combo = ctk.CTkComboBox(save_options_frame, values=["LF (\\n)", "CRLF (\\r\\n)"],
                                                 state="disabled", width=120)
        self.line_ending_combo.set("LF (\\n)")
        self.line_ending_combo.pack(side="left", padx=(0, 5))

        save_buttons_frame = ctk.CTkFrame(save_panel, fg_color="transparent")
        save_buttons_frame.pack(fill="x", pady=(5, 5), padx=5, anchor="s")  # anchor s
        self.save_button = ctk.CTkButton(save_buttons_frame, text="CSV'yi Kaydet", command=self.save_csv,
                                         state="disabled")
        self.save_button.pack(side="left")

        # Durum Çubuğu
        self.status_label = ctk.CTkLabel(main_frame, text="Durum: Başlamaya hazır.", anchor="w")
        self.status_label.pack(pady=(5, 10), padx=10, fill="x")

    def update_treeview(self, df_to_show):
        for i in self.tree.get_children():
            self.tree.delete(i)

        if df_to_show is None or df_to_show.empty:
            self.tree["columns"] = []
            self.preview_label.configure(text="Veri Önizleme: (Veri Yok veya Filtre Sonucu Boş)")
            return

        self.tree["columns"] = list(df_to_show.columns)
        for col in df_to_show.columns:
            self.tree.heading(col, text=col, anchor="w")
            # Kolon genişliğini içeriğe ve başlığa göre biraz daha iyi ayarlama
            # Örnek bir içerik alıp genişliği ona göre de set edebiliriz ama şimdilik başlık yeterli.
            col_width = max(100, len(col) * 9,
                            df_to_show[col].astype(str).str.len().max() * 7 if len(df_to_show) > 0 else 0)
            self.tree.column(col, anchor="w", width=min(col_width, 300), minwidth=60)  # Maksimum genişlik de ekleyelim

        limit_rows = 100
        df_display = df_to_show.head(limit_rows)
        for index, row in df_display.iterrows():
            self.tree.insert("", "end", values=list(row))

        total_filtered_rows = len(df_to_show)
        if total_filtered_rows > limit_rows:
            self.preview_label.configure(
                text=f"Veri Önizleme (İlk {limit_rows} satır / Toplam {total_filtered_rows} filtrelenmiş satır):")
        else:
            self.preview_label.configure(text=f"Veri Önizleme ({total_filtered_rows} filtrelenmiş satır):")

    def load_csv(self):
        file_path = filedialog.askopenfilename(defaultextension=".csv",
                                               filetypes=[("CSV dosyaları", "*.csv"), ("Tüm dosyalar", "*.*")])
        if not file_path: return

        try:
            try:
                self.original_df = pd.read_csv(file_path)
            except UnicodeDecodeError:
                try:
                    self.original_df = pd.read_csv(file_path, encoding='latin1')
                except UnicodeDecodeError:
                    self.original_df = pd.read_csv(file_path, encoding='iso-8859-9')  # Türkçe için
                except Exception as e_inner:
                    messagebox.showerror("Okuma Hatası",
                                         f"Dosya farklı encoding'lerle denendi ancak okunamadı: {e_inner}")
                    return

            self.view_df = self.original_df.copy()
            self.update_treeview(self.view_df)
            self.loaded_file_label.configure(text=f"Dosya: ...{file_path[-40:]}")
            self.status_label.configure(text=f"{len(self.original_df)} satır yüklendi. Filtre uygulanmadı.")

            columns = [""] + list(self.original_df.columns)  # Boş seçenek ekleyerek combobox'ı sıfırlama imkanı
            self.filter_column_combo.configure(values=columns, state="normal")
            self.modify_column_combo.configure(values=columns, state="normal")
            if len(columns) > 1:  # Eğer "" dışında kolon varsa ilkini seç
                self.filter_column_combo.set(columns[1])
                self.modify_column_combo.set(columns[1])
            else:  # Sadece "" varsa onu seç veya boş bırak
                self.filter_column_combo.set(columns[0] if columns else "")
                self.modify_column_combo.set(columns[0] if columns else "")

            self.enable_controls()
        except Exception as e:
            messagebox.showerror("CSV Yükleme Hatası", f"Dosya yüklenirken bir hata oluştu: {e}")
            self.original_df = None
            self.view_df = None
            self.update_treeview(None)
            self.disable_controls()  # Yükleme başarısız olursa kontrolleri devre dışı bırak

    def enable_controls(self):
        self.filter_value_entry.configure(state="normal")
        self.apply_filter_button.configure(state="normal")
        self.reset_filters_button.configure(state="normal")
        # modify_column_combo zaten load_csv içinde normal yapılıyor
        self.new_value_entry.configure(state="normal")
        self.apply_modify_button.configure(state="normal")
        self.line_ending_combo.configure(state="normal")
        self.save_button.configure(state="normal")

    def disable_controls(self):
        self.filter_column_combo.configure(state="disabled", values=[])
        self.filter_value_entry.configure(state="disabled", placeholder_text="Değer veya [DOLU]/[BOŞ]")
        self.apply_filter_button.configure(state="disabled")
        self.reset_filters_button.configure(state="disabled")
        self.modify_column_combo.configure(state="disabled", values=[])
        self.new_value_entry.configure(state="disabled", placeholder_text="Yeni değer")
        self.apply_modify_button.configure(state="disabled")
        self.line_ending_combo.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.loaded_file_label.configure(text="Yüklü dosya: Yok")
        self.preview_label.configure(text="Veri Önizleme:")
        self.status_label.configure(text="Durum: Başlamaya hazır.")

    def reset_all_filters(self):
        if self.original_df is not None:
            self.view_df = self.original_df.copy()
            self.update_treeview(self.view_df)
            self.status_label.configure(text=f"Tüm filtreler sıfırlandı. {len(self.view_df)} satır gösteriliyor.")

            columns = [""] + list(self.original_df.columns)
            if len(columns) > 1:
                self.filter_column_combo.set(columns[1])
            else:
                self.filter_column_combo.set(columns[0] if columns else "")
            self.filter_value_entry.delete(0, "end")
        else:
            messagebox.showwarning("Uyarı", "Sıfırlanacak filtre yok. Önce bir CSV dosyası yükleyin.")

    def apply_cumulative_filter(self):
        if self.view_df is None:
            messagebox.showwarning("Uyarı", "Önce bir CSV dosyası yükleyin.")
            return

        filter_col = self.filter_column_combo.get()
        filter_val_str = self.filter_value_entry.get().strip()

        if not filter_col or filter_col == "":  # Boş kolon seçilmişse
            messagebox.showwarning("Uyarı", "Lütfen filtrelemek için geçerli bir kolon seçin.")
            return

        if not filter_val_str:
            messagebox.showinfo("Bilgi",
                                "Filtre uygulamak için bir değer girin veya özel komut ([DOLU]/[BOŞ]) kullanın.")
            return

        temp_df = self.view_df
        try:
            if filter_val_str.upper() == "[DOLU]" or filter_val_str.upper() == "[NOT_EMPTY]":
                if pd.api.types.is_string_dtype(temp_df[filter_col]) or pd.api.types.is_object_dtype(
                        temp_df[filter_col]):
                    condition = temp_df[filter_col].notna() & \
                                (temp_df[filter_col].astype(str).str.strip() != "") & \
                                (temp_df[filter_col].astype(str).str.strip() != "[]")
                    self.view_df = temp_df[condition].copy()
                else:
                    self.view_df = temp_df[temp_df[filter_col].notna()].copy()

            elif filter_val_str.upper() == "[BOŞ]" or filter_val_str.upper() == "[EMPTY]":
                if pd.api.types.is_string_dtype(temp_df[filter_col]) or pd.api.types.is_object_dtype(
                        temp_df[filter_col]):
                    condition = temp_df[filter_col].isna() | \
                                (temp_df[filter_col].astype(str).str.strip() == "") | \
                                (temp_df[filter_col].astype(str).str.strip() == "[]")
                    self.view_df = temp_df[condition].copy()
                else:
                    self.view_df = temp_df[temp_df[filter_col].isna()].copy()

            else:  # Eşitlik filtresi
                original_dtype = self.original_df[filter_col].dtype
                filter_val_typed = None

                if pd.api.types.is_numeric_dtype(original_dtype):
                    try:
                        filter_val_typed = pd.to_numeric(filter_val_str)
                    except ValueError:
                        messagebox.showerror("Filtre Hatası",
                                             f"'{filter_col}' sayısal kolon, geçerli sayı girin: '{filter_val_str}'"); return
                elif pd.api.types.is_datetime64_any_dtype(original_dtype):
                    try:
                        filter_val_typed = pd.to_datetime(filter_val_str)
                    except ValueError:
                        messagebox.showerror("Filtre Hatası",
                                             f"'{filter_col}' tarih/saat kolon, geçerli format girin: '{filter_val_str}'"); return
                elif pd.api.types.is_boolean_dtype(original_dtype):  # Hem numpy bool hem de pandas BooleanDtype
                    if filter_val_str.lower() in ['true', '1', 'evet', 'doğru', 'dogru']:
                        filter_val_typed = True
                    elif filter_val_str.lower() in ['false', '0', 'hayır', 'yanlış', 'yanlis']:
                        filter_val_typed = False
                    else:
                        messagebox.showerror("Filtre Hatası",
                                             f"'{filter_col}' boolean kolon, 'true'/'false' benzeri bir değer girin: '{filter_val_str}'"); return
                else:
                    filter_val_typed = filter_val_str

                column_as_str_for_comparison = temp_df[filter_col].fillna('').astype(str)
                self.view_df = temp_df[column_as_str_for_comparison == str(filter_val_typed)].copy()

            self.update_treeview(self.view_df)
            self.status_label.configure(
                text=f"Filtre '{filter_col}' üzerine uygulandı. {len(self.view_df)} satır bulundu.")
        except Exception as e:
            messagebox.showerror("Filtreleme Hatası", f"Filtre uygulanırken hata: {e}\n\nDetay: {type(e).__name__}")
            self.status_label.configure(text=f"Filtreleme hatası oluştu. {len(self.view_df)} satır gösteriliyor.")

    def apply_modification(self):
        if self.original_df is None or self.view_df is None:
            messagebox.showwarning("Uyarı", "Önce CSV yükleyin ve gerekiyorsa filtreleyin.")
            return

        modify_col = self.modify_column_combo.get()
        new_val_str = self.new_value_entry.get()  # Kullanıcı boş bırakırsa boş string olarak gider

        if not modify_col or modify_col == "":  # Boş kolon seçilmişse
            messagebox.showwarning("Uyarı", "Değiştirilecek geçerli bir kolon seçin.")
            return

        if self.view_df.empty:
            messagebox.showinfo("Bilgi", "Değişiklik uygulanacak filtrelenmiş satır bulunmuyor.")
            return

        try:
            target_dtype = self.original_df[modify_col].dtype
            new_val = None

            # Kullanıcı boş string girdiyse ve kolonun tipi bunu NA/NaN/NaT olarak kabul edebiliyorsa, öyle ata.
            # Yoksa boş string olarak ata.
            if new_val_str == "":
                if pd.api.types.is_numeric_dtype(target_dtype):
                    new_val = pd.NA
                elif pd.api.types.is_datetime64_any_dtype(target_dtype):
                    new_val = pd.NaT
                elif str(target_dtype) == 'boolean':
                    new_val = pd.NA  # Pandas nullable boolean
                elif str(target_dtype) == 'bool':  # Numpy bool için boş atama genellikle istenmez, True/False olmalı
                    messagebox.showerror("Değer Hatası",
                                         f"'{modify_col}' standart boolean (True/False) kolonudur, boş atanamaz. 'true' veya 'false' girin.");
                    return
                else:
                    new_val = ""  # String veya object kolonlar için boş string
            else:  # Kullanıcı boş olmayan bir değer girdiyse tip dönüşümü yap
                if pd.api.types.is_numeric_dtype(target_dtype):
                    try:
                        new_val = pd.to_numeric(new_val_str)
                    except ValueError:
                        messagebox.showerror("Değer Hatası",
                                             f"'{modify_col}' sayısal kolon, geçerli sayı girin: '{new_val_str}'."); return
                elif pd.api.types.is_datetime64_any_dtype(target_dtype):
                    try:
                        new_val = pd.to_datetime(new_val_str)
                    except ValueError:
                        messagebox.showerror("Değer Hatası",
                                             f"'{modify_col}' tarih/saat kolon, geçerli format girin: '{new_val_str}'."); return
                elif pd.api.types.is_boolean_dtype(target_dtype):
                    if new_val_str.lower() in ['true', '1', 'evet', 'doğru', 'dogru']:
                        new_val = True
                    elif new_val_str.lower() in ['false', '0', 'hayır', 'yanlış', 'yanlis']:
                        new_val = False
                    else:
                        messagebox.showerror("Değer Hatası",
                                             f"'{modify_col}' boolean kolon, 'true'/'false' benzeri bir değer girin: '{new_val_str}'."); return
                else:
                    new_val = new_val_str

            indices_to_modify = self.view_df.index

            self.original_df.loc[indices_to_modify, modify_col] = new_val
            self.view_df.loc[indices_to_modify, modify_col] = new_val  # view_df'i de anında güncelle

            self.update_treeview(self.view_df)
            self.status_label.configure(
                text=f"'{modify_col}' kolonundaki {len(indices_to_modify)} filtrelenmiş satır güncellendi.")
            messagebox.showinfo("Başarılı", f"Değişiklikler '{modify_col}' kolonuna uygulandı.")
        except Exception as e:
            messagebox.showerror("Değiştirme Hatası", f"Değer değiştirilirken hata: {e}\n\nDetay: {type(e).__name__}")

    def save_csv(self):
        if self.original_df is None:
            messagebox.showwarning("Uyarı", "Kaydedilecek veri yok. Önce bir CSV yükleyin.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV dosyaları", "*.csv"), ("Tüm dosyalar", "*.*")],
                                                 initialfile="guncellenmis_veri.csv")
        if not file_path: return

        line_ending_choice = self.line_ending_combo.get()
        terminator = '\n' if line_ending_choice == "LF (\\n)" else '\r\n'

        try:
            self.original_df.to_csv(file_path, index=False, line_terminator=terminator, encoding='utf-8-sig')
            self.status_label.configure(text=f"Dosya '{file_path}' olarak kaydedildi.")
            messagebox.showinfo("Başarılı", f"Dosya başarıyla kaydedildi:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Kaydetme Hatası", f"Dosya kaydedilirken bir hata oluştu: {e}")


if __name__ == "__main__":
    app = CSVEditorApp()
    app.mainloop()