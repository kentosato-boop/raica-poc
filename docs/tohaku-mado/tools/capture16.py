#!/usr/bin/env python3
"""v10.0: LIFF追加ショット（入力エラー・数量変更・未入力案内・履歴バッジ）"""
import datetime
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = "/tmp/claude-0/-home-user-raica-poc/42e3a875-5e6e-5197-9d02-6c0b7e5e05c7/scratchpad/shots"
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()


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
              const hs=document.getElementById('headerStatus'); if(hs)hs.style.display='none';
            """)

        def shot(p, name, full=False):
            hide_badges(p)
            p.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def el(p, sel, name):
            hide_badges(p)
            try:
                loc = p.locator(sel).first
                loc.scroll_into_view_if_needed(timeout=2500)
                p.wait_for_timeout(200)
                loc.screenshot(path=f"{OUT}/btn/{name}.png", timeout=4000)
                print("el:", name)
            except Exception as e:
                print("EL-FAIL", name, str(e)[:80])

        # ── A) 事前同意: 必須エラー表示 ──
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?mode=pre&page=preconsent")
        p.wait_for_timeout(2200)
        try:
            p.click("text=申込にすすむ")
            p.wait_for_timeout(1500)
            p.click("#btnPreNext")
            p.wait_for_timeout(800)
            shot(p, "l-pre-error-required")
        except Exception as e:
            print("FAIL l-pre-error", str(e)[:90])
        # メール形式エラー
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
            p.wait_for_timeout(800)
            shot(p, "l-pre-error-email")
        except Exception as e:
            print("FAIL l-pre-error-email", str(e)[:90])
        ctx.close()

        # ── B) 申込者情報が未入力のホーム（案内バナー付き） ──
        ctx, p = new_page("precheckin")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2500)
        shot(p, "m-home-precheckin")
        ctx.close()

        # ── C) カートの数量変更・履歴バッジ ──
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2500)
        try:
            p.evaluate("goOrder()")
            p.wait_for_timeout(1500)
            # 商品をカートに追加（＋を2回）
            cards = p.locator(".menu-item, .product-card")
            cards.first.click()
            p.wait_for_timeout(700)
            p.locator("button:has-text('＋'), .qty-plus").first.click()
            p.wait_for_timeout(400)
            p.locator("button:has-text('＋'), .qty-plus").first.click()
            p.wait_for_timeout(400)
            # モーダルを閉じる（×）
            try:
                p.locator("button:has-text('×'), .modal-close").first.click()
                p.wait_for_timeout(500)
            except Exception:
                p.keyboard.press("Escape")
            # カートバーを開く
            p.locator("#cartBar, .cart-bar").first.click()
            p.wait_for_timeout(800)
            shot(p, "m-cart-qty-open")
            el(p, ".cart-item, #cartItems > div", "l-cart-item-qty")
        except Exception as e:
            print("FAIL cart-qty", str(e)[:90])
        # 履歴の状態バッジ
        try:
            p.evaluate("goHistory()")
            p.wait_for_timeout(1500)
            el(p, "#historyList .hist-item, #historyList > div", "l-hist-item-badge")
        except Exception as e:
            print("FAIL hist badge", str(e)[:90])
        ctx.close()

        # ── D) TOP: ご利用のルール・お問合せ先を開いた状態（前日TOPの下部） ──
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?mode=pre&page=preconsent")
        p.wait_for_timeout(2200)
        shot(p, "j-pre-1-top-full", full=True)
        ctx.close()

        browser.close()


if __name__ == '__main__':
    main()
