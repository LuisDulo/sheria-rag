from app.db import apply_schema


def add_document(conn):
    return conn.execute(
        "INSERT INTO documents (url, agency, title, content_hash)"
        " VALUES ('https://x.test', 'KRA', 'PAYE', 'h') RETURNING id"
    ).fetchone()[0]


def add_chunk(conn, document_id, content="Employers deduct PAYE monthly"):
    conn.execute(
        "INSERT INTO chunks (document_id, position, heading, content, embedding)"
        " VALUES (%s, 0, 'Filing', %s, %s::vector)",
        (document_id, content, str([0.1] * 384)),
    )


def test_schema_can_be_applied_twice(conn):
    apply_schema(conn)
    apply_schema(conn)


def test_full_text_column_is_generated(conn):
    add_chunk(conn, add_document(conn))
    found = conn.execute(
        "SELECT count(*) FROM chunks WHERE search @@ plainto_tsquery('english', 'deducted')"
    ).fetchone()[0]
    assert found == 1


def test_deleting_a_document_removes_its_chunks(conn):
    document_id = add_document(conn)
    add_chunk(conn, document_id)
    conn.execute("DELETE FROM documents WHERE id = %s", (document_id,))
    assert conn.execute("SELECT count(*) FROM chunks").fetchone()[0] == 0
