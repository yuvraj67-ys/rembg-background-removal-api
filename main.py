import os
import io
import gc  # Memory cleanup ke liye
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
import rembg

app = FastAPI(
    title="Background Removal API",
    description="Optimized for Render Free Tier (512MB RAM)",
    version="1.0.0"
)

# Global session with smaller model
print("Loading AI Model (u2netp) into memory...")
try:
    # u2netp is only ~4MB compared to u2net's ~170MB
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
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    
    if session is None:
        raise HTTPException(status_code=500, detail="AI Model failed to load.")

    try:
        # Read image
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents)).convert("RGBA")
        
        # Process image
        output_image = rembg.remove(input_image, session=session)
        
        # Save to buffer
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        
        # CLEAR MEMORY: Force Python to clear RAM immediately
        del input_image
        del output_image
        del contents
        gc.collect()
        
        return StreamingResponse(img_byte_arr, media_type="image/png")
        
    except Exception as e:
        # Emergency memory cleanup in case of error
        gc.collect()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
