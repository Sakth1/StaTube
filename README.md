<div id="top">

<div align="center" style="position: relative; width: 100%; height: 100%; ">

<img src="./assets/StaTube_banner.png" width="0%" style="position: absolute; top: 0; right: 0;" alt="StaTube banner"/>

# STATUBE

<em>A desktop GUI application to fetch, view, and analyze video transcriptions and comments from YouTube.</em>

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/badge/PySide6-required-orange.svg)](https://pypi.org/project/PySide6/)

<em>Built with the tools and technologies:</em>

<p>
  <img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-83CD29.svg?style=flat-square&logo=Qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/SQLite-003B57.svg?style=flat-square&logo=SQLite&logoColor=white" alt="SQLite">
  
  <img src="https://img.shields.io/badge/NLTK-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="NLTK">
  <img src="https://img.shields.io/badge/WordCloud-FF9900.svg?style=flat-square&logo=python&logoColor=white" alt="WordCloud">
  
  <img src="https://img.shields.io/badge/yt--dlp-c4302b.svg?style=flat-square&logo=youtube&logoColor=white" alt="yt-dlp">
  <img src="https://img.shields.io/badge/scrapetube-FF0000.svg?style=flat-square&logo=youtube&logoColor=white" alt="scrapetube">

  <img src="https://img.shields.io/badge/Nuitka-0065a9.svg?style=flat-square&logo=python&logoColor=white" alt="Nuitka">
  <img src="https://img.shields.io/badge/Inno%20Setup-265699.svg?style=flat-square&logo=windows&logoColor=white" alt="Inno Setup">
  <img src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat-square&logo=GitHub-Actions&logoColor=white" alt="GitHub Actions">
</p>

</div>
<br clear="right">

---

## ☀️ Table of Contents

- [☀️ Table of Contents](#-table-of-contents)
- [🌞 Overview](#-overview)
- [🔥 Features](#-features)
- [🌅 Project Structure](#-project-structure)
    - [🌄 Project Index](#-project-index)
- [🚀 Getting Started](#-getting-started)
    - [🌟 Prerequisites](#-prerequisites)
    - [⚡ Installation](#-installation)
    - [🔆 Usage](#-usage)
    - [📦 Building the Installer](#-building-the-installer)
- [🌻 Roadmap](#-roadmap)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [✨ Acknowledgments](#-acknowledgments)

---

## 🌞 Overview

**StaTube** is a desktop GUI application built with **Python** and **PySide6**. It allows users to fetch, view, and analyze video transcriptions and comments from any YouTube channel without loggining in and not using any API keys. 

The application utilizes a local architecture where data is scraped from YouTube and persisted into a local **SQLite database** (defined in `Data/schema.sql`). This allows for batch operations, offline viewing of fetched transcripts, and data storing capabilities.

---

## 🔥 Features

- 🆓 **No Credentials Needed**: Use the application immediately—no registration, login, or API key is required.
- 🎯 **Channel Scraping**: Fetch the list of videos from any specific YouTube channel.
- 📄 **Transcription Retrieval**: Retrieve and display video transcriptions (if available).
- 💬 **Comment Analysis**: Fetch and display user comments for specific videos.
- 🧰 **Modern GUI**: A responsive desktop interface built with PySide6.
- 🔄 **Batch Operations**: Support for processing multiple videos.
- 📁 **Analysis Export**: Export transcript and comment analysis image.
- 💾 **Local Database**: All data is structured and stored locally using SQLite.

---

## 🌅 Project Structure

```sh
└── StaTube/
    ├── .github
    │   ├── dependabot.yml
    │   └── workflows
    │   	├── build-release.yml
    │   	└── python-package.yml
    ├── Analysis
    │   ├── __init__.py
    │   ├── SentimentAnalysis.py
    │   └── WordCloud.py
    ├── assets
    │   ├── ER_Diagram.png
    │   ├── gif
    │   ├── icon
    │   ├── StaTube .png
    │   ├── StaTube_logo.png
    │   └── wireframe.excalidraw
    ├── Backend
    │   ├── __init__.py
    │   ├── ScrapeChannel.py
    │   ├── ScrapeComments.py
    │   ├── ScrapeTranscription.py
    │   └── ScrapeVideo.py
    ├── build
    │   └── installer
	│   	└── installer
	│   		├── StaTube.iss
	│  			└── extract_metadata.py
    ├── Data
    │   ├── __init__.py
    │   ├── DatabaseManager.py
    │   └── schema.sql
    ├── LICENSE
    ├── main.py
    ├── requirements.txt
    ├── UI
    │   ├── __init__.py
    │   ├── CommentPage.py
    │   ├── Homepage.py
    │   ├── MainWindow.py
    │   ├── SettingsPage.py
    │   ├── SplashScreen.py
    │   ├── Style.qss
    │   ├── TranscriptPage.py
    │   └── VideoPage.py
    ├── utils
    │   ├── __init__.py
    │   ├── AppState.py
    │   ├── CheckInternet.py
    │   ├── Config.py
    │   ├── Logger.py
    │   ├── Proxy.py
    │   └── ProxyThread.py
    └── widgets
        ├── __init__.py
        └── DownloadableImage.py
```

### 🌄 Project Index

<details open>
	<summary><b><code>STATUBE/</code></b></summary>
	<details>
		<summary><b>__root__</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ __root__</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./LICENSE'>LICENSE</a></b></td>
					<td style='padding: 8px;'>MIT License file for the project.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./main.py'>main.py</a></b></td>
					<td style='padding: 8px;'>Entry point for the StaTube application. Initializes the PySide6 application loop.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./requirements.txt'>requirements.txt</a></b></td>
					<td style='padding: 8px;'>List of Python dependencies required to run the application (e.g., PySide6, aiohttp).</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<details>
		<summary><b>.github</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ .github</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./.github/dependabot.yml'>dependabot.yml</a></b></td>
					<td style='padding: 8px;'>Configuration for Dependabot dependency updates.</td>
				</tr>
			</table>
			<details>
				<summary><b>workflows</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ .github.workflows</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='./.github/workflows/build-release.yml'>build-release.yml</a></b></td>
							<td style='padding: 8px;'>CI/CD workflow for creating the Windows executable and Inno Setup installer.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='./.github/workflows/python-package.yml'>python-package.yml</a></b></td>
							<td style='padding: 8px;'>CI/CD workflow for testing and packaging the Python module.</td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
    <details>
		<summary><b>Analysis</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ Analysis</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Analysis/__init__.py'>__init__.py</a></b></td>
					<td style='padding: 8px;'>Marks the directory as a Python package.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Analysis/SentimentAnalysis.py'>SentimentAnalysis.py</a></b></td>
					<td style='padding: 8px;'>Module for performing sentiment analysis on fetched comments.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Analysis/WordCloud.py'>WordCloud.py</a></b></td>
					<td style='padding: 8px;'>Module for generating visual word clouds from text data (transcripts/comments).</td>
				</tr>
			</table>
		</blockquote>
	</details>
    <details>
		<summary><b>assets</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ assets</b></code>
				<p style='padding: 8px;'>Directory containing project images, diagrams (`ER_Diagram.png`, `wireframe.excalidraw`), icons, and the application logo (`StaTube_logo.png`).</p>
			</table>
		</blockquote>
	</details>
	<details>
		<summary><b>Backend</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ Backend</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Backend/__init__.py'>__init__.py</a></b></td>
					<td style='padding: 8px;'>Marks the directory as a Python package.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Backend/ScrapeChannel.py'>ScrapeChannel.py</a></b></td>
					<td style='padding: 8px;'>Logic for fetching video lists from a YouTube Channel.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Backend/ScrapeComments.py'>ScrapeComments.py</a></b></td>
					<td style='padding: 8px;'>Logic for fetching user comments from specific videos.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Backend/ScrapeTranscription.py'>ScrapeTranscription.py</a></b></td>
					<td style='padding: 8px;'>Logic for retrieving video transcripts.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Backend/ScrapeVideo.py'>ScrapeVideo.py</a></b></td>
					<td style='padding: 8px;'>Core logic for general video metadata scraping.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<details>
		<summary><b>build</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ build</b></code>
			<details>
				<summary><b>installer</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ build.installer</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='./build/installer/extract_metadata.py'>extract_metadata.py</a></b></td>
							<td style='padding: 8px;'>Helper script to extract version and metadata for the installer generation.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='./build/installer/StaTube.iss'>StaTube.iss</a></b></td>
							<td style='padding: 8px;'>Inno Setup script used to generate the Windows Installer (.exe) for end-users.</td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
	<details>
		<summary><b>Data</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ Data</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Data/__init__.py'>__init__.py</a></b></td>
					<td style='padding: 8px;'>Marks the directory as a Python package.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Data/DatabaseManager.py'>DatabaseManager.py</a></b></td>
					<td style='padding: 8px;'>Handles interactions and operations with the local SQLite database.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./Data/schema.sql'>schema.sql</a></b></td>
					<td style='padding: 8px;'>Defines the SQL schema for the local SQLite database.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<details>
		<summary><b>UI</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ UI</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/__init__.py'>__init__.py</a></b></td>
					<td style='padding: 8px;'>Marks the directory as a Python package.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/CommentPage.py'>CommentPage.py</a></b></td>
					<td style='padding: 8px;'>UI widget for displaying and interacting with video comments.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/Homepage.py'>Homepage.py</a></b></td>
					<td style='padding: 8px;'>The main landing page or dashboard UI component.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/MainWindow.py'>MainWindow.py</a></b></td>
					<td style='padding: 8px;'>The main window structure and application frame.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/SettingsPage.py'>SettingsPage.py</a></b></td>
					<td style='padding: 8px;'>UI widget for configuring application settings (e.g., proxy).</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/SplashScreen.py'>SplashScreen.py</a></b></td>
					<td style='padding: 8px;'>UI component shown during application startup/loading.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/Style.qss'>Style.qss</a></b></td>
					<td style='padding: 8px;'>Qt Stylesheet file for custom application look and feel.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/TranscriptPage.py'>TranscriptPage.py</a></b></td>
					<td style='padding: 8px;'>UI widget for viewing and analyzing video transcripts.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./UI/VideoPage.py'>VideoPage.py</a></b></td>
					<td style='padding: 8px;'>UI component for displaying video list and metadata.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<details>
		<summary><b>utils</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ utils</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./utils/__init__.py'>__init__.py</a></b></td>
					<td style='padding: 8px;'>Marks the directory as a Python package.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./utils/AppState.py'>AppState.py</a></b></td>
					<td style='padding: 8px;'>Manages and holds the global state of the application.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./utils/CheckInternet.py'>CheckInternet.py</a></b></td>
					<td style='padding: 8px;'>Utility function to verify network connectivity.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./utils/Config.py'>Config.py</a></b></td>
					<td style='padding: 8px;'>Handles application configuration and settings management.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./utils/Logger.py'>Logger.py</a></b></td>
					<td style='padding: 8px;'>Utility for application logging and error handling.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./utils/Proxy.py'>Proxy.py</a></b></td>
					<td style='padding: 8px;'>Module for managing proxy connection details.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./utils/ProxyThread.py'>ProxyThread.py</a></b></td>
					<td style='padding: 8px;'>Threading logic for asynchronous proxy operations.</td>
				</tr>
			</table>
		</blockquote>
	</details>
	<details>
		<summary><b>widgets</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ widgets</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./widgets/__init__.py'>__init__.py</a></b></td>
					<td style='padding: 8px;'>Marks the directory as a Python package.</td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='./widgets/DownloadableImage.py'>DownloadableImage.py</a></b></td>
					<td style='padding: 8px;'>Custom widget for displaying images that can be downloaded.</td>
				</tr>
			</table>
		</blockquote>
	</details>
</details>

---

## 🚀 Getting Started

### 🌟 Prerequisites

This project requires the following dependencies:

- **Programming Language:** Python 3.9 or later
- **Package Manager:** Pip

### ⚡ Installation

**Windows:**

Go to the [Releases](https://github.com/Sakth1/StaTube/releases) page and download the installer or portable version.

**Linux/macOS:**

Build StaTube from the source and install dependencies:

1. **Clone the repository:**

    ```sh
    git clone https://github.com/Sakth1/StaTube.git
    ```

2. **Navigate to the project directory:**

    ```sh
    cd StaTube
    ```

3. **Install the dependencies:**

	```sh
	pip install -r requirements.txt
	```

### 🔆 Usage

Run the project with:

```sh
python main.py
```

1. Search for the channel you want to do comment/transcript analysis.
2. Select the channel.
3. Select videos from the channel and scrape transcripts or comment.
4. Analysis will be done and you will be able to visualize and download the analysis.

### 📦 Building the Installer

The project includes an automated workflow to create a portable executable and Windows Installer (`.exe`).

1. **Workflow:** The `.github/workflows/build-release.yml` file handles the CI/CD pipeline.
2. **Inno Setup:** The installer is generated using **Inno Setup**, utilizing the configuration script located at `build/installer/StaTube.iss`.
3. **Metadata:** `build/installer/extract_metadata.py` is used during the build process to ensure the installer is versioned correctly.

To generate the installer locally, you must have Inno Setup installed and compile the `StaTube.iss` script after generating the executable.

---

## 🌻 Roadmap

- [ ] **Docker Version**: A Dockerized version of the application is planned.
- [ ] **Proxy Settings**: Ability to configure network proxy settings.
- [ ] **Theming**: Light/Dark theme support.
- [ ] **In-App Help**: Built-in documentation and help guide.

---

## 🤝 Contributing

- **💬 [Join the Discussions](https://github.com/Sakth1/StaTube/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://github.com/Sakth1/StaTube/issues)**: Submit bugs found or log feature requests for the `StaTube` project.
- **💡 [Submit Pull Requests](https://github.com/Sakth1/StaTube/pulls)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your account.
2. **Clone Locally**: Clone the forked repository to your local machine.
   ```sh
   git clone [https://github.com/Sakth1/StaTube.git](https://github.com/Sakth1/StaTube.git)
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to Remote**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
</details>

---

## 📜 License

StaTube is protected under the [MIT License](https://choosealicense.com/licenses/mit/). For more details, refer to the [LICENSE](./LICENSE) file.

---

## ✨ Acknowledgments

- Built using the [PySide6](https://pypi.org/project/PySide6/) framework.
- YouTube data scrapping possible by:
	- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
	- [scrapetube](https://github.com/dermasmid/scrapetube)

<div align="right">

[![][back-to-top]](#top)

</div>


[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square