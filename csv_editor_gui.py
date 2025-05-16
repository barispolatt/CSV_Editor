import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import pandas as pd

# Varsayılan görünüm modu ve renk teması
ctk.set_appearance_mode("System")  # "Light", "Dark", "System"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class CSVEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gelişmiş CSV Düzenleyici")
        self.geometry("900x700") # Pencere boyutunu biraz büyüttük

        self.data_frame = None
        self.filtered_data_frame = None # Filtrelenmiş veriyi tutmak için

        # Ana Çerçeve
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # --- Dosya İşlemleri Çerçevesi ---
        file_ops_frame = ctk.CTkFrame(main_frame)
        file_ops_frame.pack(pady=10, padx=10, fill="x")

        self.load_button = ctk.CTkButton(file_ops_frame, text="CSV Yükle", command=self.load_csv)
        self.load_button.pack(side="left", padx=5)

        self.loaded_file_label = ctk.CTkLabel(file_ops_frame, text="Yüklü dosya: Yok")
        self.loaded_file_label.pack(side="left", padx=5)

        # --- Veri Önizleme Çerçevesi ---
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.preview_label = ctk.CTkLabel(preview_frame, text="Veri Önizleme (İlk 5 Satır):")
        self.preview_label.pack(pady=(0,5))

        # Treeview için stil
        style = ttk.Style()
        # Temaları dene: 'clam', 'alt', 'default', 'classic'
        # Hangi tema daha iyi görünüyorsa veya CTk ile uyumluysa seçilebilir
        try:
            style.theme_use("clam") # Veya 'default' gibi başka bir tema
        except:
            print("Clam teması bulunamadı, varsayılan tema kullanılıyor.")

        # Treeview renklerini CustomTkinter temasına uydurmaya çalışalım
        # Bu kısım işletim sistemi ve temaya göre değişiklik gösterebilir
        bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        header_bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        borderwidth=0)
        style.map('Treeview', background=[('selected', header_bg_color[0])], foreground=[('selected', text_color)]) # header_bg_color[0] koyu modda sorun çıkarabilir, tek renk denenebilir
        style.configure("Treeview.Heading",
                        background=header_bg_color[0] if isinstance(header_bg_color, tuple) else header_bg_color,
                        foreground=text_color, # Başlık metin rengi
                        relief="flat",
                        padding=(5,5))
        style.map("Treeview.Heading",
                  background=[('active', header_bg_color[1] if isinstance(header_bg_color, tuple) else header_bg_color)])


        self.tree_frame = ctk.CTkFrame(preview_frame) # Scrollbar'ları eklemek için ekstra frame
        self.tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.tree_frame, show="headings", style="Treeview")
        self.tree_vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree_hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.tree_vsb.set, xscrollcommand=self.tree_hsb.set)

        self.tree_vsb.pack(side="right", fill="y")
        self.tree_hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)


        # --- Filtreleme Çerçevesi ---
        filter_frame = ctk.CTkFrame(main_frame)
        filter_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(filter_frame, text="Filtrele:").pack(side="left", padx=(0,5))
        self.filter_column_combo = ctk.CTkComboBox(filter_frame, values=[], state="disabled")
        self.filter_column_combo.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Değer:").pack(side="left", padx=5)
        self.filter_value_entry = ctk.CTkEntry(filter_frame, placeholder_text="Filtre değeri", state="disabled")
        self.filter_value_entry.pack(side="left", padx=5, expand=True, fill="x")

        self.apply_filter_button = ctk.CTkButton(filter_frame, text="Filtreyi Uygula/Kaldır", command=self.toggle_filter, state="disabled")
        self.apply_filter_button.pack(side="left", padx=5)


        # --- Değer Değiştirme Çerçevesi ---
        modify_frame = ctk.CTkFrame(main_frame)
        modify_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(modify_frame, text="Değeri Değiştir:").pack(side="left", padx=(0,5))
        self.modify_column_combo = ctk.CTkComboBox(modify_frame, values=[], state="disabled")
        self.modify_column_combo.pack(side="left", padx=5)

        ctk.CTkLabel(modify_frame, text="Yeni Değer:").pack(side="left", padx=5)
        self.new_value_entry = ctk.CTkEntry(modify_frame, placeholder_text="Yeni değer", state="disabled")
        self.new_value_entry.pack(side="left", padx=5, expand=True, fill="x")

        self.apply_modify_button = ctk.CTkButton(modify_frame, text="Değişikliği Uygula", command=self.apply_modification, state="disabled")
        self.apply_modify_button.pack(side="left", padx=5)

        # --- Kaydetme Çerçevesi ---
        save_frame = ctk.CTkFrame(main_frame)
        save_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(save_frame, text="Satır Sonlandırma:").pack(side="left", padx=(0,5))
        self.line_ending_combo = ctk.CTkComboBox(save_frame, values=["LF (\\n)", "CRLF (\\r\\n)"], state="disabled")
        self.line_ending_combo.set("LF (\\n)") # Varsayılan
        self.line_ending_combo.pack(side="left", padx=5)

        self.save_button = ctk.CTkButton(save_frame, text="Değiştirilmiş CSV'yi Kaydet", command=self.save_csv, state="disabled")
        self.save_button.pack(side="left", padx=5)

        # Durum Çubuğu
        self.status_label = ctk.CTkLabel(main_frame, text="Durum: Başlamaya hazır.")
        self.status_label.pack(pady=10)


    def update_treeview(self, df_to_show):
        # Treeview'i temizle
        for i in self.tree.get_children():
            self.tree.delete(i)

        if df_to_show is None or df_to_show.empty:
            self.tree["columns"] = []
            return

        # Kolonları ayarla
        self.tree["columns"] = list(df_to_show.columns)
        for col in df_to_show.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", width=100) # Genişliği ayarlayabilirsiniz

        # Veri satırlarını ekle (ilk N satırı veya tümünü)
        # Performans için çok büyük dosyalarda sadece ilk N satırı göstermek daha iyi olabilir
        # Şimdilik ilk 50 satırı gösterelim
        for index, row in df_to_show.head(50).iterrows():
            self.tree.insert("", "end", values=list(row))


    def load_csv(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV dosyaları", "*.csv"), ("Tüm dosyalar", "*.*")]
        )
        if not file_path:
            return

        try:
            # Olası encoding hatalarını yakalamak için farklı encoding'ler denenebilir
            # Veya kullanıcıya encoding seçme opsiyonu sunulabilir.
            # Şimdilik utf-8 ve latin1 deneyelim.
            try:
                self.data_frame = pd.read_csv(file_path)
            except UnicodeDecodeError:
                try:
                    self.data_frame = pd.read_csv(file_path, encoding='latin1')
                except Exception as e_latin1:
                    messagebox.showerror("Okuma Hatası", f"Dosya okunamadı (latin1 denendi): {e_latin1}")
                    return
            except Exception as e_utf8:
                 messagebox.showerror("Okuma Hatası", f"Dosya okunamadı (utf-8 denendi): {e_utf8}")
                 return


            self.filtered_data_frame = self.data_frame.copy() # Başlangıçta filtrelenmemiş veri
            self.update_treeview(self.filtered_data_frame) # Filtrelenmiş veriyi göster
            self.loaded_file_label.configure(text=f"Yüklü dosya: ...{file_path[-30:]}") # Dosya adının son kısmını göster
            self.status_label.configure(text=f"{len(self.data_frame)} satır yüklendi.")

            columns = list(self.data_frame.columns)
            self.filter_column_combo.configure(values=columns, state="normal")
            self.modify_column_combo.configure(values=columns, state="normal")
            if columns:
                self.filter_column_combo.set(columns[0])
                self.modify_column_combo.set(columns[0])

            self.filter_value_entry.configure(state="normal")
            self.apply_filter_button.configure(state="normal")
            self.new_value_entry.configure(state="normal")
            self.apply_modify_button.configure(state="normal")
            self.line_ending_combo.configure(state="normal")
            self.save_button.configure(state="normal")

        except Exception as e:
            messagebox.showerror("CSV Yükleme Hatası", f"Dosya yüklenirken bir hata oluştu: {e}")
            self.data_frame = None
            self.filtered_data_frame = None
            self.update_treeview(None)
            self.loaded_file_label.configure(text="Yüklü dosya: Yok")
            self.disable_controls()

    def disable_controls(self):
        self.filter_column_combo.configure(state="disabled", values=[])
        self.filter_value_entry.configure(state="disabled")
        self.apply_filter_button.configure(state="disabled")
        self.modify_column_combo.configure(state="disabled", values=[])
        self.new_value_entry.configure(state="disabled")
        self.apply_modify_button.configure(state="disabled")
        self.line_ending_combo.configure(state="disabled")
        self.save_button.configure(state="disabled")

    def toggle_filter(self):
        if self.data_frame is None:
            messagebox.showwarning("Uyarı", "Önce bir CSV dosyası yükleyin.")
            return

        filter_col = self.filter_column_combo.get()
        filter_val_str = self.filter_value_entry.get()

        # Eğer filtre zaten uygulanmışsa ve kullanıcı tekrar basıyorsa, filtreyi kaldır
        if self.filtered_data_frame is not self.data_frame and not filter_val_str: # filtre değeri boşsa ve filtrelenmişse kaldır
             self.filtered_data_frame = self.data_frame.copy()
             self.update_treeview(self.filtered_data_frame)
             self.status_label.configure(text=f"Filtre kaldırıldı. {len(self.filtered_data_frame)} satır gösteriliyor.")
             self.apply_filter_button.configure(text="Filtreyi Uygula")
             return

        if not filter_col or not filter_val_str:
            # Eğer değer girilmemişse ve filtre yoksa, tüm veriyi göster (filtreyi kaldır)
            self.filtered_data_frame = self.data_frame.copy()
            self.update_treeview(self.filtered_data_frame)
            self.status_label.configure(text=f"Filtre kaldırıldı / Değer girilmedi. {len(self.filtered_data_frame)} satır gösteriliyor.")
            self.apply_filter_button.configure(text="Filtreyi Uygula")
            return

        try:
            # Veri tipini korumaya çalışarak filtrele
            original_dtype = self.data_frame[filter_col].dtype
            if pd.api.types.is_numeric_dtype(original_dtype):
                try:
                    filter_val = pd.to_numeric(filter_val_str)
                except ValueError:
                    messagebox.showerror("Filtre Hatası", f"'{filter_col}' sayısal bir kolon, lütfen geçerli bir sayı girin.")
                    return
            elif pd.api.types.is_datetime64_any_dtype(original_dtype):
                try:
                    filter_val = pd.to_datetime(filter_val_str)
                except ValueError:
                     messagebox.showerror("Filtre Hatası", f"'{filter_col}' tarih/saat kolonu, lütfen geçerli bir format girin (örn: YYYY-AA-GG).")
                     return
            else: # String veya diğer tipler
                filter_val = filter_val_str

            self.filtered_data_frame = self.data_frame[self.data_frame[filter_col] == filter_val].copy()
            self.update_treeview(self.filtered_data_frame)
            self.status_label.configure(text=f"Filtre uygulandı. {len(self.filtered_data_frame)} satır bulundu.")
            self.apply_filter_button.configure(text="Filtreyi Kaldır") # Buton metnini değiştir
        except Exception as e:
            messagebox.showerror("Filtreleme Hatası", f"Filtre uygulanırken hata: {e}")


    def apply_modification(self):
        if self.data_frame is None or self.filtered_data_frame is None: # data_frame yerine filtered_data_frame kontrolü
            messagebox.showwarning("Uyarı", "Önce bir CSV dosyası yükleyin ve gerekiyorsa filtreleyin.")
            return

        modify_col = self.modify_column_combo.get()
        new_val_str = self.new_value_entry.get()

        if not modify_col:
            messagebox.showwarning("Uyarı", "Değiştirilecek bir kolon seçin.")
            return

        try:
            # Yeni değeri, hedef kolonun veri tipine dönüştürmeye çalış
            target_dtype = self.data_frame[modify_col].dtype
            if pd.api.types.is_numeric_dtype(target_dtype):
                try:
                    new_val = pd.to_numeric(new_val_str)
                except ValueError:
                    if new_val_str == "": # Boş değer NaN (Not a Number) olarak atanabilir
                        new_val = pd.NA
                    else:
                        messagebox.showerror("Değer Hatası", f"'{modify_col}' sayısal bir kolon, lütfen geçerli bir sayı girin veya boş bırakın.")
                        return
            elif pd.api.types.is_datetime64_any_dtype(target_dtype):
                try:
                    new_val = pd.to_datetime(new_val_str)
                except ValueError:
                    if new_val_str == "":
                        new_val = pd.NaT # Not a Time
                    else:
                        messagebox.showerror("Değer Hatası", f"'{modify_col}' tarih/saat kolonu, lütfen geçerli bir format girin veya boş bırakın.")
                        return
            elif pd.api.types.is_boolean_dtype(target_dtype):
                if new_val_str.lower() in ['true', '1', 'evet', 'doğru']:
                    new_val = True
                elif new_val_str.lower() in ['false', '0', 'hayır', 'yanlış']:
                    new_val = False
                elif new_val_str == "" and target_dtype == 'boolean': # Pandas 'boolean' (nullable)
                    new_val = pd.NA
                else:
                    messagebox.showerror("Değer Hatası", f"'{modify_col}' boolean bir kolon, lütfen 'true'/'false' gibi bir değer girin.")
                    return
            else: # String veya object
                new_val = new_val_str


            # Değişikliği hem filtrelenmiş DataFrame'de (görsel geri bildirim için)
            # hem de ana DataFrame'de (kayıt için) yap.
            # ÖNEMLİ: Filtrelenmiş DataFrame'in indekslerini kullanarak ana DataFrame'i güncelle.
            indices_to_modify = self.filtered_data_frame.index
            self.data_frame.loc[indices_to_modify, modify_col] = new_val

            # Filtrelenmiş veriyi de güncelle (eğer ayrı bir kopya ise)
            self.filtered_data_frame.loc[indices_to_modify, modify_col] = new_val

            self.update_treeview(self.filtered_data_frame) # Güncellenmiş veriyi göster
            self.status_label.configure(text=f"'{modify_col}' kolonundaki {len(indices_to_modify)} satır '{new_val_str}' olarak güncellendi.")
            messagebox.showinfo("Başarılı", f"Değişiklikler uygulandı.")

        except Exception as e:
            messagebox.showerror("Değiştirme Hatası", f"Değer değiştirilirken hata: {e}")


    def save_csv(self):
        if self.data_frame is None:
            messagebox.showwarning("Uyarı", "Kaydedilecek veri yok. Önce bir CSV yükleyin.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV dosyaları", "*.csv"), ("Tüm dosyalar", "*.*")],
            initialfile="guncellenmis_veri.csv"
        )
        if not file_path:
            return

        line_ending_choice = self.line_ending_combo.get()
        terminator = '\n' if line_ending_choice == "LF (\\n)" else '\r\n'

        try:
            self.data_frame.to_csv(file_path, index=False, line_terminator=terminator, encoding='utf-8-sig') # utf-8-sig Excel uyumluluğu için
            self.status_label.configure(text=f"Dosya '{file_path}' olarak kaydedildi.")
            messagebox.showinfo("Başarılı", f"Dosya başarıyla kaydedildi:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Kaydetme Hatası", f"Dosya kaydedilirken bir hata oluştu: {e}")

if __name__ == "__main__":
    app = CSVEditorApp()
    app.mainloop()