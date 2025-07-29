"""
Streamlit application for unified GitHub release history visualization.

This application allows users to:
1. Authenticate with GitHub API using a personal access token
2. Add multiple repositories for comparison
3. View a unified timeline of releases with color coding
4. Filter releases by date range
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitHubAPI:
    """GitHub API client for fetching release data."""

    def __init__(self, token: str):
        """Initialize GitHub API client with authentication token."""
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        logger.info("GitHub API client initialized")

    def test_authentication(self) -> bool:
        """Test if the provided token is valid."""
        try:
            response = requests.get(
                f'{self.base_url}/user',
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("GitHub authentication successful")
                return True
            else:
                logger.warning(f"GitHub authentication failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"GitHub authentication error: {e}")
            return False

    def check_repository_access(self, owner: str, repo: str) -> Tuple[bool, str]:
        """Check if repository exists and is accessible."""
        try:
            url = f'{self.base_url}/repos/{owner}/{repo}'
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return True, "Repository accessible"
            elif response.status_code == 404:
                return False, "Repository not found or private (no access)"
            elif response.status_code == 403:
                return False, "Access forbidden - check token permissions"
            else:
                return False, f"HTTP {response.status_code}: {response.reason}"
        except requests.RequestException as e:
            return False, f"Network error: {e}"

    def get_releases(self, owner: str, repo: str) -> Tuple[List[Dict], str]:
        """Fetch releases for a given repository. Returns (releases, error_message)."""
        try:
            url = f'{self.base_url}/repos/{owner}/{repo}/releases'
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                releases = response.json()
                logger.info(f"Fetched {len(releases)} releases for {owner}/{repo}")
                return releases, ""
            elif response.status_code == 404:
                # Check if it's a repository access issue
                repo_accessible, repo_msg = self.check_repository_access(owner, repo)
                if not repo_accessible:
                    error_msg = f"Cannot access repository: {repo_msg}"
                    logger.warning(f"Repository {owner}/{repo} - {error_msg}")
                    return [], error_msg
                else:
                    # Repository exists but no releases
                    logger.info(f"Repository {owner}/{repo} has no releases")
                    return [], "Repository exists but has no releases"
            elif response.status_code == 403:
                error_msg = "Access forbidden - check your token permissions"
                logger.error(f"Failed to fetch releases for {owner}/{repo}: {error_msg}")
                return [], error_msg
            else:
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                logger.error(f"Failed to fetch releases for {owner}/{repo}: {error_msg}")
                return [], error_msg
        except requests.RequestException as e:
            error_msg = f"Network error: {e}"
            logger.error(f"Error fetching releases for {owner}/{repo}: {error_msg}")
            return [], error_msg


class RepositoryManager:
    """Manages repository list and color assignments."""

    def __init__(self):
        """Initialize repository manager."""
        self.colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D2B4DE'
        ]
        logger.info("Repository manager initialized")

    def parse_github_url(self, url: str) -> Optional[Tuple[str, str]]:
        """Parse GitHub URL to extract owner and repository name."""
        try:
            parsed = urlparse(url.strip())
            if parsed.netloc != 'github.com':
                return None

            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                # Remove .git suffix if present
                if repo.endswith('.git'):
                    repo = repo[:-4]
                logger.info(f"Parsed GitHub URL: {owner}/{repo}")
                return owner, repo
            return None
        except Exception as e:
            logger.error(f"Error parsing GitHub URL {url}: {e}")
            return None

    def get_color_for_repo(self, repo_key: str, repo_index: int) -> str:
        """Get a unique color for a repository."""
        color = self.colors[repo_index % len(self.colors)]
        logger.debug(f"Assigned color {color} to repository {repo_key}")
        return color


class ReleaseTimeline:
    """Handles release timeline visualization with a vertical scrollable design."""

    def __init__(self):
        """Initialize release timeline."""
        logger.info("Release timeline initialized")

    def create_timeline(self, releases_data: Dict, start_date: datetime, end_date: datetime) -> None:
        """Create a unified vertical timeline visualization of releases."""
        all_releases = []

        # Collect all releases with metadata
        for repo_key, data in releases_data.items():
            releases = data['releases']
            color = data['color']

            for release in releases:
                try:
                    # Skip releases without published_at (drafts, etc.)
                    if not release.get('published_at'):
                        continue
                    published_at = datetime.fromisoformat(
                        release['published_at'].replace('Z', '+00:00')
                    )

                    # Filter by date range
                    if start_date <= published_at.date() <= end_date:
                        all_releases.append({
                            'repo': repo_key,
                            'tag': release['tag_name'],
                            'date': published_at,
                            'color': color,
                            'name': release.get('name', release['tag_name']),
                            'url': release['html_url'],
                            'body': release.get('body', '').strip()[:200] + ('...' if len(release.get('body', '')) > 200 else '')
                        })
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing release data: {e}")
                    continue

        # Sort releases by date (newest first for message-thread feel)
        all_releases.sort(key=lambda x: x['date'], reverse=True)

        if not all_releases:
            logger.info("No releases found in the specified date range")
            st.info("📅 No releases found in the selected date range")
            return

        # Create vertical timeline using Streamlit components
        st.markdown("### 🚀 Release Timeline")
        st.markdown(f"**{len(all_releases)} releases** from **{len(set(r['repo'] for r in all_releases))} repositories**")

        # Create a scrollable container
        timeline_container = st.container()

        with timeline_container:
            # Add custom CSS for timeline styling
            st.markdown("""
            <style>
            .timeline-item {
                border-left: 3px solid #ddd;
                padding-left: 20px;
                margin-bottom: 20px;
                position: relative;
            }
            .timeline-dot {
                position: absolute;
                left: -8px;
                top: 8px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 0 0 2px #ddd;
            }
            .timeline-content {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                border: 1px solid #e9ecef;
            }
            .repo-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                color: white;
                margin-bottom: 8px;
            }
            .release-tag {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .release-date {
                color: #6c757d;
                font-size: 14px;
                margin-bottom: 10px;
            }
            .release-body {
                color: #495057;
                font-size: 14px;
                line-height: 1.4;
            }
            </style>
            """, unsafe_allow_html=True)

            # Display each release as a timeline item
            for i, release in enumerate(all_releases):
                # Create timeline item HTML
                timeline_html = f"""
                <div class="timeline-item">
                    <div class="timeline-dot" style="background-color: {release['color']};"></div>
                    <div class="timeline-content">
                        <div class="repo-badge" style="background-color: {release['color']};">
                            {release['repo']}
                        </div>
                        <div class="release-tag">{release['tag']}</div>
                        <div class="release-date">
                            📅 {release['date'].strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                        {f'<div class="release-body">{release["body"]}</div>' if release['body'] else ''}
                    </div>
                </div>
                """

                # Display the timeline item
                st.markdown(timeline_html, unsafe_allow_html=True)

                # Add a link to the GitHub release
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    st.markdown(f"[🔗 View Release]({release['url']})")
                with col2:
                    if release['name'] != release['tag']:
                        st.caption(f"*{release['name']}*")

                # Add separator between items (except for the last one)
                if i < len(all_releases) - 1:
                    st.markdown("---")

        logger.info(f"Created timeline with {len(all_releases)} releases from {len(set(r['repo'] for r in all_releases))} repositories")


def setup_streamlit_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="GitHub Release Timeline",
        page_icon="📊",
        layout="wide"
    )


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'repositories' not in st.session_state:
        st.session_state.repositories = {}
    if 'github_api' not in st.session_state:
        st.session_state.github_api = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False


def render_authentication_section(repo_manager):
    """Render GitHub authentication section in sidebar."""
    st.subheader("🔐 GitHub Authentication")

    # Try to load token from environment first
    default_token = os.getenv('GITHUB_TOKEN', '')

    github_token = st.text_input(
        "GitHub Personal Access Token",
        value=default_token,
        type="password",
        help="Enter your GitHub PAT to access private repositories"
    )

    if github_token and not st.session_state.authenticated:
        api = GitHubAPI(github_token)
        if api.test_authentication():
            st.session_state.github_api = api
            st.session_state.authenticated = True
            st.success("✅ Authentication successful!")
            logger.info("User authenticated successfully")
        else:
            st.error("❌ Authentication failed. Please check your token.")
            st.session_state.authenticated = False

    if st.session_state.authenticated:
        st.success("🔓 Authenticated")


def render_repository_management(repo_manager):
    """Render repository management section in sidebar."""
    st.subheader("📚 Repository Management")

    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repo",
        help="Enter the full GitHub repository URL"
    )

    if st.button("➕ Add Repository") and repo_url and st.session_state.authenticated:
        parsed = repo_manager.parse_github_url(repo_url)
        if parsed:
            owner, repo = parsed
            repo_key = f"{owner}/{repo}"

            if repo_key not in st.session_state.repositories:
                with st.spinner(f"Fetching releases for {repo_key}..."):
                    releases, error_msg = st.session_state.github_api.get_releases(owner, repo)

                    if releases:
                        color = repo_manager.get_color_for_repo(
                            repo_key, len(st.session_state.repositories)
                        )
                        st.session_state.repositories[repo_key] = {
                            'releases': releases,
                            'color': color
                        }
                        st.success(f"✅ Added {repo_key} ({len(releases)} releases)")
                        logger.info(f"Added repository {repo_key} with {len(releases)} releases")
                    else:
                        if error_msg:
                            st.error(f"❌ {error_msg} for {repo_key}")
                            logger.warning(f"Failed to fetch releases for {repo_key}: {error_msg}")
                        else:
                            st.error(f"❌ No releases found for {repo_key}")
                            logger.warning(f"No releases found for {repo_key}")
            else:
                st.warning(f"⚠️ {repo_key} is already added")
        else:
            st.error("❌ Invalid GitHub URL format")

    # Display added repositories
    if st.session_state.repositories:
        st.subheader("📋 Added Repositories")
        for repo_key, data in st.session_state.repositories.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f'<span style="color: {data["color"]}">●</span> {repo_key} '
                    f'({len(data["releases"])} releases)',
                    unsafe_allow_html=True
                )
            with col2:
                if st.button("🗑️", key=f"remove_{repo_key}"):
                    del st.session_state.repositories[repo_key]
                    st.rerun()


def render_date_range_selector():
    """Render date range selector in sidebar."""
    st.subheader("📅 Date Range")

    # Default to last year
    default_end = datetime.now().date()
    default_start = default_end - timedelta(days=365)

    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)

    if start_date > end_date:
        st.error("❌ Start date must be before end date")

    return start_date, end_date


def render_main_content(timeline, start_date, end_date):
    """Render main content area."""
    if not st.session_state.authenticated:
        st.info("🔐 Please authenticate with GitHub to get started.")
        st.markdown("""
        ### How to get a GitHub Personal Access Token:
        1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
        2. Click "Generate new token (classic)"
        3. Select scopes: `repo` (for private repos) or `public_repo` (for public repos only)
        4. Copy the generated token and paste it above
        """)

    elif not st.session_state.repositories:
        st.info("📚 Add some repositories to see their release timeline.")
        st.markdown("""
        ### Getting Started:
        1. ✅ You're authenticated with GitHub
        2. 📝 Add repository URLs in the sidebar
        3. 📊 View the unified timeline below
        4. 🎯 Use date filters to focus on specific periods
        """)

    else:
        # Display statistics first
        if start_date <= end_date:
            # Release statistics
            total_releases = sum(
                len(data['releases']) for data in st.session_state.repositories.values()
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Repositories", len(st.session_state.repositories))
            with col2:
                st.metric("Total Releases", total_releases)
            with col3:
                # Count releases in date range
                releases_in_range = 0
                for data in st.session_state.repositories.values():
                    for release in data['releases']:
                        try:
                            # Skip releases without published_at (drafts, etc.)
                            if not release.get('published_at'):
                                continue
                            published_at = datetime.fromisoformat(
                                release['published_at'].replace('Z', '+00:00')
                            ).date()
                            if start_date <= published_at <= end_date:
                                releases_in_range += 1
                        except (ValueError, KeyError):
                            continue
                st.metric("Releases in Range", releases_in_range)

            # Display timeline
            timeline.create_timeline(
                st.session_state.repositories,
                start_date,
                end_date
            )


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="GitHub Release Timeline",
        page_icon="📊",
        layout="wide"
    )

    st.title("🚀 Unified GitHub Release History")
    st.markdown("Visualize and compare release timelines across multiple GitHub repositories")

    # Initialize session state
    if 'repositories' not in st.session_state:
        st.session_state.repositories = {}
    if 'github_api' not in st.session_state:
        st.session_state.github_api = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Initialize managers
    repo_manager = RepositoryManager()
    timeline = ReleaseTimeline()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # GitHub Authentication
        st.subheader("🔐 GitHub Authentication")

        # Try to load token from environment first
        default_token = os.getenv('GITHUB_TOKEN', '')

        github_token = st.text_input(
            "GitHub Personal Access Token",
            value=default_token,
            type="password",
            help="Enter your GitHub PAT to access private repositories"
        )

        if github_token and not st.session_state.authenticated:
            api = GitHubAPI(github_token)
            if api.test_authentication():
                st.session_state.github_api = api
                st.session_state.authenticated = True
                st.success("✅ Authentication successful!")
                logger.info("User authenticated successfully")
            else:
                st.error("❌ Authentication failed. Please check your token.")
                st.session_state.authenticated = False

        if st.session_state.authenticated:
            st.success("🔓 Authenticated")

        # Repository Management
        st.subheader("📚 Repository Management")

        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/owner/repo",
            help="Enter the full GitHub repository URL"
        )

        if st.button("➕ Add Repository") and repo_url and st.session_state.authenticated:
            parsed = repo_manager.parse_github_url(repo_url)
            if parsed:
                owner, repo = parsed
                repo_key = f"{owner}/{repo}"

                if repo_key not in st.session_state.repositories:
                    with st.spinner(f"Fetching releases for {repo_key}..."):
                        releases, error_msg = st.session_state.github_api.get_releases(owner, repo)

                        if releases:
                            color = repo_manager.get_color_for_repo(
                                repo_key, len(st.session_state.repositories)
                            )
                            st.session_state.repositories[repo_key] = {
                                'releases': releases,
                                'color': color
                            }
                            st.success(f"✅ Added {repo_key} ({len(releases)} releases)")
                            logger.info(f"Added repository {repo_key} with {len(releases)} releases")
                        else:
                            if error_msg:
                                st.error(f"❌ {error_msg} for {repo_key}")
                                logger.warning(f"Failed to fetch releases for {repo_key}: {error_msg}")
                            else:
                                st.error(f"❌ No releases found for {repo_key}")
                                logger.warning(f"No releases found for {repo_key}")
                else:
                    st.warning(f"⚠️ {repo_key} is already added")
            else:
                st.error("❌ Invalid GitHub URL format")

        # Display added repositories
        if st.session_state.repositories:
            st.subheader("📋 Added Repositories")
            for repo_key, data in st.session_state.repositories.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(
                        f'<span style="color: {data["color"]}">●</span> {repo_key} '
                        f'({len(data["releases"])} releases)',
                        unsafe_allow_html=True
                    )
                with col2:
                    if st.button("🗑️", key=f"remove_{repo_key}"):
                        del st.session_state.repositories[repo_key]
                        st.rerun()

        # Date Range Selector
        st.subheader("📅 Date Range")

        # Default to last year
        default_end = datetime.now().date()
        default_start = default_end - timedelta(days=365)

        start_date = st.date_input("Start Date", value=default_start)
        end_date = st.date_input("End Date", value=default_end)

        if start_date > end_date:
            st.error("❌ Start date must be before end date")

    # Main content area
    if not st.session_state.authenticated:
        st.info("🔐 Please authenticate with GitHub to get started.")
        st.markdown("""
        ### How to get a GitHub Personal Access Token:
        1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
        2. Click "Generate new token (classic)"
        3. Select scopes: `repo` (for private repos) or `public_repo` (for public repos only)
        4. Copy the generated token and paste it above
        """)

    elif not st.session_state.repositories:
        st.info("📚 Add some repositories to see their release timeline.")
        st.markdown("""
        ### Getting Started:
        1. ✅ You're authenticated with GitHub
        2. 📝 Add repository URLs in the sidebar
        3. 📊 View the unified timeline below
        4. 🎯 Use date filters to focus on specific periods
        """)

    else:
        # Display statistics first
        if start_date <= end_date:
            # Release statistics
            total_releases = sum(
                len(data['releases']) for data in st.session_state.repositories.values()
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Repositories", len(st.session_state.repositories))
            with col2:
                st.metric("Total Releases", total_releases)
            with col3:
                # Count releases in date range
                releases_in_range = 0
                for data in st.session_state.repositories.values():
                    for release in data['releases']:
                        try:
                            # Skip releases without published_at (drafts, etc.)
                            if not release.get('published_at'):
                                continue
                            published_at = datetime.fromisoformat(
                                release['published_at'].replace('Z', '+00:00')
                            ).date()
                            if start_date <= published_at <= end_date:
                                releases_in_range += 1
                        except (ValueError, KeyError):
                            continue
                st.metric("Releases in Range", releases_in_range)

            # Display timeline
            timeline.create_timeline(
                st.session_state.repositories,
                start_date,
                end_date
            )


if __name__ == "__main__":
    main()
