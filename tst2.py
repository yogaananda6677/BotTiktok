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
        context.add_cookies(cookies)

        page = context.new_page()

        print("[INFO] Opening TikTok…")
        page.goto(PROFILE_URL, timeout=60000)
        page.wait_for_timeout(3000)

        if "login" in page.url:
            print("[ERROR] Cookies expired / invalid.")
            return

        print("[SUCCESS] Login OK!")

        # ---------------------------------------------------------
        # 1. BUKA TAB REPOSTS
        # ---------------------------------------------------------
        print("[INFO] Mencari tombol 'Reposts'...")
        try:
            repost_tab = page.locator("span:has-text('Reposts')").first
            repost_tab.click()
            print("[SUCCESS] Tab Reposts dibuka.")
        except:
            print("[ERROR] Tidak menemukan tab Reposts!")
            return

        page.wait_for_timeout(4000)

        # ---------------------------------------------------------
        # 2. SCROLL PANJANG UNTUK LOAD SEMUA VIDEO
        # ---------------------------------------------------------
        print("[INFO] Scrolling halaman reposts secara panjang...")

        for i in range(25):     # scroll lebih banyak
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(1200)
        print("[INFO] Scrolling selesai.")

        # ---------------------------------------------------------
        # 3. SELECTOR KHUSUS TAB REPOSTS
        # TikTok pakai selector ini untuk postingan ulang:
        # div[data-e2e='user-repost-item']
        # ---------------------------------------------------------
        videos = page.locator("div[data-e2e='user-repost-item']")
        total = videos.count()

        print(f"[INFO] Total repost video ditemukan: {total}")

        repost_list = []

        # ---------------------------------------------------------
        # 4. SCRAPE SATU PER SATU
        # ---------------------------------------------------------
        for i in range(total):
            print(f"[INFO] Membuka repost ke-{i+1}/{total}…")

            videos.nth(i).click()
            page.wait_for_timeout(2500)

            # CEK jika video privat / tidak bisa dibuka
            if "video" not in page.url:
                print("[SKIP] Video privat / tidak bisa dibuka, dilewati.")
                page.go_back()
                page.wait_for_timeout(1500)
                continue

            video_url = page.url

            # ambil caption
            try:
                caption = page.locator("h1[data-e2e='video-caption']").inner_text(timeout=3000)
            except:
                caption = "(tanpa caption)"

            repost_list.append({
                "index": i + 1,
                "url": video_url,
                "caption": caption
            })

            print(f"[OK] {video_url}")

            page.go_back()
            page.wait_for_timeout(2000)

        # ---------------------------------------------------------
        # 5. OUTPUT
        # ---------------------------------------------------------
        print("\n===== LIST REPOST VIDEO =====")
        for v in repost_list:
            print(f"{v['index']}. {v['url']} | {v['caption']}")

        print("\n[INFO] Selesai.")
        input("\nENTER untuk keluar…")
        browser.close()


if __name__ == "__main__":
    main()
