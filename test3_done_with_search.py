import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scripts.pdf_conversion import convert_scanned_pdf_to_ocr,is_scanned_pdf
from scripts.docx_conversion import convert_docx_to_searchable,is_scanned_word
from scripts.file_searching import search_files

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

class UnifiedDocumentApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Unified Document Converter")
        self.geometry("800x600")

        # Initialize variables
        self.doc_paths_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.monitor_directory = tk.StringVar()
        self.observer = None
        self.file_handler = None

        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TButton', padding=6, relief="flat", background="#eee")
        self.style.configure('TLabel', padding=6)

        # Top frame for document conversion and search input
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 10))
        top_frame.pack(fill=tk.X)

        doc_label = ttk.Label(top_frame, text="Document Path(s):")
        doc_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        doc_path_entry = ttk.Entry(top_frame, textvariable=self.doc_paths_var, width=60)
        doc_path_entry.grid(row=0, column=1, padx=5, pady=5)

        select_button = ttk.Button(top_frame, text="Select Document(s)", command=self.select_documents)
        select_button.grid(row=0, column=2, padx=5, pady=5)

        convert_button = ttk.Button(top_frame, text="Convert", command=self.convert_documents)
        convert_button.grid(row=0, column=3, padx=5, pady=5)

        search_label = ttk.Label(top_frame, text="Enter word or sentence to search:")
        search_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=60)
        search_entry.grid(row=1, column=1, padx=5, pady=5)

        search_button = ttk.Button(top_frame, text="Search", command=self.search_files)
        search_button.grid(row=1, column=2, padx=5, pady=5)

        refresh_button = ttk.Button(top_frame, text="Refresh", command=self.refresh_file_list)
        refresh_button.grid(row=1, column=3, padx=5, pady=5)

        # Directory monitoring frame
        monitoring_frame = ttk.Frame(self, padding=(10, 10, 10, 10))
        monitoring_frame.pack(fill=tk.X)

        monitor_label = ttk.Label(monitoring_frame, text="Directory to Watch:")
        monitor_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        monitor_entry = ttk.Entry(monitoring_frame, textvariable=self.monitor_directory, width=60)
        monitor_entry.grid(row=0, column=1, padx=5, pady=5)

        select_dir_button = ttk.Button(monitoring_frame, text="Select Directory", command=self.select_directory)
        select_dir_button.grid(row=0, column=2, padx=5, pady=5)

        start_monitor_button = ttk.Button(monitoring_frame, text="Start Monitoring", command=self.start_monitoring)
        start_monitor_button.grid(row=0, column=3, padx=5, pady=5)

        stop_monitor_button = ttk.Button(monitoring_frame, text="Stop Monitoring", command=self.stop_monitoring)
        stop_monitor_button.grid(row=0, column=4, padx=5, pady=5)

        # File list display
        self.file_listbox = tk.Listbox(self, selectmode=tk.SINGLE, height=20, width=80)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.file_listbox.bind("<Double-1>", self.open_selected_file)

        # Status and progress
        self.status_label = ttk.Label(self, text="Status: Waiting for action...")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X)

        self.progress_bar = ttk.Progressbar(self, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT, padx=10, pady=10)

        # Folder to store converted files
        self.converted_folder = 'converted'
        if not os.path.exists(self.converted_folder):
            os.makedirs(self.converted_folder)

        # Refresh the file list on startup
        self.refresh_file_list()

        # Initialize file monitoring system
        self.file_monitor_app = FileMonitorApp(self)

    def select_documents(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Document files", "*.pdf *.docx")],
            title="Select Documents"
        )
        if file_paths:
            self.doc_paths_var.set("; ".join(file_paths))
            self.status_label.config(text="Status: Documents Selected")

    def convert_documents(self):
        doc_paths = self.doc_paths_var.get().split("; ")
        if not doc_paths or doc_paths == ['']:
            messagebox.showwarning("No Documents Selected", "Please select documents to convert.")
            return

        self.status_label.config(text="Status: Converting...")
        self.progress_bar.start()

        for doc_path in doc_paths:
            if not os.path.exists(doc_path):
                continue

            if doc_path.lower().endswith(".pdf"):
                output_path = os.path.join(self.converted_folder, os.path.basename(doc_path).replace(".pdf", "_converted.pdf"))
                threading.Thread(target=self.convert_pdf, args=(doc_path, output_path)).start()
            elif doc_path.lower().endswith(".docx"):
                output_path = os.path.join(self.converted_folder, os.path.basename(doc_path).replace(".docx", "_searchable.docx"))
                threading.Thread(target=self.convert_docx, args=(doc_path, output_path)).start()

    def convert_pdf(self, doc_path, output_path):
        try:
            convert_scanned_pdf_to_ocr(doc_path, output_path)
            self.status_label.config(text=f"Status: Conversion completed for {doc_path}")
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {str(e)}")
        finally:
            self.progress_bar.stop()
            self.refresh_file_list()  # Refresh the file list after conversion

    def convert_docx(self, doc_path, output_path):
        try:
            convert_docx_to_searchable(doc_path, output_path)
            self.status_label.config(text=f"Searchable DOCX saved as: {output_path}")
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {str(e)}")
        finally:
            self.progress_bar.stop()
            self.refresh_file_list()  # Refresh the file list after conversion

    def search_files(self):
        search_term = self.search_var.get()
        if not search_term:
            messagebox.showwarning("No Search Term", "Please enter a search term.")
            return

        self.file_listbox.delete(0, tk.END)
        files = search_files(search_term, self.converted_folder)
        for file in files:
            self.file_listbox.insert(tk.END, file)
        self.status_label.config(text="Status: File list updated")

    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for root, dirs, files in os.walk(self.converted_folder):
            for file in files:
                file_path = os.path.join(root, file)
                self.file_listbox.insert(tk.END, file_path)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.monitor_directory.set(directory)
            self.file_monitor_app.monitor_directory.set(directory)
            self.status_label.config(text="Status: Directory Selected")

    def start_monitoring(self):
        self.file_monitor_app.start_monitoring()

    def stop_monitoring(self):
        self.file_monitor_app.stop_monitoring()

    def open_selected_file(self, event):
        selected_item = self.file_listbox.get(tk.ACTIVE)
        if not selected_item:
            return

        file_path = selected_item.split(" - ")[0].strip()

        if os.path.exists(file_path):
            try:
                os.startfile(file_path)  # On Windows
                # For other OS, use appropriate method:
                # subprocess.call(['open', file_path])  # For macOS
                # subprocess.call(['xdg-open', file_path])  # For Linux
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")

class FileMonitorApp:
    def __init__(self, root):
        self.root = root
        self.monitor_directory = tk.StringVar()
        self.observer = None
        self.file_records = []

        self.file_handler = FileHandler(self)

    def start_monitoring(self):
        directory = self.monitor_directory.get()
        if not directory:
            messagebox.showwarning("Warning", "Please select a directory to monitor.")
            return

        self.file_records = []
        self.root.refresh_file_list()  # Refresh file list on start
        self.observer = Observer()
        self.observer.schedule(self.file_handler, directory, recursive=False)
        self.observer.start()
        self.root.status_label.config(text=f"Monitoring directory: {directory}")

    def stop_monitoring(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.root.status_label.config(text="Monitoring stopped.")

class FileHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path.endswith('.pdf'):
                LOGGER.info(f"New PDF file detected: {file_path}")
                self.handle_pdf(file_path)
            elif file_path.endswith('.docx') or file_path.endswith('.doc'):
                LOGGER.info(f"New Word document detected: {file_path}")
                self.handle_word(file_path)

    def handle_pdf(self, pdf_path):
        if self.is_file_stable(pdf_path):
            self.process_pdf(pdf_path)
        else:
            LOGGER.warning(f"File {pdf_path} is still being downloaded or is unstable.")

    def handle_word(self, word_path):
        if self.is_file_stable(word_path):
            self.process_word(word_path)
        else:
            LOGGER.warning(f"File {word_path} is still being downloaded or is unstable.")

    def is_file_stable(self, file_path, checks=5, delay=0.6):
        try:
            initial_size = os.path.getsize(file_path)
            for _ in range(checks):
                time.sleep(delay)
                current_size = os.path.getsize(file_path)
                if current_size != initial_size:
                    return False
                initial_size = current_size
            return True
        except Exception as e:
            LOGGER.warning(f"Failed to check file stability: {e}")
            return False

    def process_pdf(self, pdf_path):
        if is_scanned_pdf(pdf_path):
            LOGGER.info(f"{os.path.basename(pdf_path)} is a scanned PDF. Converting to OCR...")
            try:
                convert_scanned_pdf_to_ocr(pdf_path)
                file_info = {
                    'name': os.path.basename(pdf_path),
                    'date': datetime.fromtimestamp(os.path.getctime(pdf_path)).strftime('%Y-%m-%d %H:%M:%S'),
                    'size': f"{os.path.getsize(pdf_path) / 1024:.2f} KB"
                }
                self.app.file_records.append(file_info)
                self.app.root.refresh_file_list()
                self.app.root.status_label.config(text=f"OCR conversion complete for {os.path.basename(pdf_path)}")
            except Exception as e:
                LOGGER.error(f"Failed to convert {os.path.basename(pdf_path)} to OCR: {e}")
        else:
            LOGGER.info(f"{os.path.basename(pdf_path)} is already machine-readable.")

    def process_word(self, word_path):
        if is_scanned_word(word_path):
            LOGGER.info(f"{os.path.basename(word_path)} is a scanned Word document. Converting to searchable Word document...")
            try:
                output_path = os.path.splitext(word_path)[0] + "_searchable.docx"
                convert_scanned_pdf_to_ocr(word_path, output_path)
                file_info = {
                    'name': os.path.basename(word_path),
                    'date': datetime.fromtimestamp(os.path.getctime(word_path)).strftime('%Y-%m-%d %H:%M:%S'),
                    'size': f"{os.path.getsize(word_path) / 1024:.2f} KB"
                }
                self.app.file_records.append(file_info)
                self.app.root.refresh_file_list()
                self.app.root.status_label.config(text=f"Conversion complete for {os.path.basename(word_path)}")
            except Exception as e:
                LOGGER.error(f"Failed to convert {os.path.basename(word_path)} to searchable Word document: {e}")
        else:
            LOGGER.info(f"{os.path.basename(word_path)} is already searchable.")

if __name__ == "__main__":
    app = UnifiedDocumentApp()
    app.mainloop()
