# 🚀 Unified GitHub Release History

A Streamlit application for visualizing and comparing release timelines across multiple GitHub repositories. This tool helps developers and project managers track releases from multiple projects in a unified, color-coded timeline.

## ✨ Features

- **GitHub API Authentication**: Secure authentication using Personal Access Tokens
- **Multi-Repository Support**: Add and compare multiple repositories simultaneously
- **Color-Coded Timeline**: Each repository gets a unique color for easy identification
- **Date Range Filtering**: Focus on specific time periods
- **Interactive Visualization**: Hover for detailed release information
- **Public & Private Repos**: Support for both public and private repositories
- **Real-time Updates**: Add/remove repositories dynamically

## 🛠️ Setup

### Prerequisites

- Python 3.10 or higher (3.12 recommended)
- Poetry for dependency management
- GitHub Personal Access Token

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd fs-unified-release-history
   ```

2. **Install dependencies using Poetry**:
   ```bash
   poetry install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GitHub token
   ```

4. **Get a GitHub Personal Access Token**:
   - Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scopes:
     - `repo` (for private repositories)
     - `public_repo` (for public repositories only)
   - Copy the token and add it to your `.env` file

## 🚀 Usage

### Running the Application

```bash
# Activate the poetry environment
poetry shell

# Run the Streamlit app
streamlit run streamlit_app.py
```

The application will open in your browser at `http://localhost:8501`.

### Using the Application

1. **Authentication**:
   - Enter your GitHub Personal Access Token in the sidebar
   - The token can be loaded from the `.env` file or entered directly
   - Authentication status will be displayed

2. **Adding Repositories**:
   - Enter GitHub repository URLs in the format: `https://github.com/owner/repo`
   - Click "Add Repository" to fetch release data
   - Each repository will be assigned a unique color

3. **Managing Repositories**:
   - View all added repositories in the sidebar
   - Remove repositories using the delete button
   - See the number of releases for each repository

4. **Timeline Visualization**:
   - View the unified timeline in the main area
   - Each release is represented by a colored marker
   - Hover over markers for detailed information
   - Use the date range selector to filter releases

5. **Date Filtering**:
   - Set start and end dates in the sidebar
   - Timeline automatically updates to show releases in the selected range
   - Statistics are updated to reflect the filtered data

## 🏗️ Architecture

The application is structured using clean architecture principles:

- **`GitHubAPI`**: Handles all GitHub API interactions
- **`RepositoryManager`**: Manages repository list and color assignments
- **`ReleaseTimeline`**: Creates and manages timeline visualizations
- **`main()`**: Streamlit UI and application logic

## 📊 Features in Detail

### Timeline Visualization
- Interactive Plotly charts with zoom and pan capabilities
- Color-coded markers for each repository
- Annotations showing release tags
- Hover tooltips with detailed information

### Repository Management
- URL parsing and validation
- Automatic color assignment
- Release count tracking
- Easy add/remove functionality

### Date Range Filtering
- Flexible date selection
- Real-time timeline updates
- Statistics recalculation
- Default to last year of data

## 🔧 Development

### Project Structure
```
fs-unified-release-history/
├── src/
│   └── unified_release_history/
│       ├── __init__.py
│       └── app.py              # Main application
├── streamlit_app.py            # Entry point
├── pyproject.toml              # Poetry configuration
├── .env.example                # Environment template
└── README.md                   # This file
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Failed**:
   - Verify your GitHub token is correct
   - Check token permissions (repo/public_repo scope)
   - Ensure token hasn't expired

2. **Repository Not Found**:
   - Verify the repository URL format
   - Check if you have access to private repositories
   - Ensure the repository exists

3. **No Releases Found**:
   - Some repositories may not have any releases
   - Check if releases exist on GitHub
   - Verify date range settings

### Logging
The application uses Python's built-in logging module. Check the console output for detailed error messages and debugging information.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Links

- [Streamlit Documentation](https://docs.streamlit.io/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
