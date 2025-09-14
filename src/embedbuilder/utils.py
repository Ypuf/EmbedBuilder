from typing import List


def chunk_text(description: str, max_chunk_size: int = 4096, max_chunks: int = 10) -> List[str]:
    text = description.strip()
    if not text:
        return [""]

    if len(text) <= max_chunk_size:
        return [text]

    if len(text) > max_chunks * max_chunk_size:
        return _simple_chunk(text, max_chunk_size, max_chunks)

    try:
        return _smart_chunk(text, max_chunk_size, max_chunks)
    except (RecursionError, MemoryError):
        return _simple_chunk(text, max_chunk_size, max_chunks)


def _simple_chunk(text: str, max_chunk_size: int, max_chunks: int) -> List[str]:
    chunks = []
    for i in range(0, len(text), max_chunk_size):
        if len(chunks) >= max_chunks:
            break
        chunks.append(text[i:i + max_chunk_size])
    return chunks


def _smart_chunk(text: str, max_chunk_size: int, max_chunks: int) -> List[str]:
    chunks = []
    pos = 0

    while pos < len(text) and len(chunks) < max_chunks:
        end_pos = min(pos + max_chunk_size, len(text))

        if end_pos >= len(text):
            chunks.append(text[pos:].rstrip())
            break

        chunk_text = text[pos:end_pos]
        split_pos = _find_best_split(chunk_text, max_chunk_size)

        actual_end = pos + split_pos
        chunks.append(text[pos:actual_end].rstrip())

        pos = actual_end
        while pos < len(text) and text[pos].isspace():
            pos += 1

    return chunks


def _find_best_split(chunk: str, max_size: int) -> int:
    min_split_pos = max_size // 3

    last_para = chunk.rfind('\n\n')
    if last_para > min_split_pos:
        return last_para + 2

    last_sentence = chunk.rfind('. ')
    if last_sentence > min_split_pos:
        return last_sentence + 2

    last_line = chunk.rfind('\n')
    if last_line > min_split_pos:
        return last_line + 1

    last_space = chunk.rfind(' ')
    if last_space > min_split_pos:
        return last_space + 1

    return max_size


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
