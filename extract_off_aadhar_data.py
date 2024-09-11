import re
from PyPDF2 import PdfReader


# Function to filter English text from the PDF content
def filter_english_text(text):
    # Remove non-English characters and keep only English letters, digits, and common punctuation
    english_text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
    return english_text

# Function to extract text from PDF using PyPDF2
def extract_text_from_pdf(pdf_path, password=None):
    try:
        reader = PdfReader(pdf_path)

        # Check if PDF is encrypted and decrypt it with the password
        if reader.is_encrypted:
            reader.decrypt(password)
        
        # Extract text from all pages
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        return text
    except Exception as e:
        raise Exception(f"Error extracting text: {e}")

# Function to find gender from text
def find_gender(text):
    text = text.lower()  # Convert text to lower case for case-insensitive matching
    if 'MALE' or 'male' in text:
        return 'Male'
    elif 'FEMALE' or 'female' in text:
        return 'Female'
    return 'Not Found'

# Function to extract Aadhaar details
def extract_aadhaar_details(text):
    details = {}

    # Filter out non-English text
    text = filter_english_text(text)

    # Split the text into lines for easier processing
    lines = text.splitlines()

    # Initialize variables to store name, DOB, and gender
    name = None
    dob = None
    gender = None

    # Regex pattern for identifying names (assuming names are in title case)
    name_pattern = re.compile(r'^[A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?', re.MULTILINE)
    
    # Iterate over lines to find the DOB and associated information
    for i, line in enumerate(lines):
        # Look for DOB line
        if re.search(r"(?:DOB|Date of Birth|DOB:)", line, re.IGNORECASE):
            dob = line.split(':')[-1].strip()
            # Try to find the name in the lines preceding the DOB line
            if i > 0:
                # Consider the lines above the DOB line for the name
                for j in range(i - 1, -1, -1):
                    candidate_name = lines[j].strip()
                    # Match candidate names using the name pattern
                    if name_pattern.match(candidate_name):
                        name = candidate_name
                        break
            # Gender is located directly below the DOB
            if i + 1 < len(lines):
                gender_line = lines[i + 1].strip()
                gender = find_gender(gender_line)
    
    # Extract Aadhaar Number (12 digit number)
    aadhaar_pattern = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
    aadhaar_number = aadhaar_pattern.search(text)
    if aadhaar_number:
        details['Aadhaar Number'] = aadhaar_number.group()

    # Store extracted details
    if name:
        details['Name'] = name
    if dob:
        details['Date of Birth'] = dob
    if gender:
        details['Gender'] = gender
        

    # Extract Phone Number (10-digit phone number)
    phone_pattern = re.compile(r"\b\d{10}\b")
    phone_number = phone_pattern.search(text)
    if phone_number:
        details['Phone Number'] = phone_number.group()

    return details

# File path to your Aadhaar PDF
pdf_path = ""

# Aadhaar PDF password (usually the first 4 letters of your name in uppercase + your birth year)
password = ""

# Extract text from the Aadhaar PDF
try:
    text = extract_text_from_pdf(pdf_path, password)

    # Extract Aadhaar details
    aadhaar_details = extract_aadhaar_details(text)

    # Display the extracted information
    print("Extracted Aadhaar Details:")
    for key, value in aadhaar_details.items():
        print(f"{key}: {value}")

except Exception as e:
    print(e)
