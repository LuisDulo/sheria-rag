import pytest

from app.extract import Section, chunk_sections, extract_html, split_section

PAGE = """
<html><body>
  <nav><p>Home and every other menu link</p></nav>
  <div class="content">
    <h2>Filing</h2>
    <p>Employers file returns   by the 9th.</p>
    <ul><li><p>Pay online</p></li></ul>
    <h2>Rates</h2>
    <table><tr><td>Band</td><td>Rate</td></tr></table>
  </div>
  <div class="other"><p>Unrelated promotion</p></div>
  <footer><p>Copyright notice</p></footer>
</body></html>
"""


def test_keeps_text_under_its_heading():
    sections = extract_html(PAGE, ".content")
    assert [section.heading for section in sections] == ["Filing", "Rates"]
    assert sections[0].text == "Employers file returns by the 9th.\nPay online"


def test_table_rows_keep_their_cells_apart():
    assert extract_html(PAGE, ".content")[1].text == "Band | Rate"


def test_selector_excludes_the_rest_of_the_page():
    text = " ".join(section.text for section in extract_html(PAGE, ".content"))
    assert "promotion" not in text


def test_page_furniture_is_removed_without_a_selector():
    text = " ".join(section.text for section in extract_html(PAGE))
    assert "menu" not in text
    assert "Copyright" not in text


def test_selector_that_matches_nothing_is_an_error():
    with pytest.raises(ValueError):
        extract_html(PAGE, ".does-not-exist")


def test_long_sections_split_with_overlap_and_keep_their_heading():
    text = "\n".join(f"line {number} " + "word " * 48 for number in range(10))
    chunks = split_section(Section("Rates", text), max_words=120, overlap=20)
    assert len(chunks) > 1
    assert all(chunk.heading == "Rates" for chunk in chunks)
    assert all(len(chunk.content.split()) <= 140 for chunk in chunks)
    assert chunks[0].content.split()[-20:] == chunks[1].content.split()[:20]


def test_a_single_very_long_line_is_still_split():
    chunks = split_section(Section("", "word " * 500), max_words=100, overlap=0)
    assert len(chunks) == 5


def test_tiny_fragments_are_dropped():
    assert chunk_sections([Section("Menu", "Read more")]) == []
