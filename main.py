from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from rembg import remove
from PIL import Image
import io
import logging

app = FastAPI(title="Free Background Removal API",
              description="Upload image → Get background removed PNG (using rembg)",
              version="1.0")

# Logging setup (Render console mein errors dekhne ke liye helpful)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {
        "message": "Background Removal API is running! 🚀",
        "how_to_use": "POST image file to /remove-bg/",
        "docs": "/docs (Swagger UI)"
    }

@app.post("/remove-bg/")
async def remove_background(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (jpg, png, etc.)")

    try:
        # Image padho
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        logger.info(f"Processing image: {file.filename}, size: {input_image.size}")
        
        # rembg se background remove (magic line)
        output_image = remove(input_image)
        
        # Transparent PNG bytes mein convert
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        
        logger.info("Background removed successfully")
        
        return StreamingResponse(
            img_byte_arr,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=removed-bg-{file.filename.split('.')[0]}.png"
            }
        )
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Optional: Health check for Render
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
