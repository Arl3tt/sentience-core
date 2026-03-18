"""Minimal pypdf stub used to satisfy imports in tests.

Provides `PdfReader` with a very small API (`pages` with `extract_text`).
This is a stub to avoid install-time failures; real PDF parsing will not work
with this lightweight implementation.
"""
import os
class Page:
    def extract_text(self):
        return ""

class PdfReader:
    def __init__(self, path):
        # Do not attempt to parse real PDFs in test environment; present empty pages
        self.pages = []
        if os.path.exists(path):
            # offer a single empty page placeholder
            self.pages = [Page()]
