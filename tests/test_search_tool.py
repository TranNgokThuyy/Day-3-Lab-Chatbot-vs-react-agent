from src.tools.search_tool import search_documents


def test_search_documents_returns_relevant_doc():
    result = search_documents("ReAct agents")
    assert "doc_agent.txt" in result
    assert "matches=" in result


def test_search_documents_no_match():
    result = search_documents("qxwyz")
    assert "No documents matched the query" in result
