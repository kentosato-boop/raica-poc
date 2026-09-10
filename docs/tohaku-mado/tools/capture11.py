#!/usr/bin/env python3
"""LIFF部品の撮り直し: フッターメニュー個別／TOPカード／pickhall距離／ENバッジ非表示"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = "/tmp/claude-0/-home-user-raica-poc/42e3a875-5e6e-5197-9d02-6c0b7e5e05c7/scratchpad/shots"

def main():
    import os
    os.makedirs(f"{OUT}/btn", exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')

        def new_page(scenario="member"):
            ctx = browser.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=2,
                                      locale="ja-JP", timezone_id="Asia/Tokyo",
                                      extra_http_headers={"X-Scenario": scenario})
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE) else r.abort())
            p = ctx.new_page()
            return ctx, p

        def hide_badges(p):
            p.evaluate("""
              const db=document.getElementById('devBanner'); if(db)db.style.display='none';
              const mb=document.getElementById('modeBadge'); if(mb)mb.style.display='none';
              const hs=document.getElementById('headerStatus');
              if(hs&&/開発|DEV|プレビュー/.test(hs.textContent))hs.style.display='none';
            """)

        def shot(p, name, full=False):
            hide_badges(p)
            p.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def el(p, sel, name):
            hide_badges(p)
            try:
                loc = p.locator(sel).first
                loc.scroll_into_view_if_needed(timeout=2000)
                p.wait_for_timeout(150)
                loc.screenshot(path=f"{OUT}/btn/{name}.png", timeout=4000)
                print("el:", name)
            except Exception as e:
                print("EL-FAIL", name, str(e)[:80])

        # 1) 会員フロー: ホーム＋フッターメニュー個別
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2500)
        shot(p, "m-checkin-home")
        for nid, nm in [("navHome", "l-nav-home"), ("navOrder", "l-nav-order"),
                        ("navMyCart", "l-nav-mycart"), ("navHistory", "l-nav-history"),
                        ("navOfficial", "l-nav-official")]:
            p.evaluate(f"document.getElementById('{nid}').style.display='flex'")
            el(p, f"#{nid}", nm)
        # 斎場選択（距離つき）
        p.evaluate("""
          showPickHall([
            {id:'HALL-15MY',name:'町屋斎場',distanceM:420},{id:'HALL-16OC',name:'落合斎場',distanceM:860},
            {id:'HALL-17YY',name:'代々幡斎場',distanceM:1200},{id:'HALL-18YT',name:'四ツ木斎場',distanceM:150},
            {id:'HALL-19KR',name:'桐ヶ谷斎場',distanceM:2300},{id:'HALL-20HR',name:'堀ノ内斎場',distanceM:3100},
            {id:'HALL-21OH',name:'お花茶屋会館',distanceM:980}])
        """)
        p.wait_for_timeout(400)
        shot(p, "m-pickhall")
        ctx.close()

        # 2) TOPカード（ご利用のルール／各種お問合せ先）を丸ごと
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?mode=pre&page=preconsent")
        p.wait_for_timeout(2200)
        el(p, "#scrTop .card:has-text('ご利用のルール')", "l-sec-rules")
        el(p, "#scrTop .card:has-text('各種お問合せ先')", "l-sec-contacts")
        ctx.close()

        # 3) エンディングノート（プレビューバッジ非表示で）
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?preview=ending-note")
        p.wait_for_timeout(2000)
        shot(p, "m-ending-note", full=True)
        ctx.close()

        browser.close()


if __name__ == '__main__':
    main()
