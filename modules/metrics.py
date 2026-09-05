"""
InsightInMinutes - Metrics & Calculation Engine
Pure, decoupled functions for computing word statistics, reading time saved, and token metrics.
"""

from typing import Dict, Tuple, Any

# Standard adult reading speed in words per minute
WORDS_PER_MINUTE: int = 220
TOKEN_WORD_MULTIPLIER: float = 1.3


def compute_reading_metrics(original_text: str, summary_text: str) -> Dict[str, Any]:
    """
    Computes reading time saved and text compression metrics between
    the source document and the generated summary.
    """
    orig_words = len(original_text.split()) if original_text else 0
    summ_words = len(summary_text.split()) if summary_text else 0

    # Net words saved
    words_saved = max(0, orig_words - summ_words)
    time_saved_sec = int((words_saved / WORDS_PER_MINUTE) * 60)
    time_saved_mins = round(time_saved_sec / 60.0, 1)

    if time_saved_mins >= 1.0:
        time_saved_display = f"~{time_saved_mins:.1f}m"
    else:
        time_saved_display = f"{time_saved_sec}s"

    compression_pct = (
        int((1.0 - (summ_words / max(1, orig_words))) * 100)
        if orig_words > 0
        else 0
    )

    estimated_read_time_sec = max(1, int(summ_words / (WORDS_PER_MINUTE / 60.0)))
    read_time_orig_min = round(orig_words / WORDS_PER_MINUTE, 1) if orig_words > 0 else 0.0

    return {
        "orig_words": orig_words,
        "summ_words": summ_words,
        "words_saved": words_saved,
        "time_saved_sec": time_saved_sec,
        "time_saved_mins": time_saved_mins,
        "time_saved_display": time_saved_display,
        "compression_pct": compression_pct,
        "read_time_summary_sec": estimated_read_time_sec,
        "read_time_orig_min": read_time_orig_min,
    }


def estimate_tokens(prompt_text: str, completion_text: str) -> Tuple[int, int, int]:
    """
    Estimates input, output, and total token volumes based on word counts.
    """
    in_tok = int(len(prompt_text.split()) * TOKEN_WORD_MULTIPLIER) if prompt_text else 0
    out_tok = int(len(completion_text.split()) * TOKEN_WORD_MULTIPLIER) if completion_text else 0
    total_tok = in_tok + out_tok
    return in_tok, out_tok, total_tok
