import math
import re


def estimate_text_tokens(text: str) -> int:
    if not text:
        return 0
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    non_chinese = re.sub(r"[\u4e00-\u9fff]", "", text)
    non_space_chars = len(re.sub(r"\s+", "", non_chinese))
    return chinese_chars + math.ceil(non_space_chars / 4)


def estimate_messages_tokens(messages: list[dict]) -> int:
    total = 0
    for message in messages:
        total += 4
        total += estimate_text_tokens(str(message.get("role", "")))
        total += estimate_text_tokens(str(message.get("content", "")))
    return total
