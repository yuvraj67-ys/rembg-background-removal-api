import os
import io
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
import rembg

app = FastAPI(
    title="Background Removal API",
    description="100% Free Background Removal API using rembg (CPU) and FastAPI",
    version="1.0.0"
)

# MEMORY FIX: Render free tier has 512MB RAM. 
# Default 'u2net' model is heavy (~170MB). We use 'u2netp' (lighter, ~4MB).
# Global session banaya hai taaki har request pe model reload na ho (warna RAM crash hogi).
try:
    print("Loading AI Model into memory...")
    session = rembg.new_session("u2netp")
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    session = None

@app.get("/")
def read_root():
    return {"message": "API running. Go to /docs to test the API."}

@app.post("/remove-bg/")
async def remove_background(file: UploadFile = File(...)):
    # 1. File type validation
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (PNG, JPG, etc.)")
    
    if session is None:
        raise HTTPException(status_code=500, detail="AI Model failed to load.")

    try:
        # 2. Read image bytes
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents)).convert("RGBA")
        
        # 3. Process image using rembg with the lighter model session
        output_image = rembg.remove(input_image, session=session)
        
        # 4. Save output to bytes
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        
        # 5. Return as StreamingResponse
        return StreamingResponse(img_byte_arr, media_type="image/png")
        
    except Exception as e:
        # Error handling for processing fails
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# PORT BINDING FIX FOR RENDER
if __name__ == "__main__":
    # Render environment variable se port leta hai, default 10000 agar na mile.
    port = int(os.environ.get("PORT", 10000))
    # Host hamesha "0.0.0.0" hona chahiye external access ke liye
    uvicorn.run("main:app", host="0.0.0.0", port=port)
