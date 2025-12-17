from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 👇 CORS configuration (this fixes "Failed to fetch")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PageData(BaseModel):
    text: str

@app.post("/analyze")
def analyze(data: PageData):
    scam_words = ["urgent", "verify", "reward"]
    score = 0

    for word in scam_words:
        if word in data.text.lower():
            score += 1

    return {"scam_score": score}
