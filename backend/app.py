from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

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
