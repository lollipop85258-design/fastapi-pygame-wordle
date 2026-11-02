import os
import random
import uuid
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Wordle API")

WORD_BANK = ["APPLE", "TRAIN", "HOUSE", "PLANT", "CLOUD"]
games_db: Dict[str, dict] = {}


class GuessRequest(BaseModel):
    game_id: str
    guess: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/new-game")
def start_new_game():
    game_id = str(uuid.uuid4())
    target_word = random.choice(WORD_BANK)
    games_db[game_id] = {
        "target": target_word,
        "status": "PLAYING"
    }
    return {"game_id": game_id, "message": "New game started!"}


@app.post("/api/guess")
def process_guess(req: GuessRequest):
    if req.game_id not in games_db:
        raise HTTPException(status_code=404, detail="Game session not found.")

    guess = req.guess.upper()
    if len(guess) != 5 or not guess.isascii() or not guess.isalpha():
        raise HTTPException(status_code=400, detail="Guess must be 5 English letters.")

    target = games_db[req.game_id]["target"]
    feedback = ["absent"] * 5
    counts = {}

    # 1. 計算目標單字字母數量
    for letter in target:
        counts[letter] = counts.get(letter, 0) + 1

    # 2. 判定綠色 (correct)
    for i in range(5):
        if guess[i] == target[i]:
            feedback[i] = "correct"
            counts[guess[i]] -= 1

    # 3. 判定黃色 (present)
    for i in range(5):
        if feedback[i] != "correct" and counts.get(guess[i], 0) > 0:
            feedback[i] = "present"
            counts[guess[i]] -= 1

    is_correct = (guess == target)
    if is_correct:
        games_db[req.game_id]["status"] = "WON"

    return {
        "guess": guess,
        "feedback": feedback,
        "is_correct": is_correct,
        "target_word": target if is_correct else None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)