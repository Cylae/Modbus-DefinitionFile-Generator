import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from parser import parse_modbus_text, generate_csv_data
import sys

class ModbusDefGeneratorApp(tk.Tk):
    # --- GUI Class is unchanged ---
    def __init__(self):
        super().__init__()
        self.title("Générateur de Définition Modbus")
        self.geometry("900x700")
        self.filepath = None
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        header_frame = ttk.LabelFrame(main_frame, text="Informations d'en-tête", padding="10")
        header_frame.pack(fill=tk.X, expand=False, pady=5)
        header_frame.columnconfigure(1, weight=1)
        self.header_vars = {}
        header_fields = {
            "Protocole:": ("protocol", "modbusRTU"),
            "Catégorie:": ("category", "Inverter"),
            "Fabricant:": ("manufacturer", "HUAWEI"),
            "Modèle:": ("model", "SUN2000-10K-LC0"),
            "Code d’écriture forcé:": ("write_code", "0"),
        }
        row = 0
        for text, (key, value) in header_fields.items():
            label = ttk.Label(header_frame, text=text)
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value=value)
            self.header_vars[key] = var
            entry = ttk.Entry(header_frame, textvariable=var)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            row += 1
        file_frame = ttk.LabelFrame(main_frame, text="Fichier PDF d'entrée", padding="10")
        file_frame.pack(fill=tk.X, expand=False, pady=10)
        file_frame.columnconfigure(1, weight=1)
        self.load_button = ttk.Button(file_frame, text="Charger un Fichier PDF", command=self.load_pdf)
        self.load_button.grid(row=0, column=0, padx=5, pady=5)
        self.filepath_label_var = tk.StringVar(value="Aucun fichier sélectionné.")
        self.filepath_label = ttk.Label(file_frame, textvariable=self.filepath_label_var, font=("TkDefaultFont", 10, "italic"))
        self.filepath_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        self.generate_button = ttk.Button(
            main_frame,
            text="Générer et Enregistrer le Fichier CSV",
            command=self.process_and_generate_csv
        )
        self.generate_button.pack(fill=tk.X, pady=10, ipady=5)

    def load_pdf(self):
        self.filepath = filedialog.askopenfilename(filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")])
        self.filepath_label_var.set(self.filepath if self.filepath else "Aucun fichier sélectionné.")

    def process_and_generate_csv(self):
        header_info = {key: var.get() for key, var in self.header_vars.items()}
        if not self.filepath:
            messagebox.showerror("Erreur", "Veuillez d'abord charger un fichier PDF.")
            return
        parsed_registers = parse_modbus_text(self.filepath)
        if not parsed_registers:
            messagebox.showwarning("Avertissement", "Aucun registre n'a pu être analysé à partir du texte fourni.")
            return
        csv_content = generate_csv_data(parsed_registers, header_info)
        model_name = header_info.get('model', 'definition')
        filename = f"webdyn_def_{model_name}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            initialfile=filename,
            title="Enregistrer le fichier de définition Modbus"
        )
        if not filepath:
            return
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)
            messagebox.showinfo("Succès", f"Fichier enregistré avec succès à l'emplacement :\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erreur d'écriture", f"Une erreur est survenue lors de l'écriture du fichier :\n{e}")

if __name__ == "__main__":
    app = ModbusDefGeneratorApp()
    app.mainloop()
