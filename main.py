import io
import fitz 
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image
import re

#Meron na nito sa sofivision >>>>>
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="PDF and Image OCR API")

class CodeSubmission(BaseModel):
    code: str

def clean_ocr_text(raw_text: str) -> str:
    # Text cleaning, removing characters and spaces
    text = re.sub(r'\s+', ' ', raw_text) 
    text = re.sub(r'\|', '', text)
    return text.strip()

@app.post("/scan-pdf-text")
async def scan_pdf_text(file: UploadFile = File(...)):
    
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read the file into memory
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        extracted_results = []
        
        # Loop through pages
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Convert page to a high-res image
            matrix = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert the pixmap to a format PIL/Tesseract can read
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            raw_text = pytesseract.image_to_string(image)
            
            # Apply the cleaning revision
            clean_text = clean_ocr_text(raw_text)

            extracted_results.append({
                "page": page_num + 1,
                "text_content": clean_text
            })


        doc.close()

        return {
            "filename": file.filename,
            "status": "Success",
            "pages_processed": len(extracted_results),
            "data": extracted_results
        }

    except Exception as e:
        return {"status": "Error", "message": str(e)}

@app.post("/scan-image-text")
async def scan_image_text(file: UploadFile = File(...)):
    # Validate supported image formats
    allowed_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail=f"File must be one of: {allowed_extensions}")

    try:
        # Read image into memory
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Perform OCR directly on the image
        raw_text = pytesseract.image_to_string(image)
        
        # Apply the cleaning revision
        clean_text = clean_ocr_text(raw_text)

        return {
            "filename": file.filename,
            "status": "Success",
            "text_content":clean_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)   
    #