import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from parser import parse_modbus_text, generate_csv_data, ParserError
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

        # --- Preview Pane ---
        preview_frame = ttk.LabelFrame(main_frame, text="Aperçu des Données", padding="10")
        preview_frame.pack(fill="both", expand=True, pady=5)

        self.tree = ttk.Treeview(preview_frame, show="headings")

        # Define columns
        self.tree["columns"] = ("index", "name", "address", "type", "unit", "gain", "scope")

        # Format columns
        self.tree.column("index", anchor=tk.CENTER, width=50)
        self.tree.column("name", anchor=tk.W, width=200)
        self.tree.column("address", anchor=tk.CENTER, width=80)
        self.tree.column("type", anchor=tk.CENTER, width=80)
        self.tree.column("unit", anchor=tk.CENTER, width=60)
        self.tree.column("gain", anchor=tk.CENTER, width=60)
        self.tree.column("scope", anchor=tk.W, width=300)

        # Create headings
        self.tree.heading("index", text="Index", anchor=tk.CENTER)
        self.tree.heading("name", text="Nom", anchor=tk.W)
        self.tree.heading("address", text="Adresse", anchor=tk.CENTER)
        self.tree.heading("type", text="Type", anchor=tk.CENTER)
        self.tree.heading("unit", text="Unité", anchor=tk.CENTER)
        self.tree.heading("gain", text="Gain", anchor=tk.CENTER)
        self.tree.heading("scope", text="Description", anchor=tk.W)

        # Add a scrollbar
        vsb = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x')
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.pack(fill="both", expand=True)

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

        # Clear previous results from the treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            parsed_registers = parse_modbus_text(self.filepath)

            if not parsed_registers:
                messagebox.showwarning("Avertissement", "Aucun registre Modbus n'a été trouvé dans les tables du document.")
                return

            # Populate the preview tree
            for reg in parsed_registers:
                values = (reg.index, reg.name, reg.address, reg.type, reg.unit, f"{reg.gain:.2f}", reg.scope)
                self.tree.insert("", tk.END, values=values)

            # Ask user to save the file
            csv_content = generate_csv_data(parsed_registers, header_info)
            model_name = header_info.get('model', 'definition')
            filename = f"webdyn_def_{model_name}.csv"

            save_filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
                initialfile=filename,
                title="Enregistrer le fichier de définition Modbus"
            )
            if not save_filepath:
                return

            with open(save_filepath, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)

            messagebox.showinfo("Succès", f"Fichier enregistré avec succès à l'emplacement :\n{save_filepath}")

        except ParserError as e:
            messagebox.showerror("Erreur de Parsing", str(e))
        except Exception as e:
            messagebox.showerror("Erreur Inattendue", f"Une erreur inattendue est survenue :\n{e}")

if __name__ == "__main__":
    app = ModbusDefGeneratorApp()
    app.mainloop()
