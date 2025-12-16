from playwright.sync_api import sync_playwright

COOKIES_FILE = "cookies.txt"
PROFILE_URL = "https://www.tiktok.com/@ygannda"

def load_cookies(file_path):
    cookies = []
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) != 7:
                continue
            domain, flag, path, secure, expiration, name, value = parts
            cookies.append({
                "domain": domain,
                "path": path,
                "name": name,
                "value": value,
                "secure": secure == "TRUE",
                "expires": int(expiration) if expiration.isdigit() else -1
            })
    return cookies


def main():
    cookies = load_cookies(COOKIES_FILE)
    print(f"[INFO] Loaded {len(cookies)} cookies...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # Pasang cookies login
        context.add_cookies(cookies)

        page = context.new_page()
        print("[INFO] Opening TikTok...")

        page.goto(PROFILE_URL, timeout=60000)

        page.wait_for_timeout(5000)

        # Deteksi gagal login
        if "login" in page.url:
            print("[ERROR] Cookies expired / tidak valid. Ambil cookies baru.")
            return

        print("[SUCCESS] Login berhasil! Profil terbuka.\n")

        print("[INFO] Mulai scraping video repost...\n")

        # Scroll untuk load semua video
        for _ in range(6):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(1200)

        # Ambil semua elemen video
        videos = page.locator("div[data-e2e='user-post-item']")
        total = videos.count()

        print(f"[INFO] Total video ditemukan: {total}")

        repost_list = []

        for i in range(total):
            print(f"\n[INFO] Mengecek video ke-{i+1}/{total}...")

            videos.nth(i).click()
            page.wait_for_timeout(2500)

            # Cek apakah ada label repost
            is_repost = False
            try:
                repost_badge = page.locator("span:has-text('Reposts'), span:has-text('Di-post ulang')")
                repost_badge.wait_for(state="visible", timeout=4000)
                is_repost = True
            except:
                is_repost = False

            if is_repost:
                print("[FOUND] Video ini REPOST!")

                video_url = page.url

                # Ambil caption (optional)
                try:
                    caption = page.locator("h1[data-e2e='video-caption']").inner_text(timeout=3000)
                except:
                    caption = "(tidak ada caption)"

                repost_list.append({
                    "index": i + 1,
                    "url": video_url,
                    "caption": caption
                })
            else:
                print("[INFO] Bukan repost.")

            # Kembali ke halaman profil
            page.go_back()
            page.wait_for_timeout(2000)

        print("\n===== HASIL VIDEO REPOST =====")
        for vid in repost_list:
            print(f"{vid['index']}. {vid['url']} | {vid['caption']}")

        print("\n[INFO] Selesai scraping.")
        input("\nTekan ENTER untuk keluar...")
        browser.close()


if __name__ == "__main__":
    main()
