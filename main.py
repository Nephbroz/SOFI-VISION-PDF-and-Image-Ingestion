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

def clean_ocr_text(raw_text: str) -> str:
    text = re.sub(r'\s+', ' ', raw_text) 
    text = re.sub(r'\|', '', text)
    return text.strip()

@app.post("/scan-document")
async def scan_document(file: UploadFile = File(...)):
    filename = file.filename.lower()
    content_type = file.content_type
    
    # Define supported formats
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")
    
    try:
        file_bytes = await file.read()
        extracted_results = []

        # CASE 1: PDF Processing
        if filename.endswith(".pdf") or content_type == "application/pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # High-res render for OCR
                matrix = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=matrix)
                
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                raw_text = pytesseract.image_to_string(image)
                extracted_results.append({
                    "page": page_num + 1,
                    "text_content": clean_ocr_text(raw_text)
                })
            doc.close()

        # CASE 2: Image Processing
        elif filename.endswith(image_extensions) or content_type.startswith("image/"):
            image = Image.open(io.BytesIO(file_bytes))
            raw_text = pytesseract.image_to_string(image)
            extracted_results.append({
                "page": 1,
                "text_content": clean_ocr_text(raw_text)
            })

        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload a PDF or an image (JPG, PNG, etc.)."
            )

        return {
            "filename": file.filename,
            "status": "Success",
            "type": "PDF" if filename.endswith(".pdf") else "Image",
            "pages_processed": len(extracted_results),
            "data": extracted_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)