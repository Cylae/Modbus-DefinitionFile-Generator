# Modbus Definition Generator for Webdyn

This tool is a desktop application used to generate Modbus definition files (`.csv`) for WebdynSunPM equipment from an equipment's technical documentation.

It was designed to automate the creation process of these files, thereby reducing manual errors and speeding up deployment.

## Technologies Used

*   **Python 3**: The main programming language used for the entire application.
*   **Tkinter**: Python's standard library for creating graphical user interfaces (GUI). Using Tkinter ensures that no external library installation is required to run the script if Python is already installed.

## Deployment and Launch (from source code)

To use this application, you must have Python 3 installed on your Windows system.

1.  **Save the files**: Ensure that the `gui_app.py` and `parser.py` files are in the same directory.
2.  **Launch the application**: Open a command prompt (`cmd`) or PowerShell in this directory and run the following command:
    ```bash
    python gui_app.py
    ```
3.  The application's graphical interface should then open.

## Using the Application

The application's interface is simple and designed to be intuitive.

1.  **Fill in the header**: The fields in the "Header Information" section are pre-filled with example values (based on the Huawei inverter). Modify them as needed to match your equipment.
2.  **Paste the Modbus table**: Copy the entire table of register definitions from the PDF document or your equipment's source (usually the "Register Definitions" chapter). Paste this raw text into the large "Modbus Table" text area.
3.  **Generate the file**: Click the "Generate and Save CSV File" button.
4.  **Save the file**: A "Save As" dialog box will open. Choose the location where you want to save your `.csv` definition file and click "Save". The filename is automatically suggested based on the equipment model.
5.  A success message will be displayed to confirm that the file has been saved successfully.

## Compiling into a Windows Executable (`.exe`)

If you want to distribute this application as a single `.exe` file that does not require end-users to have Python installed, you can compile it using the `PyInstaller` tool.

1.  **Install PyInstaller**: If you don't already have it, open a command prompt and install it using `pip`, Python's package manager.
    ```bash
    pip install pyinstaller
    ```
2.  **Compile the script**: Still in your terminal, navigate to the directory containing `gui_app.py` and `parser.py`. Run the following command:
    ```bash
    pyinstaller --onefile --windowed --name "ModbusDefGenerator" gui_app.py
    ```
    *   `--onefile`: Bundles the application and all its dependencies into a single executable file.
    *   `--windowed`: Prevents a black console from opening in the background when running the application, which is ideal for a GUI application.
    *   `--name "ModbusDefGenerator"`: Sets the name of the `.exe` file that will be created.

3.  **Find the executable**: Once the compilation is complete (it may take a minute), you will find a new folder named `dist` in your directory. Inside this folder is your `ModbusDefGenerator.exe` application, ready to be used and distributed on any Windows computer.
