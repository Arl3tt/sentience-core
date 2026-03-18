"""Light integration tests for LangGraph and ingest modules."""
from core.tools.ingest import ingest_text_file, ingest_pdf
from core.tools.langgraph_integration import create_bci_planner, run_sample_bci_plan

def test_ingest_text_file():
    """Test text file ingestion."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test EEG data\nLine 2")
        f.flush()
        temp_path = f.name
    try:
        # Mock ingest_document to avoid memory store dependency
        with patch("core.tools.ingest.ingest_document") as mock_ingest:
            mock_ingest.return_value = {"doc_id": temp_path, "status": "ok"}
            result = ingest_text_file(temp_path)
            mock_ingest.assert_called_once()
            assert result["status"] == "ok"
    finally:
        os.unlink(temp_path)

def test_ingest_text_file_with_id():
    """Test text ingestion with custom doc_id."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content")
        f.flush()
        temp_path = f.name
    try:
        with patch("core.tools.ingest.ingest_document") as mock_ingest:
            mock_ingest.return_value = {"doc_id": "custom_id", "status": "ok"}
            result = ingest_text_file(temp_path, doc_id="custom_id")
            # check that custom doc_id was used
            args, kwargs = mock_ingest.call_args
            assert args[0] == "custom_id"
    finally:
        os.unlink(temp_path)

def test_ingest_pdf():
    """Test PDF ingestion (mocked PdfReader)."""
    with patch("core.tools.ingest.PdfReader") as mock_pdf_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF page text"
        mock_pdf_reader.return_value.pages = [mock_page]

        with patch("core.tools.ingest.ingest_document") as mock_ingest:
            mock_ingest.return_value = {"doc_id": "pdf.pdf", "status": "ok"}
            result = ingest_pdf("pdf.pdf")
            assert result["status"] == "ok"

def test_create_bci_planner():
    """Test BCI planner creation."""
    planner = create_bci_planner()
    assert planner is not None
    assert hasattr(planner, "plan")

def test_langgraph_integration_import():
    """Test that langgraph_integration module can be imported."""
    from core.tools import langgraph_integration
    assert hasattr(langgraph_integration, "create_bci_planner")
    assert hasattr(langgraph_integration, "run_sample_bci_plan")
