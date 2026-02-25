import logging
import re
import requests
from urllib.parse import urlparse, parse_qs, urlencode
from django.conf import settings
from .models import Resource, ResourceChunk
from .services import VectorStoreService
from ai_engine.services import EmbeddingService

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_REQUEST_TIMEOUT = int(getattr(settings, 'AI_ENGINE', {}).get('DOC_REQUEST_TIMEOUT', 10))


class ResearchOrchestrator:
    """
    Coordinates research activities for a given topic.
    """
    @staticmethod
    def research_topic(topic):
        """
        Research a topic using YouTube and Documentation.
        Stores results and updates vector index.
        """
        logger.info(f"Starting research for topic: {topic}")

        resources = []

        # 1. YouTube Research
        yt_resources = YouTubeResearcher.search(topic)
        resources.extend(yt_resources)

        # 2. Documentation Research
        doc_resources = DocResearcher.search(topic)
        resources.extend(doc_resources)

        # 3. Process and Index
        for res_data in resources:
            try:
                # Create Resource object
                resource, created = Resource.objects.get_or_create(
                    url=res_data['url'],
                    defaults={
                        'resource_type': res_data['type'],
                        'title': res_data['title'],
                        'description': res_data.get('description', ''),
                        'transcript_text': res_data.get('text', ''),
                        'metadata': res_data.get('metadata', {})
                    }
                )

                if created or not resource.chunks.exists():
                    # Chunk and Embed
                    ResearchOrchestrator.index_resource(resource)

            except Exception as e:
                logger.error(f"Failed to process resource {res_data.get('url')}: {e}")

        logger.info(f"Research complete for '{topic}': {len(resources)} resources found")
        return resources

    @staticmethod
    def index_resource(resource):
        """Chunks a resource and adds it to the vector store."""
        text = resource.transcript_text or resource.description
        if not text:
            return

        chunks = EmbeddingService.chunk_text(text)
        chunk_objects = []
        texts_to_embed = []
        metadatas = []

        for i, chunk_text in enumerate(chunks):
            chunk = ResourceChunk.objects.create(
                resource=resource,
                chunk_text=chunk_text,
                chunk_index=i,
                token_count=len(chunk_text.split())  # Rough estimate
            )
            chunk_objects.append(chunk)
            texts_to_embed.append(chunk_text)
            metadatas.append({'chunk_id': chunk.id})

        # Add to FAISS
        VectorStoreService.add_texts(texts_to_embed, metadatas)
        logger.info(f"Indexed {len(chunk_objects)} chunks for resource: {resource.title}")


# ==========================================================================
# YouTube Researcher
# ==========================================================================

class YouTubeResearcher:
    """
    Searches YouTube for educational videos and fetches their transcripts.

    Strategy:
    1. If YOUTUBE_API_KEY is configured → use YouTube Data API v3
    2. Otherwise → fallback to DuckDuckGo site:youtube.com search
    3. Fetch transcript for each video via youtube-transcript-api
    4. Skip videos with no transcript (they add no value for RAG)
    """

    # Preferred educational channels — boost these in results
    _PREFERRED_CHANNELS = {
        '3blue1brown', 'sentdex', 'corey schafer', 'traversy media',
        'fireship', 'tech with tim', 'freecodecamp', 'cs dojo',
        'the coding train', 'computerphile', 'mit opencourseware',
        'khan academy', 'programming with mosh', 'net ninja',
        'web dev simplified', 'academind', 'hussein nasser',
    }

    @staticmethod
    def search(topic, limit=None):
        """
        Search YouTube for videos on the given topic and return resource dicts.

        Returns:
            list[dict]: Each dict has keys: type, title, url, description, text, metadata
        """
        if limit is None:
            limit = int(settings.AI_ENGINE.get('YOUTUBE_MAX_RESULTS', 5))

        logger.info(f"Searching YouTube for: {topic}")

        api_key = settings.AI_ENGINE.get('YOUTUBE_API_KEY', '')
        if api_key:
            videos = YouTubeResearcher._search_youtube_api(topic, limit, api_key)
        else:
            logger.info("No YOUTUBE_API_KEY configured, using fallback search")
            videos = YouTubeResearcher._search_youtube_fallback(topic, limit)

        # Fetch transcripts for each video, only keep those with transcripts
        results = []
        for video in videos:
            video_id = YouTubeResearcher._extract_video_id(video['url'])
            if not video_id:
                continue

            transcript = YouTubeResearcher._fetch_transcript(video_id)

            # Skip videos without transcripts — no value for RAG
            if not transcript or len(transcript) < 100:
                logger.info(f"Skipping video (no/short transcript): {video.get('title', '')[:60]}")
                continue

            video['text'] = transcript
            video['type'] = 'youtube'
            results.append(video)

            # Stop once we have enough quality results
            if len(results) >= limit:
                break

        logger.info(f"YouTube: found {len(results)} videos with transcripts for '{topic}'")
        return results

    @staticmethod
    def _search_youtube_api(topic, limit, api_key):
        """
        Search YouTube via the Data API v3.
        Uses better queries to find educational content.
        """
        try:
            from googleapiclient.discovery import build

            youtube = build('youtube', 'v3', developerKey=api_key)

            # Search with multiple targeted queries to get diverse results
            queries = [
                f"{topic} tutorial explained",
                f"{topic} complete guide course",
            ]

            all_videos = []
            seen_ids = set()

            for query in queries:
                if len(all_videos) >= limit * 2:
                    break

                request = youtube.search().list(
                    q=query,
                    part='snippet',
                    type='video',
                    maxResults=limit,
                    order='relevance',
                    videoDuration='medium',  # 4-20 min, skips shorts and very long
                    relevanceLanguage='en',
                )
                response = request.execute()

                for item in response.get('items', []):
                    snippet = item['snippet']
                    video_id = item['id']['videoId']

                    if video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)

                    channel = snippet.get('channelTitle', '')
                    # Score: boost preferred channels
                    is_preferred = any(
                        pref in channel.lower()
                        for pref in YouTubeResearcher._PREFERRED_CHANNELS
                    )

                    all_videos.append({
                        'title': snippet.get('title', ''),
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'description': snippet.get('description', ''),
                        'metadata': {
                            'channel': channel,
                            'published_at': snippet.get('publishedAt', ''),
                            'source': 'youtube_api',
                            'preferred_channel': is_preferred,
                        },
                        '_score': 10 if is_preferred else 0,
                    })

            # Sort: preferred channels first
            all_videos.sort(key=lambda v: v.get('_score', 0), reverse=True)
            return all_videos[:limit * 2]  # Return extra, transcript check will filter

        except Exception as e:
            logger.error(f"YouTube API search failed: {e}")
            return YouTubeResearcher._search_youtube_fallback(topic, limit)

    @staticmethod
    def _search_youtube_fallback(topic, limit):
        """
        Fallback: search DuckDuckGo for YouTube videos.
        Uses targeted search queries for better educational content.
        """
        try:
            # Use more specific query for educational content
            query = f"site:youtube.com {topic} tutorial explained full course"
            url = "https://html.duckduckgo.com/html/"
            resp = requests.post(
                url,
                data={'q': query},
                headers={'User-Agent': _USER_AGENT},
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')

            videos = []
            for result in soup.select('.result__a'):
                href = result.get('href', '')
                title = result.get_text(strip=True)

                # DuckDuckGo wraps URLs — extract the actual URL
                actual_url = YouTubeResearcher._extract_ddg_url(href)
                if not actual_url:
                    continue

                # Only keep youtube.com watch URLs (skip shorts, playlists)
                if 'youtube.com/watch' not in actual_url:
                    continue

                # Skip obvious non-educational content
                title_lower = title.lower()
                skip_keywords = ['reaction', 'prank', 'vlog', 'unboxing', 'asmr', 'shorts']
                if any(kw in title_lower for kw in skip_keywords):
                    continue

                videos.append({
                    'title': title,
                    'url': actual_url,
                    'description': '',
                    'metadata': {'source': 'duckduckgo_fallback'}
                })

                # Fetch extra to account for transcript filtering
                if len(videos) >= limit * 2:
                    break

            return videos

        except Exception as e:
            logger.error(f"YouTube fallback search failed: {e}")
            return []

    @staticmethod
    def _fetch_transcript(video_id):
        """
        Fetch transcript text for a YouTube video.

        Uses youtube-transcript-api. Falls back gracefully if unavailable.
        Returns: transcript string or empty string.
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
            except Exception:
                # Fall back to any available transcript, translated to English
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except Exception:
                    # Get first available and translate
                    for t in transcript_list:
                        try:
                            transcript = t.translate('en')
                            break
                        except Exception:
                            transcript = t
                            break
                    else:
                        return ""

            fetched = transcript.fetch()
            # Concatenate all text segments
            text_parts = [entry.text for entry in fetched]
            full_text = " ".join(text_parts)
            logger.info(f"Fetched transcript for {video_id}: {len(full_text)} chars")
            return full_text

        except Exception as e:
            logger.warning(f"Could not fetch transcript for video {video_id}: {e}")
            return ""

    @staticmethod
    def _extract_video_id(url):
        """Extract YouTube video ID from various URL formats."""
        try:
            parsed = urlparse(url)

            # Standard: youtube.com/watch?v=ID
            if 'youtube.com' in parsed.hostname:
                qs = parse_qs(parsed.query)
                return qs.get('v', [None])[0]

            # Short: youtu.be/ID
            if parsed.hostname == 'youtu.be':
                return parsed.path.lstrip('/')

        except Exception:
            pass

        # Regex fallback
        match = re.search(r'(?:v=|youtu\.be/)([\w-]{11})', url)
        return match.group(1) if match else None

    @staticmethod
    def _extract_ddg_url(href):
        """Extract the actual URL from a DuckDuckGo redirect link."""
        try:
            parsed = urlparse(href)
            qs = parse_qs(parsed.query)
            # DuckDuckGo wraps URLs in uddg= parameter
            actual = qs.get('uddg', [None])[0]
            return actual
        except Exception:
            return href


# ==========================================================================
# Documentation Researcher
# ==========================================================================

class DocResearcher:
    """
    Searches the web for documentation and articles, then extracts text content.

    Uses DuckDuckGo HTML search (no API key required) + BeautifulSoup for extraction.
    Prioritizes high-quality documentation domains and deduplicates by domain.
    """

    # Domains to skip (not useful documentation sources)
    _SKIP_DOMAINS = {
        'youtube.com', 'youtu.be', 'facebook.com', 'twitter.com', 'x.com',
        'instagram.com', 'tiktok.com', 'reddit.com', 'pinterest.com',
        'linkedin.com', 'amazon.com', 'ebay.com', 'quora.com',
        'stackoverflow.com',  # Often has Q&A, not structured docs
    }

    # High-quality documentation domains — prefer these
    _PREFERRED_DOMAINS = {
        'docs.python.org', 'developer.mozilla.org', 'realpython.com',
        'docs.djangoproject.com', 'reactjs.org', 'react.dev',
        'vuejs.org', 'angular.io', 'nodejs.org',
        'docs.microsoft.com', 'learn.microsoft.com',
        'cloud.google.com', 'aws.amazon.com/docs',
        'kubernetes.io', 'docs.docker.com',
        'pytorch.org', 'tensorflow.org', 'scikit-learn.org',
        'pandas.pydata.org', 'numpy.org',
        'en.wikipedia.org', 'geeksforgeeks.org',
        'tutorialspoint.com', 'w3schools.com',
        'freecodecamp.org', 'digitalocean.com',
        'medium.com', 'dev.to', 'towardsdatascience.com',
        'javatpoint.com', 'baeldung.com',
        'docs.oracle.com', 'docs.swift.org',
        'rust-lang.org', 'go.dev',
    }

    @staticmethod
    def search(topic, limit=None):
        """
        Search for documentation/articles on the given topic.
        Uses multiple queries, deduplicates by domain, and prefers quality sources.
        """
        if limit is None:
            limit = int(settings.AI_ENGINE.get('DOC_MAX_RESULTS', 5))

        logger.info(f"Searching documentation for: {topic}")

        # Use multiple targeted search queries for better coverage
        queries = [
            f'"{topic}" documentation tutorial guide',
            f'{topic} official docs getting started',
            f'{topic} comprehensive guide explained',
        ]

        all_search_results = []
        seen_urls = set()

        for query in queries:
            search_results = DocResearcher._search_duckduckgo(query, limit * 2)
            for sr in search_results:
                url = sr['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_search_results.append(sr)

        # Score and sort by domain quality
        scored_results = []
        for sr in all_search_results:
            url = sr['url']
            hostname = urlparse(url).hostname or ''
            score = 0

            # Boost preferred domains
            for domain in DocResearcher._PREFERRED_DOMAINS:
                if domain in hostname:
                    score += 10
                    break

            # Boost URLs containing doc-related path segments
            path_lower = urlparse(url).path.lower()
            if any(kw in path_lower for kw in ['/docs/', '/guide/', '/tutorial/', '/learn/']):
                score += 5

            # Boost if title contains educational keywords
            title_lower = sr.get('title', '').lower()
            if any(kw in title_lower for kw in ['documentation', 'guide', 'tutorial', 'introduction', 'getting started']):
                score += 3

            sr['_score'] = score
            scored_results.append(sr)

        # Sort by score descending
        scored_results.sort(key=lambda x: x['_score'], reverse=True)

        # Fetch content with domain deduplication
        results = []
        seen_domains = set()

        for sr in scored_results:
            if len(results) >= limit:
                break

            url = sr['url']
            if not DocResearcher._is_valid_doc_url(url):
                continue

            # Deduplicate by domain: max 2 pages per domain
            hostname = urlparse(url).hostname or ''
            domain_key = '.'.join(hostname.split('.')[-2:])  # e.g., 'realpython.com'
            domain_count = sum(1 for d in seen_domains if d == domain_key)
            if domain_count >= 2:
                continue

            # Fetch and extract page content
            text = DocResearcher._fetch_page_content(url)
            if not text or len(text) < 200:  # Raised minimum from 100 to 200
                continue

            # Truncate very long pages (keep first ~5000 words)
            words = text.split()
            if len(words) > 5000:
                text = " ".join(words[:5000])

            seen_domains.add(domain_key)
            results.append({
                'type': 'documentation',
                'title': sr.get('title', ''),
                'url': url,
                'description': sr.get('snippet', '')[:500],
                'text': text,
                'metadata': {
                    'source': 'web_search',
                    'domain': hostname,
                    'quality_score': sr.get('_score', 0),
                }
            })

        logger.info(f"Docs: found {len(results)} quality documentation pages for '{topic}'")
        return results

    @staticmethod
    def _search_duckduckgo(query, limit):
        """
        Search DuckDuckGo HTML version and parse results.

        Returns: list of dicts with keys: title, url, snippet
        """
        try:
            url = "https://html.duckduckgo.com/html/"
            resp = requests.post(
                url,
                data={'q': query},
                headers={'User-Agent': _USER_AGENT},
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')

            results = []
            for result in soup.select('.result'):
                link_el = result.select_one('.result__a')
                snippet_el = result.select_one('.result__snippet')

                if not link_el:
                    continue

                href = link_el.get('href', '')
                actual_url = DocResearcher._extract_ddg_url(href)
                if not actual_url:
                    continue

                title = link_el.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ''

                results.append({
                    'title': title,
                    'url': actual_url,
                    'snippet': snippet,
                })

                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    @staticmethod
    def _fetch_page_content(url):
        """
        Fetch a web page and extract its main text content.

        Returns: cleaned text string or empty string on failure.
        """
        try:
            resp = requests.get(
                url,
                headers={'User-Agent': _USER_AGENT},
                timeout=_REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            resp.raise_for_status()

            # Only process HTML content
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                return ""

            return DocResearcher._extract_text(resp.text)

        except Exception as e:
            logger.warning(f"Failed to fetch page {url}: {e}")
            return ""

    @staticmethod
    def _extract_text(html):
        """
        Extract clean article text from HTML using BeautifulSoup.

        Prioritizes <article>, <main>, [role="main"] content areas.
        Strips navigation, footers, scripts, ads, and other non-content elements.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # Remove non-content elements
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header',
                                   'aside', 'form', 'iframe', 'noscript',
                                   'svg', 'button', 'select', 'input']):
            tag.decompose()

        # Remove common non-content classes/ids
        for selector in ['.sidebar', '.nav', '.menu', '.footer', '.header',
                         '.advertisement', '.ad', '.cookie', '.popup',
                         '.comments', '.comment', '.social', '.share',
                         '.breadcrumb', '.pagination', '.related',
                         '#sidebar', '#nav', '#menu', '#footer', '#header',
                         '#cookie-banner', '#cookie-consent', '#comments']:
            for el in soup.select(selector):
                el.decompose()

        # Try to find the main content area first (priority order)
        main_content = (
            soup.find('article') or
            soup.find('main') or
            soup.find('div', {'role': 'main'}) or
            soup.find('div', class_=re.compile(r'content|article|post|entry|documentation|tutorial', re.I)) or
            soup.find('body')
        )

        if not main_content:
            return ""

        # Get text, collapse whitespace
        text = main_content.get_text(separator='\n')

        # Clean up: collapse multiple newlines and whitespace
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and len(line) > 3:  # Skip very short lines (likely UI artifacts)
                lines.append(line)

        return '\n'.join(lines)

    @staticmethod
    def _is_valid_doc_url(url):
        """Check if URL is a valid documentation/article source."""
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or '').lower()

            # Skip known non-doc domains
            for skip in DocResearcher._SKIP_DOMAINS:
                if skip in hostname:
                    return False

            # Skip non-HTTP(S) URLs
            if parsed.scheme not in ('http', 'https'):
                return False

            return True
        except Exception:
            return False

    @staticmethod
    def _extract_ddg_url(href):
        """Extract the actual URL from a DuckDuckGo redirect link."""
        try:
            parsed = urlparse(href)
            qs = parse_qs(parsed.query)
            actual = qs.get('uddg', [None])[0]
            return actual
        except Exception:
            return href
