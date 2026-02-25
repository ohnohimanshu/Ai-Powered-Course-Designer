#!/usr/bin/env python3
"""
Test suite for YouTube and Documentation fetching in the research module.

Tests both YouTubeResearcher and DocResearcher with mocked external calls
to avoid hitting real APIs during testing.
"""
import os
import sys
import json
import django
from unittest.mock import patch, MagicMock, PropertyMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coursebuilder.settings')
django.setup()

# Mock heavy dependencies if not installed
try:
    import sentence_transformers
except ImportError:
    sys.modules['sentence_transformers'] = MagicMock()

try:
    import faiss
except ImportError:
    sys.modules['faiss'] = MagicMock()

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from research.researcher import YouTubeResearcher, DocResearcher, ResearchOrchestrator
from research.models import Resource, ResourceChunk


# =========================================================================
# YouTubeResearcher Tests
# =========================================================================

class YouTubeResearcherTest(TestCase):
    """Tests for the YouTubeResearcher class."""

    def test_extract_video_id_standard_url(self):
        """Test extracting video ID from standard YouTube URLs."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(YouTubeResearcher._extract_video_id(url), "dQw4w9WgXcQ")

    def test_extract_video_id_short_url(self):
        """Test extracting video ID from youtu.be short URLs."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(YouTubeResearcher._extract_video_id(url), "dQw4w9WgXcQ")

    def test_extract_video_id_with_extra_params(self):
        """Test extracting video ID from URLs with extra query parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s&list=PLx"
        self.assertEqual(YouTubeResearcher._extract_video_id(url), "dQw4w9WgXcQ")

    def test_extract_video_id_invalid_url(self):
        """Test that invalid URLs return None."""
        self.assertIsNone(YouTubeResearcher._extract_video_id("https://example.com"))
        self.assertIsNone(YouTubeResearcher._extract_video_id("not-a-url"))

    @patch('research.researcher.settings')
    @patch('research.researcher.YouTubeResearcher._search_youtube_api')
    @patch('research.researcher.YouTubeResearcher._fetch_transcript')
    def test_search_with_api_key(self, mock_transcript, mock_api_search, mock_settings):
        """Test YouTube search when API key is configured."""
        mock_settings.AI_ENGINE = {
            'YOUTUBE_API_KEY': 'test-api-key',
            'YOUTUBE_MAX_RESULTS': 2,
        }

        mock_api_search.return_value = [
            {
                'title': 'Python Tutorial',
                'url': 'https://www.youtube.com/watch?v=abc123def45',
                'description': 'A great tutorial',
                'metadata': {'source': 'youtube_api'},
            }
        ]
        mock_transcript.return_value = "Welcome to this Python tutorial where we cover all the basics of Python programming language including variables, data types, control structures, functions and more. " * 2

        results = YouTubeResearcher.search("Python", limit=2)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'youtube')
        self.assertEqual(results[0]['title'], 'Python Tutorial')
        self.assertEqual(results[0]['text'], "Welcome to this Python tutorial where we cover all the basics of Python programming language including variables, data types, control structures, functions and more. " * 2)
        mock_api_search.assert_called_once_with("Python", 2, 'test-api-key')

    @patch('research.researcher.settings')
    @patch('research.researcher.YouTubeResearcher._search_youtube_fallback')
    @patch('research.researcher.YouTubeResearcher._fetch_transcript')
    def test_search_fallback_when_no_api_key(self, mock_transcript, mock_fallback, mock_settings):
        """Test YouTube search falls back to DuckDuckGo when no API key."""
        mock_settings.AI_ENGINE = {
            'YOUTUBE_API_KEY': '',
            'YOUTUBE_MAX_RESULTS': 2,
        }

        mock_fallback.return_value = [
            {
                'title': 'Python Basics',
                'url': 'https://www.youtube.com/watch?v=xyz789abc12',
                'description': '',
                'metadata': {'source': 'duckduckgo_fallback'},
            }
        ]
        mock_transcript.return_value = "In this video we cover Python basics including variables, loops, functions, classes and modules. This comprehensive tutorial will help you understand Python programming. " * 2

        results = YouTubeResearcher.search("Python", limit=2)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], 'youtube')
        mock_fallback.assert_called_once()

    @patch('research.researcher.YouTubeResearcher._fetch_transcript')
    @patch('research.researcher.settings')
    @patch('research.researcher.YouTubeResearcher._search_youtube_fallback')
    def test_search_skips_videos_without_valid_id(self, mock_fallback, mock_settings, mock_transcript):
        """Test that videos with un-extractable IDs are skipped."""
        mock_settings.AI_ENGINE = {'YOUTUBE_API_KEY': '', 'YOUTUBE_MAX_RESULTS': 3}
        mock_fallback.return_value = [
            {'title': 'Bad URL', 'url': 'https://example.com/not-youtube', 'description': '', 'metadata': {}},
        ]

        results = YouTubeResearcher.search("Python", limit=3)
        self.assertEqual(len(results), 0)
        mock_transcript.assert_not_called()

    def test_extract_ddg_url(self):
        """Test DuckDuckGo URL extraction."""
        ddg_href = "/l/?uddg=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3Dabc123&rut=something"
        result = YouTubeResearcher._extract_ddg_url(ddg_href)
        self.assertIn("youtube.com/watch", result)


# =========================================================================
# DocResearcher Tests
# =========================================================================

class DocResearcherTest(TestCase):
    """Tests for the DocResearcher class."""

    def test_is_valid_doc_url_accepts_docs(self):
        """Test that documentation URLs are accepted."""
        self.assertTrue(DocResearcher._is_valid_doc_url("https://docs.python.org/3/tutorial"))
        self.assertTrue(DocResearcher._is_valid_doc_url("https://developer.mozilla.org/en-US/docs"))
        self.assertTrue(DocResearcher._is_valid_doc_url("https://realpython.com/python-generators"))

    def test_is_valid_doc_url_rejects_social(self):
        """Test that social media URLs are rejected."""
        self.assertFalse(DocResearcher._is_valid_doc_url("https://www.youtube.com/watch?v=abc"))
        self.assertFalse(DocResearcher._is_valid_doc_url("https://twitter.com/user/status/123"))
        self.assertFalse(DocResearcher._is_valid_doc_url("https://www.facebook.com/page"))
        self.assertFalse(DocResearcher._is_valid_doc_url("https://www.reddit.com/r/python"))

    def test_extract_text_strips_non_content(self):
        """Test that HTML extraction removes nav/footer/scripts."""
        html = """
        <html>
        <head><script>var tracking = true;</script></head>
        <body>
            <nav><a href="/">Home</a></nav>
            <article>
                <h1>Python Generators Tutorial</h1>
                <p>Generators are functions that return an iterator using yield.</p>
                <p>They are memory efficient for large datasets.</p>
            </article>
            <footer>Copyright 2024</footer>
        </body>
        </html>
        """
        text = DocResearcher._extract_text(html)

        self.assertIn("Python Generators Tutorial", text)
        self.assertIn("Generators are functions", text)
        self.assertNotIn("tracking", text)  # Script removed
        self.assertNotIn("Copyright", text)  # Footer removed

    def test_extract_text_empty_html(self):
        """Test extraction from empty/minimal HTML."""
        self.assertEqual(DocResearcher._extract_text("<html><body></body></html>"), "")

    @patch('research.researcher.requests.get')
    def test_fetch_page_content_success(self, mock_get):
        """Test successful page content fetching."""
        mock_resp = MagicMock()
        mock_resp.text = """
        <html><body>
            <article>
                <h1>Python Documentation</h1>
                <p>Python is a programming language that lets you work more quickly.</p>
            </article>
        </body></html>
        """
        mock_resp.headers = {'Content-Type': 'text/html; charset=utf-8'}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        text = DocResearcher._fetch_page_content("https://docs.python.org/3/")
        self.assertIn("Python", text)

    @patch('research.researcher.requests.get')
    def test_fetch_page_content_non_html(self, mock_get):
        """Test that non-HTML content returns empty string."""
        mock_resp = MagicMock()
        mock_resp.headers = {'Content-Type': 'application/pdf'}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        text = DocResearcher._fetch_page_content("https://example.com/file.pdf")
        self.assertEqual(text, "")

    @patch('research.researcher.requests.get')
    def test_fetch_page_content_timeout(self, mock_get):
        """Test graceful handling of timeout."""
        mock_get.side_effect = Exception("Connection timed out")
        text = DocResearcher._fetch_page_content("https://slow-site.com/docs")
        self.assertEqual(text, "")

    @patch('research.researcher.settings')
    @patch('research.researcher.DocResearcher._search_duckduckgo')
    @patch('research.researcher.DocResearcher._fetch_page_content')
    def test_search_returns_valid_docs(self, mock_fetch, mock_ddg, mock_settings):
        """Test full doc search pipeline."""
        mock_settings.AI_ENGINE = {'DOC_MAX_RESULTS': 2, 'DOC_REQUEST_TIMEOUT': 5}

        mock_ddg.return_value = [
            {
                'title': 'Python Generators - RealPython',
                'url': 'https://realpython.com/python-generators/',
                'snippet': 'Learn about generators in Python...',
            },
            {
                'title': 'YouTube Video',
                'url': 'https://www.youtube.com/watch?v=abc',
                'snippet': 'A video about generators',
            },
            {
                'title': 'Python Docs - Generators',
                'url': 'https://docs.python.org/3/howto/functional.html',
                'snippet': 'Functional programming howto...',
            },
        ]

        mock_fetch.side_effect = [
            "Generators in Python are a simple way of creating iterators. " * 5,  # realpython
            "Python supports several functional programming concepts. " * 5,      # docs.python
        ]

        results = DocResearcher.search("Python generators", limit=2)

        # Should skip YouTube URL
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['type'], 'documentation')
        self.assertIn('realpython', results[0]['url'])
        self.assertIn('docs.python', results[1]['url'])


# =========================================================================
# ResearchOrchestrator Integration Tests
# =========================================================================

class ResearchOrchestratorTest(TestCase):
    """Integration tests for the full research pipeline."""

    @patch('research.researcher.VectorStoreService.add_texts')
    @patch('research.researcher.EmbeddingService.chunk_text')
    @patch('research.researcher.DocResearcher.search')
    @patch('research.researcher.YouTubeResearcher.search')
    def test_research_topic_creates_resources(self, mock_yt, mock_doc, mock_chunk, mock_add):
        """Test that research_topic creates Resource objects in the database."""
        mock_yt.return_value = [
            {
                'type': 'youtube',
                'title': 'Generators Tutorial',
                'url': 'https://www.youtube.com/watch?v=unique_test_1',
                'description': 'A tutorial on generators',
                'text': 'Welcome to generators tutorial content here.',
                'metadata': {'source': 'test'},
            }
        ]
        mock_doc.return_value = [
            {
                'type': 'documentation',
                'title': 'Python Generators Docs',
                'url': 'https://docs.example.com/generators-unique-test',
                'description': 'Official docs',
                'text': 'Generators allow you to declare a function that behaves like an iterator.',
                'metadata': {'source': 'test'},
            }
        ]
        mock_chunk.return_value = ['chunk1', 'chunk2']

        resources = ResearchOrchestrator.research_topic("Python generators")

        # Should have found 2 resources
        self.assertEqual(len(resources), 2)

        # Should be saved in the DB
        self.assertTrue(
            Resource.objects.filter(url='https://www.youtube.com/watch?v=unique_test_1').exists()
        )
        self.assertTrue(
            Resource.objects.filter(url='https://docs.example.com/generators-unique-test').exists()
        )

        # Should have called chunk + embed
        self.assertEqual(mock_chunk.call_count, 2)
        self.assertEqual(mock_add.call_count, 2)

    @patch('research.researcher.VectorStoreService.add_texts')
    @patch('research.researcher.EmbeddingService.chunk_text')
    @patch('research.researcher.DocResearcher.search')
    @patch('research.researcher.YouTubeResearcher.search')
    def test_research_topic_skips_existing_resources(self, mock_yt, mock_doc, mock_chunk, mock_add):
        """Test that existing resources are not re-indexed."""
        # Pre-create a resource
        existing = Resource.objects.create(
            url='https://www.youtube.com/watch?v=existing_vid',
            resource_type='youtube',
            title='Existing Video',
            transcript_text='Already indexed content',
        )
        # Create a chunk so it's considered "already indexed"
        ResourceChunk.objects.create(
            resource=existing, chunk_text='already here', chunk_index=0
        )

        mock_yt.return_value = [
            {
                'type': 'youtube',
                'title': 'Existing Video',
                'url': 'https://www.youtube.com/watch?v=existing_vid',
                'text': 'Already indexed content',
                'metadata': {},
            }
        ]
        mock_doc.return_value = []

        ResearchOrchestrator.research_topic("test")

        # Should NOT re-chunk/re-embed
        mock_chunk.assert_not_called()


# =========================================================================
# API Endpoint Test
# =========================================================================

class ResearchTopicAPITest(TestCase):
    """Test the research_topic API endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='researcher', password='testpass')
        self.client.force_authenticate(user=self.user)

    @patch('research.researcher.ResearchOrchestrator.research_topic')
    def test_research_topic_endpoint(self, mock_research):
        """Test POST /api/resources/research_topic/"""
        mock_research.return_value = [
            {'type': 'youtube', 'title': 'Video 1', 'url': 'https://youtube.com/watch?v=x', 'text': 'content'},
        ]

        response = self.client.post('/api/resources/research_topic/', {'topic': 'Python'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['topic'], 'Python')
        self.assertEqual(response.data['resources_found'], 1)
        mock_research.assert_called_once_with('Python')

    def test_research_topic_requires_topic(self):
        """Test that missing topic returns 400."""
        response = self.client.post('/api/resources/research_topic/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_research_topic_requires_auth(self):
        """Test that unauthenticated requests are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/resources/research_topic/', {'topic': 'Python'})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


# =========================================================================
# Runner
# =========================================================================

def run_tests():
    import unittest
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    run_tests()
