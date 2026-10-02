#!/usr/bin/env python3
"""v10.0: LIFF撮り直し（必須エラー・メール形式エラー・カート数量行）"""
import datetime
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = "/tmp/claude-0/-home-user-raica-poc/42e3a875-5e6e-5197-9d02-6c0b7e5e05c7/scratchpad/shots"
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()


def main():
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
              const hs=document.getElementById('headerStatus'); if(hs)hs.style.display='none';
            """)

        def shot(p, name, full=False):
            hide_badges(p)
            p.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        # ── A) 事前同意: 必須エラー・メール形式エラー ──
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?mode=pre&page=preconsent")
        p.wait_for_timeout(2200)
        p.click("text=申込にすすむ")
        p.wait_for_timeout(1500)
        # 空のまま「次へ（規約確認）」→ 必須エラーのトースト
        try:
            p.click("#btnPreNext")
            p.wait_for_timeout(600)
            shot(p, "l-pre-error-required")
        except Exception as e:
            print("FAIL required", str(e)[:90])
        p.wait_for_timeout(2500)
        # メール形式だけ誤り
        try:
            p.select_option("#preHall", "HALL-18YT")
            p.fill("#preDate", TODAY)
            p.fill("#preDeceasedLast", "東博"); p.fill("#preDeceasedFirst", "太郎")
            p.fill("#preDeceasedLastKana", "とうはく"); p.fill("#preDeceasedFirstKana", "たろう")
            p.fill("#preAppLast", "東博"); p.fill("#preAppFirst", "花子")
            p.fill("#preAppLastKana", "とうはく"); p.fill("#preAppFirstKana", "はなこ")
            p.fill("#prePhone", "090-1234-5678")
            p.fill("#preEmail", "hanako@")
            p.fill("#prePostal", "124-0012")
            p.fill("#preAddress", "東京都葛飾区立石8-1-1")
            p.select_option("#preRelationship", "子")
            p.click("#btnPreNext")
            p.wait_for_timeout(600)
            shot(p, "l-pre-error-email")
        except Exception as e:
            print("FAIL email", str(e)[:90])
        ctx.close()

        # ── B) カートの数量変更行 ──
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2500)
        try:
            p.evaluate("goOrder()")
            p.wait_for_timeout(1500)
            p.evaluate("""
              const items=allItems();
              S.cart={}; S.cart[items[0].id]=2; S.cart[items[2].id]=1;
              refreshCart(); renderMenu();
            """)
            p.wait_for_timeout(400)
            p.evaluate("toggleCart()")
            p.wait_for_timeout(600)
            hide_badges(p)
            p.locator(".cart-row").first.screenshot(path=f"{OUT}/btn/l-cart-item-qty.png")
            print("el: l-cart-item-qty")
            p.locator("#cartList").screenshot(path=f"{OUT}/btn/l-cart-list.png")
            print("el: l-cart-list")
        except Exception as e:
            print("FAIL cart", str(e)[:90])
        ctx.close()

        browser.close()


if __name__ == '__main__':
    main()
