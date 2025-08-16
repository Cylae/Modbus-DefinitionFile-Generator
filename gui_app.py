import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from parser import parse_modbus_text, generate_csv_data

class ModbusDefGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Générateur de Définition Modbus")
        self.geometry("900x700")

        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Header Information ---
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

        # --- Modbus Data Input ---
        data_frame = ttk.LabelFrame(main_frame, text="Table Modbus (coller le texte ici)", padding="10")
        data_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.modbus_text = scrolledtext.ScrolledText(data_frame, wrap=tk.WORD, height=20, font=("Courier New", 10))
        self.modbus_text.pack(fill=tk.BOTH, expand=True)

        # --- Action Button ---
        self.generate_button = ttk.Button(
            main_frame,
            text="Générer et Enregistrer le Fichier CSV",
            command=self.process_and_generate_csv
        )
        self.generate_button.pack(fill=tk.X, pady=10, ipady=5)

    def process_and_generate_csv(self):
        """The callback function for the generate button."""
        header_info = {key: var.get() for key, var in self.header_vars.items()}
        modbus_data_text = self.modbus_text.get("1.0", tk.END)

        if not modbus_data_text.strip():
            messagebox.showerror("Erreur", "La zone de texte de la table Modbus est vide.")
            return

        parsed_registers = parse_modbus_text(modbus_data_text)

        if not parsed_registers:
            messagebox.showwarning("Avertissement", "Aucun registre n'a pu être analysé à partir du texte fourni. Veuillez vérifier le format.")
            return

        csv_content = generate_csv_data(parsed_registers, header_info)

        # Open a "Save As" dialog
        model_name = header_info.get('model', 'definition')
        filename = f"webdyn_def_{model_name}.csv"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            initialfile=filename,
            title="Enregistrer le fichier de définition Modbus"
        )

        if not filepath:
            # User cancelled the save dialog
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
