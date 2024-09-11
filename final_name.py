import json
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

# Configure Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Function to extract text from image using pytesseract
def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

# Function to filter English text from the OCR text
def filter_english_text(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters

# Function to detect gender from text
def detect_gender(text):
    text = text.lower()
    if 'female' in text:
        return 'Female'
    else:
        return 'Male'
    

# Function to find the name which is exactly before the DOB
def find_name(text, dob_start_pos):
    # Extract the portion of text before the DOB
    text_before_dob = text[:dob_start_pos].strip()
    
    # Remove empty lines and split into lines
    lines_before_dob = [line.strip() for line in text_before_dob.split('\n') if line.strip()]
    
    if not lines_before_dob:
        return "Not Found"

    # The last non-empty line before DOB is considered as the potential name
    potential_name = lines_before_dob[-2]
    if len(potential_name) > 15:
        potential_name = lines_before_dob[-2].split()
        
        name = ""
        for char in potential_name:
            if len(char) > 1:
                name += ' ' + char
            elif len(char) == 1:
                name += ' ' + char
                
                return name
    return potential_name

    # Refined regex pattern to capture names
    # name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2}(?:\s[A-Z])?\b', re.MULTILINE)
    # if name_pattern.fullmatch(potential_name):
    #     return potential_name

    return "Not Found"
# Function to extract Aadhaar details from text
def extract_aadhaar_details(text):
    details = {}

    # Filter out non-English text
    text = filter_english_text(text)

    # Regex patterns
    aadhaar_pattern = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
    dob_pattern = re.compile(r"(\d{2}[/-]\d{2}[/-]\d{4})")
    phone_pattern = re.compile(r"\b\d{10}\b")

    # Search for Aadhaar number, DOB, and phone number
    aadhaar_number = aadhaar_pattern.search(text)
    dob = dob_pattern.search(text)
    phone = phone_pattern.search(text)

    # Find Name using the updated name pattern (exactly before DOB)
    if dob:
        dob_start_pos = dob.start()  # Get the position of DOB in the text
        name = find_name(text, dob_start_pos)
    else:
        name = "Not Found"

    # Detect gender
    gender = detect_gender(text)

    # Store extracted details
    if aadhaar_number:
        details['Aadhaar Number'] = aadhaar_number.group()
    if name != "Not Found":
        details['Name'] = name
    if dob:
        details['Date of Birth'] = dob.group()
    if gender != "Not Found":
        details['Gender'] = gender
    if phone:
        details['Phone Number'] = phone.group()

    return details

# Function to extract data from scanned PDF
def extract_data_from_pdf(pdf_path):
    # Open the PDF file
    doc = fitz.open(pdf_path)
    
    full_text = ""
    
    # Iterate through pages
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        images = page.get_images(full=True)
        
        # If images found on the page
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Convert the image to PIL format
            image = Image.open(io.BytesIO(image_bytes))
            
            # Apply OCR to extract text
            text = extract_text_from_image(image)
            
            full_text += text  # Collect text from all pages
    
    # Extract the details from the full OCR text
    details = extract_aadhaar_details(full_text)
    
    return details

# Path to the Aadhaar PDF
pdf_path = "scanned.pdf"

# Extract and print the final details
try:
    details = extract_data_from_pdf(pdf_path)
    
    # Specify the output JSON file name
    output_json_file = "aadhaar_details.json"
    
    # Write the extracted details to the JSON file
    with open(output_json_file, 'w') as json_file:
        json.dump(details, json_file, indent=4)  # Save in pretty-printed format
    
    print(f"Extracted Aadhaar details saved to {output_json_file}")
except Exception as e:
    print(e)
