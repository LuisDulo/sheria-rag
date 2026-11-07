"""Turn downloaded HTML or PDF into sections of clean text, then into search-sized chunks."""

import io
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup
from pypdf import PdfReader

REMOVED_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "aside", "form", "iframe"]
HEADINGS = {"h1", "h2", "h3", "h4", "h5"}
TEXT_BLOCKS = {"p", "li", "tr", "dt", "dd", "blockquote"}


@dataclass
class Section:
    heading: str
    text: str


@dataclass
class Chunk:
    heading: str
    content: str


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_html(html: str | bytes, selector: str | None = None) -> list[Section]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(REMOVED_TAGS):
        tag.decompose()
    root = soup.select_one(selector) if selector else (soup.body or soup)
    if root is None:  # falling back to the whole page would store menus as if they were guidance
        raise ValueError(f"selector {selector!r} matched nothing")

    sections: list[Section] = []
    heading, blocks = "", []

    def flush() -> None:
        if blocks:
            sections.append(Section(heading, "\n".join(blocks)))
            blocks.clear()

    for element in root.find_all(HEADINGS | TEXT_BLOCKS):
        if element.name in HEADINGS:
            flush()
            heading = clean(element.get_text(" "))
        elif not element.find_parent(TEXT_BLOCKS):  # a <p> inside <li> is already counted
            separator = " | " if element.name == "tr" else " "
            cells = element.find_all(["td", "th"]) if element.name == "tr" else [element]
            text = separator.join(clean(cell.get_text(" ")) for cell in cells)
            if text.strip(" |"):
                blocks.append(text)
    flush()
    return sections


def extract_pdf(data: bytes) -> list[Section]:
    pages = PdfReader(io.BytesIO(data)).pages
    sections = []
    for number, page in enumerate(pages, start=1):
        if text := clean(page.extract_text() or ""):
            sections.append(Section(f"Page {number}", text))
    return sections


def split_section(section: Section, max_words: int = 180, overlap: int = 30) -> list[Chunk]:
    """Pack whole lines into chunks; only a line longer than a chunk is cut mid-way."""
    words_per_line = [line.split() for line in section.text.split("\n")]
    pieces: list[list[str]] = []
    for words in words_per_line:
        for start in range(0, len(words), max_words):
            pieces.append(words[start : start + max_words])

    chunks: list[Chunk] = []
    current: list[str] = []
    for piece in pieces:
        if current and len(current) + len(piece) > max_words:
            chunks.append(Chunk(section.heading, " ".join(current)))
            current = current[-overlap:]
        current = current + piece
    if current:
        chunks.append(Chunk(section.heading, " ".join(current)))
    return chunks


def chunk_sections(sections: list[Section], min_words: int = 8) -> list[Chunk]:
    chunks = [chunk for section in sections for chunk in split_section(section)]
    return [chunk for chunk in chunks if len(chunk.content.split()) >= min_words]
