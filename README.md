# Google Drive Video Downloader

A high-performance tool that automates downloading the highest quality video and audio streams from Google Drive video links and merges them seamlessly into a single `.mp4` file using `ffmpeg`.

It uses your local browser session to handle authentication, ensuring access to private, restricted, or view-only Google Drive files without requiring API keys or OAuth credentials.

---

## Features

- **Highest Quality Selection**: Automatically selects 1080p (or maximum available resolution) from Google Drive's player.
- **Standalone Executable**: Bundled with `ffmpeg` and Playwright drivers into a portable `.exe` using PyInstaller.
- **Auto-Merge**: Downloads separated video and audio streams natively and merges them losslessly into a final `.mp4`.

---

## 🚀 Quick Start (Running the Compiled Executable)

If you are using the compiled binary (`download_drive_file.exe`), you **do not need Python or ffmpeg installed**.

### Prerequisites
1. **Operating System**: Windows 10/11 (64-bit).
2. **Browser**: Google Chrome.
3. **Google Account**: You need to login to Google Account to Access the video.

### How to Run

1. Open **Command Prompt** or **PowerShell**.
2. Navigate to the folder containing `download_drive_file.exe`:
   ```cmd
   cd path\to\dist
   ```
3. Run the executable with your Google Drive video or Folder URL:
   ```cmd
   download_drive_file.exe "YOUR_GOOGLE_DRIVE_VIDEO_URL_OR_FOLDER_URL"
   ```

**Example:**
```cmd
download_drive_file.exe "https://drive.google.com/file/d/1EG7hhxWLw4rg1krBKebmk9wu23tvt1Yr/view?usp=drive_link"
```

The final video will be saved to the `./downloads` folder by default.

---

## 🛠️ Building the Executable from Source (PyInstaller)

If you want to compile the project yourself into a standalone `.exe`:

### 1. Prerequisites
- **Python 3.8+** installed ([python.org](https://www.python.org/)) with **"Add Python to PATH"** checked.

### 2. Install Dependencies
```cmd
pip install -r requirements.txt
playwright install chromium
```

### 3. Build with PyInstaller
Run the build using the provided `.spec` file:
```cmd
pyinstaller --onefile --add-binary "ffmpeg.exe;." --collect-all playwright download_drive_file.py
```

Once the build finishes, your standalone executable will be generated at:
```
dist/download_drive_file.exe
```

---

## 🐍 Running from Python Source

If you prefer running directly from source code without compiling:

### Windows Setup

1. **Create and Activate Virtual Environment (Optional but recommended):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Run the script:**
   ```cmd
   python download_drive_file.py "YOUR_GOOGLE_DRIVE_VIDEO_URL_OR_FOLDER_URL"
   ```

### Linux (Ubuntu) Setup

1. **Install System Dependencies & ffmpeg:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv ffmpeg
   ```

2. **Install Google Chrome (if not installed):**
   ```bash
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo apt install ./google-chrome-stable_current_amd64.deb
   ```

3. **Install Python Packages:**
   ```bash
   pip3 install playwright
   playwright install chromium
   ```

4. **Run the script:**
   ```bash
   python3 download_drive_file.py "YOUR_GOOGLE_DRIVE_VIDEO_URL"
   ```

---

## ⚙️ Command Line Options & Flags

You can customize the downloader using optional command-line flags:

| Flag | Description | Default |
|------|-------------|---------|
| `url` | *(Required)* The Google Drive video file link | - |
| `--download-dir` | Directory to save the final video | `./downloads` |

### Examples with Options

- **Specify download folder:**
  ```cmd
  download_drive_file.exe "YOUR_URL" --download-dir "D:\MyVideos"
  ```

---

## 💡 Troubleshooting & Notes

- **Browser Closes Automatically:**
  Playwright requires exclusive access to the browser user profile. The script will automatically close active background browser processes before launching.
- **Permission Denied / URL Not Intercepted:**
  Ensure you are logged into the Google Account that has view/download permissions for the target file in your selected browser.
- **Temporary Files:**
  The separate `video.mp4` and `audio.mp4` streams are downloaded temporarily and automatically merged and cleaned up after creating `final_video.mp4`.
  
## ❕ Note
- This only works with **Google Chrome**
- This project is done for learning purpose. The developer doesn't have any responsibility if this is misused.
- This program won't be have any regular update & won't be sure it works with future version of Google Chrome. We used Google Chrome 152.0.7977.65 for Windows.
