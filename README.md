# Google Drive Video Downloader

A high-performance tool that automates downloading the highest quality video and audio streams from Google Drive video links and merges them seamlessly into a single `.mp4` file using `ffmpeg`.

It uses your local browser session (Microsoft Edge or Google Chrome) to handle authentication, ensuring access to private, restricted, or view-only Google Drive files without requiring API keys or OAuth credentials.

---

## Features

- **Highest Quality Selection**: Automatically selects 1080p (or maximum available resolution) from Google Drive's player.
- **Standalone Executable**: Bundled with `ffmpeg` and Playwright drivers into a portable `.exe` using PyInstaller.
- **Session Re-use**: Leverages your logged-in browser session to download files you have access to.
- **Auto-Merge**: Downloads separated video and audio streams natively and merges them losslessly into a final `.mp4`.

---

## 🚀 Quick Start (Running the Compiled Executable)

If you are using the compiled binary (`download_drive_file.exe`), you **do not need Python or ffmpeg installed**.

### Prerequisites
1. **Operating System**: Windows 10/11 (64-bit).
2. **Browser**: Microsoft Edge (built-in) or Google Chrome.
3. **Google Account**: Ensure you are logged into Google in your browser so the tool can access the file.

### How to Run

1. Open **Command Prompt** or **PowerShell**.
2. Navigate to the folder containing `download_drive_file.exe`:
   ```cmd
   cd path\to\dist
   ```
3. Run the executable with your Google Drive video URL:
   ```cmd
   download_drive_file.exe "YOUR_GOOGLE_DRIVE_VIDEO_URL"
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
- Place `ffmpeg.exe` in the root folder of the project.

### 2. Install Build Dependencies
```cmd
pip install playwright pyinstaller
playwright install chromium
```

### 3. Build with PyInstaller
Run the build using the provided `.spec` file:
```cmd
pyinstaller download_drive_file.spec
```

Once the build finishes, your standalone executable will be generated at:
```
dist/download_drive_file.exe
```

---

## 🐍 Running from Python Source

If you prefer running directly from source code without compiling:

### Windows Setup

1. **Install Dependencies:**
   ```cmd
   pip install playwright
   playwright install chromium
   ```

2. **Ensure ffmpeg is available:**
   - Either place `ffmpeg.exe` in the project root directory, or add `ffmpeg` to your system PATH.

3. **Run the script:**
   ```cmd
   python download_drive_file.py "YOUR_GOOGLE_DRIVE_VIDEO_URL"
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
| `--browser` | Specify browser engine (`msedge` or `chrome`) | `msedge` (Windows) / `chrome` (Linux) |
| `--download-dir` | Directory to save the final video | `./downloads` |
| `--profile-dir` | Custom path to browser user profile | Auto-detected system profile path |

### Examples with Options

- **Specify download folder:**
  ```cmd
  download_drive_file.exe "YOUR_URL" --download-dir "D:\MyVideos"
  ```

- **Use Google Chrome instead of Edge:**
  ```cmd
  download_drive_file.exe "YOUR_URL" --browser chrome
  ```

- **Use custom browser profile directory:**
  ```cmd
  download_drive_file.exe "YOUR_URL" --profile-dir "C:\Users\username\AppData\Local\Google\Chrome\User Data"
  ```

---

## 💡 Troubleshooting & Notes

- **Browser Closes Automatically:**
  Playwright requires exclusive access to the browser user profile. The script will automatically close active background browser processes before launching.
- **Permission Denied / URL Not Intercepted:**
  Ensure you are logged into the Google Account that has view/download permissions for the target file in your selected browser.
- **Temporary Files:**
  The separate `video.mp4` and `audio.mp4` streams are downloaded temporarily and automatically merged and cleaned up after creating `final_video.mp4`.
