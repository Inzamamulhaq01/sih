import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from pdf_conversion import convert_scanned_pdf_to_ocr
from file_searching import search_files
from docx_conversion import convert_docx_to_searchable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

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
        self.search_var.trace_add("write", self.debounce_search)
        self.search_thread = None
        self.search_timer = None
        self.debounce_time = 500  # milliseconds

        self.monitor_directory = tk.StringVar()
        self.observer = None
        self.file_records = []

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

        # Directory monitoring controls
        monitor_frame = ttk.Frame(self, padding=(10, 10, 10, 10))
        monitor_frame.pack(fill=tk.X)

        monitor_label = ttk.Label(monitor_frame, text="Monitor Directory:")
        monitor_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        monitor_entry = ttk.Entry(monitor_frame, textvariable=self.monitor_directory, width=60)
        monitor_entry.grid(row=0, column=1, padx=5, pady=5)

        select_monitor_button = ttk.Button(monitor_frame, text="Select Directory", command=self.select_directory)
        select_monitor_button.grid(row=0, column=2, padx=5, pady=5)

        start_monitor_button = ttk.Button(monitor_frame, text="Start Monitoring", command=self.start_monitoring)
        start_monitor_button.grid(row=1, column=0, padx=5, pady=5)

        stop_monitor_button = ttk.Button(monitor_frame, text="Stop Monitoring", command=self.stop_monitoring)
        stop_monitor_button.grid(row=1, column=1, padx=5, pady=5)

        # File list display
        self.files_listbox = tk.Listbox(self, selectmode=tk.SINGLE, height=20, width=80)
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.files_listbox.bind("<Double-1>", self.open_selected_file)

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
            # Here, convert_scanned_pdf_to_ocr will handle whether the PDF is scanned or not
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

        self.files_listbox.delete(0, tk.END)
        files = search_files(search_term, self.converted_folder)
        for file in files:
            self.files_listbox.insert(tk.END, file)
        self.status_label.config(text="Status: File list updated")

    def open_selected_file(self, event):
        selected_file = self.files_listbox.get(tk.ACTIVE)
        if selected_file:
            # Construct the full path to the selected file
            full_path = os.path.join(self.converted_folder, selected_file)
            os.startfile(full_path)

    def refresh_file_list(self):
        self.files_listbox.delete(0, tk.END)
        if os.path.exists(self.converted_folder):
            files = os.listdir(self.converted_folder)
            for file in files:
                self.files_listbox.insert(tk.END, os.path.basename(file))
        self.status_label.config(text="Status: File list refreshed")

    def debounce_search(self, *args):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(self.debounce_time, self.search_files)

    def select_directory(self):
        """Open a dialog to select a directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.monitor_directory.set(directory)

    def start_monitoring(self):
        """Start the monitoring thread."""
        directory = self.monitor_directory.get()
        if not directory:
            messagebox.showwarning("Warning", "Please select a directory to monitor.")
            return

        self.file_records = []
        self.update_file_list()
        self.event_handler = FileHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, directory, recursive=True)
        self.observer.start()
        self.status_label.config(text="Monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring thread."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.status_label.config(text="Monitoring stopped")

    def update_file_list(self):
        """Update the list of files in the directory."""
        directory = self.monitor_directory.get()
        if os.path.exists(directory):
            self.files_listbox.delete(0, 'end')
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.files_listbox.insert('end', file_path)
                    self.file_records.append(file_path)

class FileHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            LOGGER.info(f"New PDF detected: {event.src_path}")
            # Perform OCR conversion if it's a scanned PDF
            output_path = os.path.join(self.app.converted_folder, os.path.basename(event.src_path).replace(".pdf", "_converted.pdf"))
            threading.Thread(target=self.convert_if_scanned, args=(event.src_path, output_path)).start()

    def convert_if_scanned(self, src_path, output_path):
        # Replace this with your actual scanned PDF check
        if is_scanned_pdf(src_path):  # This is a placeholder for your scanned PDF check function
            try:
                convert_scanned_pdf_to_ocr(src_path, output_path)
                LOGGER.info(f"Conversion completed for: {src_path}")
                self.app.update_file_list()  # Refresh the file list after conversion
            except Exception as e:
                LOGGER.error(f"Error during conversion for {src_path}: {str(e)}")

def is_scanned_pdf(pdf_path):
    # Implement your logic to determine if the PDF is scanned
    return True  # Placeholder: always returns True for testing


if __name__ == "__main__":
    app = UnifiedDocumentApp()
    app.mainloop()
