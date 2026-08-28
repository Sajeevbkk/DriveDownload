import asyncio
import time
import urllib.parse
import urllib.request
import shutil
import subprocess
import os
import sys
import platform
import argparse
from playwright.async_api import async_playwright

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def get_ffmpeg_path():
    """Gets the path to ffmpeg, preferring the PyInstaller bundled version if available."""
    # If running as a PyInstaller bundle, look in the extracted _MEIPASS directory
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled_ffmpeg = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        if os.path.exists(bundled_ffmpeg):
            return bundled_ffmpeg
            
    # Otherwise, fall back to checking the system's PATH
    return shutil.which("ffmpeg")

def force_close_browser(browser_channel):
    """Kills all background browser processes so Playwright can safely access the profile."""
    print(f"Ensuring all {browser_channel} processes are closed...")
    try:
        if platform.system() == "Windows":
            if browser_channel == "msedge":
                subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            if browser_channel == "msedge":
                subprocess.run(["pkill", "-f", "msedge"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Give it a second to clean up process locks
        import time
        time.sleep(1)
    except Exception as error:
        sys.stderr.write(f"{error}\n")

async def get_video_urls_and_cookies(file_url, user_data_dir, browser_channel):
    force_close_browser(browser_channel)
    print(f"Launching {browser_channel} to capture URLs...")
    captured_urls = {}
    
    # Adjust user agent slightly based on browser to blend in
    if browser_channel == "msedge":
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.0.0"
    else:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel=browser_channel,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                user_agent=user_agent
            )
            print("Launching browser...")
        except Exception as e:
            print(f"❌ Failed to launch browser: {e}")
            print(f"Please check if {browser_channel} is installed and the profile directory '{user_data_dir}' is valid and accessible.")
            return None, None, None
            
        page = await context.new_page()

        def handle_request(request):
            url = request.url
            if "videoplayback" in url:
                decoded_url = urllib.parse.unquote(url)
                is_video = "mime=video" in decoded_url
                is_audio = "mime=audio" in decoded_url
                
                import re
                # Google Drive URLs are cryptographically signed. Using urlparse breaks the signature!
                # We must use regex to cleanly remove ONLY the range parameter.
                full_url = re.sub(r'&range=[^&]*', '', url)
                full_url = re.sub(r'\?range=[^&]*&', '?', full_url)
                full_url = re.sub(r'\?range=[^&]*$', '', full_url)
                
                # Also remove chunking parameters so we get a raw video file instead of a protobuf stream
                for param in ['alr', 'rn', 'rbuf', 'ump']:
                    full_url = re.sub(rf'&{param}=[^&]*', '', full_url)
                    full_url = re.sub(rf'\?{param}=[^&]*&', '?', full_url)
                    full_url = re.sub(rf'\?{param}=[^&]*$', '', full_url)
                
                # Overwrite with the latest requested URLs 
                # (so we get the 1080p ones after switching quality)
                if is_video:
                    captured_urls["video"] = full_url
                elif is_audio:
                    captured_urls["audio"] = full_url
                    
        page.on("request", handle_request)
        
        print(f"Navigating to {file_url}...")
        await page.goto(file_url)
        
        print("Waiting for the page to settle...")
        await asyncio.sleep(5) 
        
        print("Searching for the video player inside iframes...")
        player_frame = None
        
        # Drive embeds the video in an iframe, so we must search across all frames
        for frame in page.frames:
            try:
                # The giant play button in the center
                play_btn = frame.locator(".ytp-large-play-button").first
                if await play_btn.is_visible():
                    print("✅ Found the video player! Clicking Play...")
                    await play_btn.click()
                    player_frame = frame
                    break
            except Exception:
                continue
                
        # Fallback to clicking center of the screen if we couldn't find the play button
        if not player_frame:
            print("⚠️ Could not find the Play button. Clicking the center of the screen as a fallback...")
            if page.viewport_size:
                await page.mouse.click(page.viewport_size['width'] / 2, page.viewport_size['height'] / 2)
            
        await asyncio.sleep(3)
        
        try:
            print("Searching for quality settings inside the player...")
            
            # If we didn't identify the frame earlier, try finding it via the settings button
            if not player_frame:
                for frame in page.frames:
                    try:
                        btn = frame.locator(".ytp-settings-button").first
                        if await btn.is_visible():
                            player_frame = frame
                            break
                    except Exception:
                        continue
            
            if player_frame:
                settings_btn = player_frame.locator(".ytp-settings-button").first
                if await settings_btn.is_visible():
                    print("Opening player settings...")
                    await settings_btn.click()
                    await asyncio.sleep(1)
                    
                    print("Clicking Quality menu...")
                    quality_item = player_frame.locator('.ytp-menuitem:has-text("Quality"), .ytp-menuitem:has-text("Auto"), .ytp-menuitem:has-text("1080p"), .ytp-menuitem:has-text("720p")').first
                    if await quality_item.is_visible():
                        await quality_item.click()
                        await asyncio.sleep(1)
                        
                        print("Attempting to select the highest available quality...")
                        qualities_to_try = ["1080p", "720p", "480p", "360p", "240p", "144p"]
                        quality_selected = False
                        
                        for q in qualities_to_try:
                            q_item = player_frame.locator(f'.ytp-menuitem:has-text("{q}")').first
                            if await q_item.is_visible():
                                await q_item.click()
                                print(f"✅ {q} selected! Capturing new stream URLs...")
                                quality_selected = True
                                break
                                
                        if not quality_selected:
                            print("⚠️ Could not find a specific quality option. Leaving at default/Auto.")
                            await page.mouse.click(10, 10) # close the menu
                    else:
                        print("Could not find the Quality option in settings.")
                        await page.mouse.click(10, 10)
                else:
                    print("Could not find the settings gear icon. Video might not support quality selection.")
            else:
                print("Could not locate the player frame.")
                
        except Exception as e:
            print(f"UI interaction failed: {e}")
            print("Feel free to manually change quality in the browser window!")

        print("\nWaiting 10 seconds to collect the latest network requests...")
        await asyncio.sleep(10)
        
        # Extract cookies so we can download the files outside the browser
        cookies = await context.cookies()
        
        await context.close()
        
    return captured_urls, cookies, user_agent

async def main():
    parser = argparse.ArgumentParser(description="Download Google Drive video in highest quality.")
    parser.add_argument("url", metavar="drive url", nargs=1, help="Google Drive File URL")
    parser.add_argument("--profile-dir", help="Path to browser profile directory (optional)")
    parser.add_argument("--browser", choices=["msedge", "chrome"], help="Browser to use (msedge or chrome) (optional)")
    parser.add_argument("--download-dir", default="./downloads", help="Directory to save downloads")
    args = parser.parse_args()

    DRIVE_FILE_URL = args.url[0]
    DOWNLOAD_DIR = args.download_dir
    browser_channel = args.browser
    profile_dir = args.profile_dir

    if not browser_channel:
        if platform.system() == "Windows":
            browser_channel = "msedge"
        else:
            browser_channel = "chrome"

    if not profile_dir:
        if platform.system() == "Windows":
             if browser_channel == "msedge":
                 profile_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
             else:
                 profile_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        elif platform.system() == "Linux":
             if browser_channel == "msedge":
                 profile_dir = os.path.expanduser("~/.config/microsoft-edge")
             else:
                 profile_dir = os.path.expanduser("~/.config/google-chrome")
        elif platform.system() == "Darwin":
             if browser_channel == "msedge":
                 profile_dir = os.path.expanduser("~/Library/Application Support/Microsoft Edge")
             else:
                 profile_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")

    print(f"Configuration:")
    print(f"URL: {DRIVE_FILE_URL}")
    print(f"Browser: {browser_channel}")
    print(f"Profile Directory: {profile_dir}")
    print(f"Download Directory: {DOWNLOAD_DIR}")
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print("\n⚠️  WARNING: ffmpeg not found!")
        print("Merging audio and video will not be possible without ffmpeg.")
        print("Please ensure ffmpeg is bundled or installed if you need audio and video merged.")
        time.sleep(3)
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # 1. Capture the URLs and Cookies using Playwright
    urls, cookies, user_agent = await get_video_urls_and_cookies(DRIVE_FILE_URL, profile_dir, browser_channel)
    
    if urls is None:
        return
        
    print("\n✅ URLs captured!")
    if not urls:
        print("⚠️ No URLs were intercepted! The video might not have played.")
        return
    else:
        for t, u in urls.items():
            print(f"{t.upper()} URL: {u[:100]}...")
            
    video_temp = os.path.join(DOWNLOAD_DIR, "video.mp4")
    audio_temp = os.path.join(DOWNLOAD_DIR, "audio.mp4")
    final_output = os.path.join(DOWNLOAD_DIR, "final_video.mp4")
            
    # 2. Use the browser to natively download the extracted URLs
    print("\nStarting browser-native downloads...")
    async with async_playwright() as p:
        # Re-attach to the browser
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel=browser_channel,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent=user_agent
        )
        
        for stream_type, url in urls.items():
            print(f"\nOpening new tab to download {stream_type}...")
            new_page = await context.new_page()
            
            # Navigate to the video stream's exact origin so the browser allows the 'download' attribute
            parsed_url = urllib.parse.urlparse(url)
            origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Mock the origin page to ensure instant, reliable navigation to the correct domain
            async def mock_origin(route):
                if route.request.url in [origin, origin + "/"]:
                    await route.fulfill(status=200, body="<html><body>Download ready</body></html>", content_type="text/html")
                else:
                    await route.continue_()
                
            await new_page.route("**/*", mock_origin)
            try:
                await new_page.goto(origin)
            except Exception:
                pass
                
            print(f"Triggering {stream_type} download...")
            try:
                async with new_page.expect_download(timeout=300000) as download_info:
                    await new_page.evaluate(f'''() => {{
                        const a = document.createElement('a');
                        a.href = "{url}";
                        a.download = "{stream_type}.mp4";
                        document.body.appendChild(a);
                        a.click();
                    }}''')
                
                download = await download_info.value
                out_path = video_temp if stream_type == "video" else audio_temp
                await download.save_as(out_path)
                print(f"✅ Saved {stream_type} to {out_path}")
            except Exception as e:
                print(f"❌ Failed to download {stream_type}: {e}")
                
            await new_page.close()
            
        await context.close()
        
    # 3. Merge them using ffmpeg
    if "video" in urls and "audio" in urls:
        if os.path.exists(video_temp) and os.path.exists(audio_temp):
            if not ffmpeg_path:
                print("\n❌ ffmpeg is not installed or bundled. Both video and audio downloaded but cannot merge.")
                print(f"Video file: {video_temp}")
                print(f"Audio file: {audio_temp}")
                return
            
            print("\nMerging video and audio with ffmpeg...")
            try:
                subprocess.run([
                    ffmpeg_path, "-y",
                    "-i", video_temp,
                    "-i", audio_temp,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    final_output
                ], check=True)
                
                print("\nCleaning up temporary files...")
                os.remove(video_temp)
                os.remove(audio_temp)
                print(f"🎉 All done! Final video saved to {final_output}")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error merging with ffmpeg: {e}")
        else:
            print("\n❌ Missing audio or video file, cannot merge.")
    elif "video" in urls:
        if os.path.exists(video_temp):
            print("\nOnly video stream was downloaded. Moving to final output...")
            shutil.move(video_temp, final_output)
            print(f"🎉 All done! Final video saved to {final_output}")
    elif "audio" in urls:
        if os.path.exists(audio_temp):
            print("\nOnly audio stream was downloaded. Moving to final output...")
            shutil.move(audio_temp, final_output)
            print(f"🎉 All done! Final audio saved to {final_output}")

if __name__ == "__main__":
    asyncio.run(main())
