# Google Drive Video Downloader

This script automates the process of downloading the highest quality video and audio streams from a Google Drive video link and merges them into a single file using `ffmpeg`. It uses Microsoft Edge or Google Chrome to handle the authentication and capture the streams dynamically.

## Prerequisites

Before running the script, you need to ensure you have the following installed on your system:
1. **Python** (Version 3.8 or higher)
2. **ffmpeg** (Used for merging video and audio)
3. **Microsoft Edge** or **Google Chrome** browser

---

## Installation & Setup

### For Windows

1. **Install Python:**
   - Download Python from [python.org](https://www.python.org/downloads/windows/).
   - During installation, **ensure you check the box that says "Add Python to PATH"**.

2. **Install ffmpeg:**
   - Download the latest `ffmpeg` build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (choose the `ffmpeg-release-essentials.zip`).
   - Extract the `.zip` file.
   - Rename the extracted folder to `ffmpeg` and move it to your `C:\` drive (e.g., `C:\ffmpeg`).
   - Add `ffmpeg` to your system PATH:
     - Press the `Windows Key`, type **Environment Variables**, and select **Edit the system environment variables**.
     - Click **Environment Variables...** at the bottom.
     - Under **System variables**, find and select `Path`, then click **Edit**.
     - Click **New** and add the path to the ffmpeg bin folder (e.g., `C:\ffmpeg\bin`).
     - Click **OK** to save and close all windows.

3. **Install Script Dependencies:**
   Open a terminal (Command Prompt or PowerShell) and run the following commands:
   ```cmd
   pip install playwright
   playwright install chromium
   ```

### For Ubuntu (Linux)

1. **Install Python and pip:**
   Open your terminal and run:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Install ffmpeg:**
   Run the following command to install `ffmpeg`:
   ```bash
   sudo apt install ffmpeg
   ```

3. **Install Google Chrome (if not already installed):**
   ```bash
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo apt install ./google-chrome-stable_current_amd64.deb
   ```

4. **Install Script Dependencies:**
   In your terminal, navigate to the folder containing this script and run:
   ```bash
   pip3 install playwright
   playwright install chromium
   ```

---

## How to Run the Script

Before running the script, make sure you are logged into your Google account in your browser (Edge on Windows, or Chrome on Ubuntu). This allows the script to access the Google Drive video without permission issues.

### Running on Windows
Open Command Prompt or PowerShell, navigate to the folder where the script is located, and run:

```cmd
python download_drive_file.py "YOUR_GOOGLE_DRIVE_VIDEO_URL"
```

**Example:**
```cmd
python download_drive_file.py "https://drive.google.com/file/d/1EG7hhxWLw4rg1krBKebmk9wu23tvt1Yr/view?usp=drive_link"
```

### Running on Ubuntu
Open your terminal, navigate to the folder where the script is located, and run:

```bash
python3 download_drive_file.py "YOUR_GOOGLE_DRIVE_VIDEO_URL"
```

### Additional Options

The script will automatically detect your operating system and use the default browser (Edge for Windows, Chrome for Linux). However, you can customize its behavior using the following optional flags:

- `--browser`: Specify the browser to use (`msedge` or `chrome`).
- `--profile-dir`: Provide a custom path to your browser's User Data profile directory.
- `--download-dir`: Specify a custom folder to save the final video (default is `./downloads`).

**Example of using optional flags:**
```bash
python3 download_drive_file.py "YOUR_URL_HERE" --browser chrome --download-dir "/path/to/save/videos"
```

## Troubleshooting

- **The script crashes immediately or says "Failed to launch browser":**
  Ensure you have closed all running instances of your browser before running the script.
- **ffmpeg not found warning:**
  The script successfully downloaded the video and audio, but failed to merge them because `ffmpeg` is not properly installed or not added to your system PATH.
- **Permission Denied / URL Not Captured:**
  Ensure you have opened your browser normally and logged into the Google account that has access to the Drive file. The script borrows your login session.
