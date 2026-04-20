"""
puzzle_rag.py
─────────────
RAG 評分引擎：
  Retrieve  → 從 puzzle_data 取得官方答案
  Augmented → 將官方答案注入 LLM prompt
  Generate  → LLM 判斷使用者的回答是否抓到關鍵
"""

import os

from openai import OpenAI

from puzzle_data import get_puzzle_by_id

MODEL    = os.getenv("LM_STUDIO_MODEL", "qwen/qwen2.5-3b-instruct")
BASE_URL = os.getenv("LM_STUDIO_URL",   "http://127.0.0.1:1234/v1")
TIMEOUT  = int(os.getenv("LM_TIMEOUT", "30"))

# ── 評分 prompt ───────────────────────────────────────────────────────────────
_JUDGE_PROMPT = """\
You are a strict but fair puzzle answer judge for a campus blockchain game.

Puzzle: {question}
Official Answer: {official_answer}
Key Points (must mention at least one): {key_points}
User's Answer: {user_answer}

Judging criteria:
- The user does NOT need to match the official answer word-for-word.
- The user MUST capture the core insight or key twist.
- For wordplay/pun puzzles: they must name the correct pun/answer.
- For logic puzzles: the final number/answer must be correct.
- For narrative puzzles: they must identify the key reason/twist.

Reply with EXACTLY this format (two lines only):
VERDICT: CORRECT   (or WRONG)
FEEDBACK: <one sentence in the same language the user used>"""


def evaluate_answer(puzzle_id: str, user_answer: str) -> dict:
    """
    Returns:
        {
            "correct": bool,
            "feedback": str,       # 給使用者看的說明
            "official_answer": str # 答錯時才顯示
        }
    """
    # ── Retrieve ─────────────────────────────────────────────────────────────
    puzzle = get_puzzle_by_id(puzzle_id)
    if not puzzle:
        return {"correct": False, "feedback": "找不到這道題目。", "official_answer": ""}

    official_answer = puzzle["answer"]
    key_points      = "、".join(puzzle.get("key_points", []))

    if not user_answer.strip():
        return {"correct": False, "feedback": "請輸入你的答案。", "official_answer": ""}

    # ── Generate (LLM judge) ─────────────────────────────────────────────────
    try:
        client = OpenAI(api_key="lm-studio", base_url=BASE_URL, timeout=TIMEOUT)
        prompt = _JUDGE_PROMPT.format(
            question=puzzle["question"],
            official_answer=official_answer,
            key_points=key_points,
            user_answer=user_answer,
        )
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=120,
        )
        text = resp.choices[0].message.content.strip()
        return _parse_verdict(text, official_answer)

    except Exception:
        # ── Fallback：關鍵字比對 ─────────────────────────────────────────────
        return _keyword_fallback(puzzle, user_answer, official_answer)


# ── 解析 LLM 回覆 ─────────────────────────────────────────────────────────────
def _parse_verdict(text: str, official_answer: str) -> dict:
    correct  = False
    feedback = "評分完成。"

    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("VERDICT:"):
            correct = "CORRECT" in line.upper()
        elif line.upper().startswith("FEEDBACK:"):
            feedback = line.split(":", 1)[1].strip()

    return {
        "correct": correct,
        "feedback": feedback,
        "official_answer": official_answer if not correct else "",
    }


# ── 關鍵字 fallback（LLM 不可用時） ──────────────────────────────────────────
def _keyword_fallback(puzzle: dict, user_answer: str, official_answer: str) -> dict:
    user_lower = user_answer.lower()
    key_points = puzzle.get("key_points", [])
    hit = any(kp.lower() in user_lower for kp in key_points)
    if hit:
        return {"correct": True,  "feedback": "答對了！關鍵詞正確。", "official_answer": ""}
    return {
        "correct": False,
        "feedback": "答錯了，沒有抓到關鍵。（AI 評分暫時離線，以關鍵字比對）",
        "official_answer": official_answer,
    }
