from typing import List
import re

class TextChunker:
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 4000,
        chunk_overlap: int = 400
    ) -> List[str]:
        """
        Splits text into chunks preserving paragraph and sentence boundaries.
        Avoids sending huge raw texts to LLM to prevent context overflow and HTTP 413.
        """
        if not text:
            return []

        text = text.strip()
        if len(text) <= chunk_size:
            return [text]

        # Split on double newlines (paragraphs) first
        paragraphs = re.split(r"\n\s*\n", text)
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)
            if current_len + para_len + 1 > chunk_size and current_chunk:
                combined = "\n\n".join(current_chunk)
                chunks.append(combined)

                # Keep overlap from end of previous chunk if possible
                overlap_text = combined[-chunk_overlap:] if len(combined) > chunk_overlap else ""
                current_chunk = [overlap_text, para] if overlap_text else [para]
                current_len = len(overlap_text) + para_len
            else:
                current_chunk.append(para)
                current_len += para_len + 1

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

