import re
from typing import List


def chunk_text(description: str, max_chunk_size: int = 4096, max_chunks: int = 10) -> List[str]:
    def split_by_hierarchy(text: str, max_size: int) -> List[str]:
        splitters = [
            ('\n\n+', 'double_newline'),
            ('\n', 'single_newline'),
            (r'[.!?]+\s+', 'sentence'),
            (r'[;:]\s+', 'clause'),
            (r',\s+', 'comma'),
            (r'\s+', 'word')
        ]

        def try_split(text: str, pattern: str) -> List[str]:
            if pattern == 'word':
                return text.split()
            else:
                parts = re.split(pattern, text)
                return [part.strip() for part in parts if part.strip()]

        for pattern, name in splitters:
            parts = try_split(text, pattern)

            if all(len(part) <= max_size for part in parts):
                return parts

            result = []
            for part in parts:
                if len(part) <= max_size:
                    result.append(part)
                else:
                    sub_parts = split_by_hierarchy(part, max_size)
                    result.extend(sub_parts)

            return result

        return [text[i:i+max_size] for i in range(0, len(text), max_size)]

    text = description.strip()
    if not text:
        raise ValueError("Description cannot be empty")

    raw_chunks = split_by_hierarchy(text, max_chunk_size)

    final_chunks = []
    current_chunk = ""

    for chunk in raw_chunks:
        if len(current_chunk) + len(chunk) + 1 <= max_chunk_size:
            current_chunk += (" " + chunk if current_chunk else chunk)
        else:
            if current_chunk:
                final_chunks.append(current_chunk)
            current_chunk = chunk

    if current_chunk:
        final_chunks.append(current_chunk)

    return final_chunks[:max_chunks]


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
