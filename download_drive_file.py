import asyncio
import os
import argparse
import sys
import platform
import subprocess
import urllib.parse
import re
import time
from playwright.async_api import async_playwright

def get_ffmpeg_path():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "ffmpeg"
    except FileNotFoundError:
        return None

def force_close_browser():
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["pkill", "-f", "chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    except Exception:
        pass

def prepare_persistent_profile():
    persistent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
    if os.path.exists(os.path.join(persistent_dir, "Default", "Network", "Cookies")):
        return persistent_dir
    os.makedirs(persistent_dir, exist_ok=True)
    return persistent_dir

async def extract_folder_items(page, folder_url):
    print(f"📂 Navigating to folder: {folder_url}")
    await page.goto(folder_url, wait_until="domcontentloaded", timeout=60000)
    print("⏳ Waiting for folder contents to load (please log in if asked)...")
    await asyncio.sleep(5)
    
    if "Sign-in" in await page.title() or "accounts.google.com" in page.url:
        print("\n⚠️ Google Sign-In required!")
        for _ in range(120):
            await asyncio.sleep(1)
            if "accounts.google.com" not in page.url:
                print("✅ Login detected! Continuing...")
                await asyncio.sleep(5)
                break
                
    print("📜 Scrolling to discover all files in the folder...")
    for _ in range(8):
        await page.mouse.wheel(0, 5000)
        await asyncio.sleep(1)
        
    files = await page.evaluate(r'''() => {
        let results = [];
        let links = document.querySelectorAll('a[href*="/file/d/"]');
        for (let a of links) {
            let match = a.href.match(/\/file\/d\/([^/]+)/);
            if (match) {
                let name = a.innerText || a.getAttribute('aria-label') || "Unknown";
                results.push({id: match[1], name: name.replace(/\n/g, ' ').trim()});
            }
        }
        if (results.length === 0) {
            let elements = document.querySelectorAll('[data-id]');
            for (let el of elements) {
                let id = el.getAttribute('data-id');
                if (id && id.length >= 28 && id.length <= 35) {
                    let name = el.innerText || el.getAttribute('aria-label') || id;
                    results.push({id: id, name: name.split('\n')[0].trim()});
                }
            }
        }
        let unique = [];
        let seen = new Set();
        for (let item of results) {
            if (!seen.has(item.id)) {
                seen.add(item.id);
                unique.push(item);
            }
        }
        return unique;
    }''')
    
    print(f"✅ Found {len(files)} items in folder.")
    return files

async def extract_video_streams(context, file_id, file_name):
    print(f"\n🎬 Processing: {file_name}")
    page = await context.new_page()
    await page.bring_to_front()
    
    captured_urls = {}
    
    def handle_request(request):
        url = request.url
        if "videoplayback" in url:
            decoded_url = urllib.parse.unquote(url)
            is_video = "mime=video" in decoded_url
            is_audio = "mime=audio" in decoded_url
            
            full_url = re.sub(r'&range=[^&]*', '', url)
            full_url = re.sub(r'\?range=[^&]*&', '?', full_url)
            full_url = re.sub(r'\?range=[^&]*$', '', full_url)
            for param in ['alr', 'rn', 'rbuf', 'ump']:
                full_url = re.sub(rf'&{param}=[^&]*', '', full_url)
                full_url = re.sub(rf'\?{param}=[^&]*&', '?', full_url)
                full_url = re.sub(rf'\?{param}=[^&]*$', '', full_url)
            
            if is_video:
                captured_urls["video"] = full_url
            elif is_audio:
                captured_urls["audio"] = full_url

    page.on("request", handle_request)
    
    file_url = f"https://drive.google.com/file/d/{file_id}/view"
    await page.goto(file_url, wait_until="domcontentloaded")
    
    if "Sign-in" in await page.title() or "accounts.google.com" in page.url:
        print("⚠️ Waiting for login...")
        for _ in range(60):
            await asyncio.sleep(1)
            if "accounts.google.com" not in page.url:
                break
                
    print("🔍 Waiting for Drive player UI to load (this can take a few seconds)...")
    
    try:
        drive_play = page.locator('div[role="button"][aria-label="Play"], button[aria-label="Play"], div[aria-label="Play"]').first
        await drive_play.wait_for(state="visible", timeout=15000)
        print("▶️ Found Drive Play button. Clicking...")
        await drive_play.click(force=True)
    except Exception:
        print("⚠️ No Drive Play button found. Blind clicking center of screen...")
        if page.viewport_size:
            await page.mouse.click(page.viewport_size['width'] / 2, page.viewport_size['height'] / 2)
            
    print("🔍 Waiting for YouTube iframe to initialize...")
    player_frame = None
    for _ in range(20):
        for frame in page.frames:
            try:
                video_el = frame.locator("video").first
                if await video_el.is_visible(timeout=500):
                    player_frame = frame
                    break
            except Exception:
                continue
        if player_frame:
            break
        await asyncio.sleep(1)
        
    if player_frame:
        print("✅ Found YouTube video frame!")
        try:
            play_btn = player_frame.locator(".ytp-large-play-button").first
            if await play_btn.is_visible(timeout=2000):
                print("▶️ Clicking YouTube play button...")
                await play_btn.click(force=True)
            else:
                print("▶️ Forcing video playback via JavaScript...")
                await player_frame.locator("video").first.evaluate("el => el.play()")
        except Exception as e:
            print(f"⚠️ Playback force failed: {e}")
    else:
        print("❌ Could not find the video frame. The video might still be processing on Google Drive.")
    
    if player_frame:
        print("⚙️ Forcing highest quality...")
        try:
            settings_btn = player_frame.locator(".ytp-settings-button").first
            if await settings_btn.is_visible():
                print("⚙️ Opening player settings...")
                await settings_btn.click(force=True)
                await asyncio.sleep(1)
                
                print("⚙️ Clicking Quality menu...")
                quality_item = player_frame.locator('.ytp-menuitem:has-text("Quality"), .ytp-menuitem:has-text("Auto"), .ytp-menuitem:has-text("1080p"), .ytp-menuitem:has-text("720p")').first
                if await quality_item.is_visible():
                    await quality_item.click(force=True)
                    await asyncio.sleep(1)
                    
                    # Clear out the old low-quality streams BEFORE we click the highest quality
                    captured_urls.clear()
                    print("🔄 Cleared initial low-quality streams...")
                    
                    print("⚙️ Attempting to select the highest available quality...")
                    qualities_to_try = ["1080p", "720p", "480p", "360p", "240p", "144p"]
                    quality_selected = False
                    
                    for q in qualities_to_try:
                        q_item = player_frame.locator(f'.ytp-menuitem:has-text("{q}")').first
                        if await q_item.is_visible():
                            await q_item.click(force=True)
                            print(f"✅ {q} selected! Capturing new stream URLs...")
                            quality_selected = True
                            break
                            
                    if not quality_selected:
                        print("⚠️ Could not find a specific quality option. Leaving at default/Auto.")
                        if page.viewport_size:
                            await page.mouse.click(10, 10)
                else:
                    print("⚠️ Could not find the Quality option in settings.")
                    if page.viewport_size:
                        await page.mouse.click(10, 10)
            else:
                print("⚠️ Could not find the settings gear icon in DOM.")
                
        except Exception as e:
            print(f"⚠️ Notice: Quality UI interaction failed (leaving at default quality): {e}")
            
    print("⏳ Waiting for stream URLs...")
    for _ in range(20):
        if "video" in captured_urls and "audio" in captured_urls:
            print("✅ Captured highest quality streams!")
            await asyncio.sleep(2)
            break
        await asyncio.sleep(1)
        
    await page.close()
    
    if "video" in captured_urls and "audio" in captured_urls:
        return {
            "id": file_id,
            "name": file_name,
            "video_url": captured_urls["video"],
            "audio_url": captured_urls["audio"]
        }
    else:
        print(f"❌ Failed to capture streams for {file_name}. (Might not be a video)")
        return None

async def download_file(context, item, download_dir, user_agent):
    file_id = item["id"]
    file_name = "".join(c for c in item["name"] if c.isalnum() or c in " ._-").strip()
    if not file_name:
        file_name = file_id
        
    print(f"\n⬇️ Starting background download for: {file_name}")
    
    video_path = os.path.join(download_dir, f"temp_v_{file_id}.mp4")
    audio_path = os.path.join(download_dir, f"temp_a_{file_id}.mp4")
    final_path = os.path.join(download_dir, f"{file_name}.mp4")
    
    if os.path.exists(final_path):
        print(f"⏭️ Skipping {file_name} (already downloaded)")
        return
        
    # Extract cookies to use natively in Python, avoiding browser UI glitches
    cookies = await context.cookies()
    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    
    import shutil
    import urllib.request
    
    def stream_download_sync(url, out_path):
        req = urllib.request.Request(url, headers={
            "Cookie": cookie_str,
            "User-Agent": user_agent,
            "Referer": "https://drive.google.com/"
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as response, open(out_path, 'wb') as out_file:
                # Download in chunks directly to disk
                shutil.copyfileobj(response, out_file, length=1024*1024)
            return True
        except Exception as e:
            print(f"❌ HTTP Download error: {e}")
            return False
            
    async def run_download(stream_type, url, out_path):
        success = await asyncio.to_thread(stream_download_sync, url, out_path)
        if success:
            print(f"✅ Downloaded {stream_type} for {file_name}")
        else:
            print(f"❌ Failed {stream_type} download for {file_name}")
            
    await asyncio.gather(
        run_download("video", item["video_url"], video_path),
        run_download("audio", item["audio_url"], audio_path)
    )
    
    if os.path.exists(video_path) and os.path.exists(audio_path):
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            print(f"🔄 Merging audio/video for {file_name}...")
            try:
                subprocess.run([
                    ffmpeg_path, "-y",
                    "-i", video_path, "-i", audio_path,
                    "-c:v", "copy", "-c:a", "aac",
                    final_path
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.remove(video_path)
                os.remove(audio_path)
                print(f"🎉 Successfully saved: {final_path}")
            except Exception as e:
                print(f"❌ FFmpeg error on {file_name}: {e}")
        else:
            print(f"⚠️ FFmpeg missing! Kept temporary files for {file_name}")

async def main():
    parser = argparse.ArgumentParser(description="Google Drive Folder/File Downloader")
    parser.add_argument("url", help="Google Drive Folder or File URL")
    parser.add_argument("--download-dir", default="./downloads", help="Directory to save downloads")
    args = parser.parse_args()

    url = args.url
    download_dir = args.download_dir
    os.makedirs(download_dir, exist_ok=True)
    
    print("Force closing background Chrome...")
    force_close_browser()
    
    persistent_profile = prepare_persistent_profile()
    
    print(f"Launching Chrome with isolated automation profile...")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=persistent_profile,
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            user_agent=user_agent
        )
        
        main_page = context.pages[0] if context.pages else await context.new_page()
        
        items_to_process = []
        
        if "/folders/" in url or "drive/u/" in url:
            items = await extract_folder_items(main_page, url)
            for item in items:
                items_to_process.append(item)
        else:
            match = re.search(r'/file/d/([^/]+)', url)
            file_id = match.group(1) if match else "unknown_file"
            # Use the unique file_id as the name to prevent naming collisions for single links
            items_to_process.append({"id": file_id, "name": file_id})
            
        print(f"\n🎯 Found {len(items_to_process)} items. Checking download status...")
        
        pending_items = []
        for item in items_to_process:
            file_id = item["id"]
            file_name = "".join(c for c in item["name"] if c.isalnum() or c in " ._-").strip()
            if not file_name:
                file_name = file_id
            final_path = os.path.join(download_dir, f"{file_name}.mp4")
            
            if os.path.exists(final_path):
                print(f"⏭️ Skipping '{file_name}' (already fully downloaded)")
            else:
                pending_items.append(item)
                
        if not pending_items:
            print("\n✅ All videos have already been downloaded!")
            await context.close()
            return
            
        print(f"\n🚀 Starting stream extraction phase for {len(pending_items)} pending video(s)...")
        
        stream_data = []
        for item in pending_items:
            data = await extract_video_streams(context, item["id"], item["name"])
            if data:
                stream_data.append(data)
                
        print(f"\n🚀 Extracted metadata for {len(stream_data)} videos. Starting parallel downloads...")
        
        download_tasks = [download_file(context, data, download_dir, user_agent) for data in stream_data]
        await asyncio.gather(*download_tasks)
        
        print("\n✅ All operations completed!")
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())