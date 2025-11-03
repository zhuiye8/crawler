"""Text splitting utilities for creating chunks"""

from typing import List


def split_text(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
    min_chunk_size: int = 50
) -> List[str]:
    """
    Split text into overlapping chunks

    Args:
        text: Input text to split
        chunk_size: Target size of each chunk (in characters)
        overlap: Number of characters to overlap between chunks
        min_chunk_size: Minimum chunk size to keep

    Returns:
        List of text chunks
    """
    if not text or len(text) < min_chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = min(start + chunk_size, text_length)

        # Try to break at sentence boundary if not at end
        if end < text_length:
            # Look for sentence endings within the last 20% of chunk
            search_start = int(end * 0.8)
            search_text = text[search_start:end + 50]

            # Find last sentence ending
            for delimiter in ['。', '！', '？', '.', '!', '?', '\n\n']:
                last_pos = search_text.rfind(delimiter)
                if last_pos != -1:
                    end = search_start + last_pos + 1
                    break

        # Extract chunk
        chunk = text[start:end].strip()

        # Only add if meets minimum size
        if len(chunk) >= min_chunk_size:
            chunks.append(chunk)

        # Move start position for next chunk
        start = end - overlap if end < text_length else text_length

    return chunks


def split_by_paragraphs(
    text: str,
    max_chunk_size: int = 500,
    min_chunk_size: int = 50
) -> List[str]:
    """
    Split text by paragraphs, merging small paragraphs

    Args:
        text: Input text
        max_chunk_size: Maximum size per chunk
        min_chunk_size: Minimum size per chunk

    Returns:
        List of text chunks
    """
    if not text:
        return []

    # Split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para_size = len(para)

        # If paragraph alone is too big, split it
        if para_size > max_chunk_size:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            # Split large paragraph
            chunks.extend(split_text(para, chunk_size=max_chunk_size, overlap=50))
        # If adding this paragraph exceeds max size, save current chunk
        elif current_size + para_size > max_chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        # Otherwise add to current chunk
        else:
            current_chunk.append(para)
            current_size += para_size

    # Add remaining chunk
    if current_chunk:
        final_chunk = '\n\n'.join(current_chunk)
        if len(final_chunk) >= min_chunk_size:
            chunks.append(final_chunk)

    return chunks
