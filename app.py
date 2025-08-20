import fitz  # PyMuPDF
import re
import uvicorn
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# --- Core Logic: PDF Word Counting ---

# This regex directly finds sequences of Devanagari characters, which is the most
# accurate way to define and count Hindi words.
HINDI_WORD_REGEX = re.compile(r'[\u0900-\u097F]+')

def count_hindi_words_in_pdf(pdf_content: bytes) -> int:
    """
    Opens a PDF from in-memory content, extracts text, and counts Hindi words.
    
    Args:
        pdf_content: The raw bytes of the PDF file.
        
    Returns:
        The total number of Hindi words found.
    """
    word_count = 0
    # Open the PDF directly from the byte stream
    with fitz.open(stream=pdf_content, filetype="pdf") as doc:
        # Iterate through each page
        for page in doc:
            text = page.get_text()
            # Find all matches for the regex and add the count
            hindi_words = HINDI_WORD_REGEX.findall(text)
            word_count += len(hindi_words)
    return word_count


# --- FastAPI Application Setup ---

app = FastAPI(title="Hindi Word Counter")

# Set up the template directory
templates = Jinja2Templates(directory="templates")


# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def get_upload_form(request: Request):
    """Serves the main HTML page with the file upload form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
async def handle_pdf_upload(request: Request, pdf_file: UploadFile = File(...)):
    """Handles the PDF file upload, counts words, and returns the result."""
    context = {"request": request}

    # Basic validation for file type
    if not pdf_file.filename.lower().endswith('.pdf'):
        context["error"] = "Invalid file type. Please upload a PDF."
        return templates.TemplateResponse("index.html", context)

    try:
        # Read the file content into memory
        file_bytes = await pdf_file.read()
        
        # Perform the word count
        total_words = count_hindi_words_in_pdf(file_bytes)
        
        # Add the result to the context to be displayed on the page
        context["word_count"] = total_words
        context["filename"] = pdf_file.filename

    except Exception as e:
        # Handle potential errors during PDF processing
        print(f"Error processing file {pdf_file.filename}: {e}")
        context["error"] = "Could not process the PDF file. It may be corrupt or invalid."
    
    return templates.TemplateResponse("index.html", context)


# --- For running the app directly ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)