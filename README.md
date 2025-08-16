# Générateur de Définition Modbus pour Webdyn

Cet outil est une application de bureau qui permet de générer des fichiers de définition Modbus (`.csv`) pour les équipements WebdynSunPM à partir de la documentation technique d'un équipement.

Il a été conçu pour automatiser le processus de création de ces fichiers, réduisant ainsi les erreurs manuelles et accélérant le déploiement.

## Technologies Utilisées

*   **Python 3**: Le langage de programmation principal utilisé pour l'ensemble de l'application.
*   **Tkinter**: La bibliothèque standard de Python pour la création d'interfaces graphiques (GUI). L'utilisation de Tkinter garantit qu'aucune installation de bibliothèque externe n'est nécessaire pour exécuter le script si Python est déjà installé.

## Déploiement et Lancement (depuis le code source)

Pour utiliser cette application, vous devez avoir Python 3 installé sur votre système Windows.

1.  **Sauvegardez les fichiers** : Assurez-vous que les fichiers `gui_app.py` et `parser.py` se trouvent dans le même répertoire.
2.  **Lancez l'application** : Ouvrez une invite de commande (`cmd`) ou un PowerShell dans ce répertoire et exécutez la commande suivante :
    ```bash
    python gui_app.py
    ```
3.  L'interface graphique de l'application devrait alors s'ouvrir.

## Utilisation de l'application

L'interface de l'application est simple et conçue pour être intuitive.

1.  **Remplir l'en-tête** : Les champs dans la section "Informations d'en-tête" sont pré-remplis avec des valeurs d'exemple (basées sur l'onduleur Huawei). Modifiez-les si nécessaire pour correspondre à votre équipement.
2.  **Coller la table Modbus** : Copiez l'intégralité du tableau de définitions de registres depuis le document PDF ou la source de votre équipement (généralement le chapitre "Register Definitions"). Collez ce texte brut dans la grande zone de texte "Table Modbus".
3.  **Générer le fichier** : Cliquez sur le bouton "Générer et Enregistrer le Fichier CSV".
4.  **Enregistrer le fichier** : Une boîte de dialogue "Enregistrer sous" s'ouvrira. Choisissez l'emplacement où vous souhaitez sauvegarder votre fichier de définition `.csv` et cliquez sur "Enregistrer". Le nom du fichier est automatiquement suggéré en fonction du modèle d'équipement.
5.  Un message de succès s'affichera pour confirmer que le fichier a bien été enregistré.

## Compilation en un Exécutable Windows (`.exe`)

Si vous souhaitez distribuer cette application en tant que fichier `.exe` unique qui n'exige pas que les utilisateurs finaux aient Python installé, vous pouvez la compiler en utilisant l'outil `PyInstaller`.

1.  **Installez PyInstaller** : Si vous ne l'avez pas déjà, ouvrez une invite de commande et installez-le en utilisant `pip`, le gestionnaire de paquets de Python.
    ```bash
    pip install pyinstaller
    ```
2.  **Compilez le script** : Toujours depuis votre terminal, naviguez jusqu'au répertoire contenant `gui_app.py` et `parser.py`. Exécutez la commande suivante :
    ```bash
    pyinstaller --onefile --windowed --name "ModbusDefGenerator" gui_app.py
    ```
    *   `--onefile` : Regroupe l'application et toutes ses dépendances en un seul fichier exécutable.
    *   `--windowed` : Empêche l'ouverture d'une console noire en arrière-plan lors de l'exécution de l'application, ce qui est idéal pour une application GUI.
    *   `--name "ModbusDefGenerator"` : Définit le nom du fichier `.exe` qui sera créé.

3.  **Trouvez l'exécutable** : Une fois la compilation terminée (cela peut prendre une minute), vous trouverez un nouveau dossier nommé `dist` dans votre répertoire. À l'intérieur de ce dossier se trouve votre application `ModbusDefGenerator.exe`, prête à être utilisée et distribuée sur n'importe quel ordinateur Windows.
