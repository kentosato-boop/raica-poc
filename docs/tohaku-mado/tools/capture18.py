#!/usr/bin/env python3
"""v11.0: 9/3ビルドのLIFF全面撮り直し（journey・部品・新機能）"""
import datetime
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = "/tmp/claude-0/-home-user-raica-poc/42e3a875-5e6e-5197-9d02-6c0b7e5e05c7/scratchpad/mado/shots"
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
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE)
                      else r.fulfill(status=200, content_type="application/octet-stream", body=b""))
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

        def el(p, sel, name, to_btn=True):
            hide_badges(p)
            try:
                loc = p.locator(sel).first
                loc.scroll_into_view_if_needed(timeout=2500)
                p.wait_for_timeout(200)
                path = f"{OUT}/btn/{name}.png" if to_btn else f"{OUT}/{name}.png"
                loc.screenshot(path=path, timeout=4000)
                print("el:", name)
            except Exception as e:
                print("EL-FAIL", name, str(e)[:80])

        # ── A) 前日: 事前同意フロー ──
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?mode=pre&page=preconsent")
        p.wait_for_timeout(2600)
        shot(p, "j-pre-1-top")
        shot(p, "j-pre-1-top-full", full=True)
        el(p, "#topBtn", "l-btn-pre-next2")
        el(p, "#topRulesCard", "l-sec-rules")
        el(p, "#topContactsCard", "l-sec-contacts")
        p.click("#topBtn")
        p.wait_for_timeout(1800)
        shot(p, "j-pre-2-info-empty", full=True)
        # 必須エラー
        try:
            p.click("#btnPreNext")
            p.wait_for_timeout(600)
            shot(p, "l-pre-error-required")
            p.wait_for_timeout(2500)
        except Exception as e:
            print("FAIL pre-required", str(e)[:80])
        # 入力
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
        try:
            p.click("#btnPreNext")
            p.wait_for_timeout(600)
            shot(p, "l-pre-error-email")
            p.wait_for_timeout(2500)
        except Exception as e:
            print("FAIL pre-email", str(e)[:80])
        p.fill("#preEmail", "hanako@example.com")
        p.wait_for_timeout(300)
        shot(p, "j-pre-3-info-filled", full=True)
        el(p, "#btnPreNext", "l-btn-pre-goterms")
        p.click("#btnPreNext")
        p.wait_for_timeout(1400)
        shot(p, "j-pre-4-consent-unchecked", full=True)
        el(p, "#masterAgreeLabel", "l-chk-master")
        el(p, "#btnAgree", "l-btn-agree-off")
        p.check("#checkAll")
        p.wait_for_timeout(400)
        shot(p, "j-pre-5-consent-checked")
        el(p, "#btnAgree", "l-btn-agree-on")
        p.click("#btnAgree")
        p.wait_for_timeout(2000)
        shot(p, "j-pre-6-complete")
        el(p, "#scrPreComplete button", "l-btn-close")
        ctx.close()

        # ── B) 友だち追加画面 ──
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?preview=friend")
        p.wait_for_timeout(2000)
        shot(p, "j-friend")
        el(p, "#btnAddFriend", "l-btn-addfriend")
        ctx.close()

        # ── C) 当日: 火葬同意フロー ──
        ctx, p = new_page("unconsented")
        p.goto(BASE + "/index.html?rsvId=RSV-001&hallId=HALL-18YT")
        p.wait_for_timeout(2600)
        shot(p, "j-day-1-top")
        el(p, "#topDeceasedInfo", "l-sec-deceased2")
        el(p, "#topBtn", "l-btn-day-next2")
        p.click("#topBtn")
        p.wait_for_timeout(1600)
        shot(p, "j-day-2-consent", full=True)
        p.check("#checkAll")
        p.wait_for_timeout(400)
        shot(p, "j-day-3-consent-checked")
        p.click("#btnAgree")
        p.wait_for_timeout(2200)
        shot(p, "j-day-4-profile", full=True)
        p.fill("#regName", "東博　花子")
        p.fill("#regKana", "とうはく　はなこ")
        p.fill("#regPhone", "090-1234-5678")
        p.fill("#regEmail", "hanako@example.com")
        p.fill("#regPostal", "124-0012")
        p.fill("#regAddress", "東京都葛飾区立石8-1-1")
        p.select_option("#regRelationship", "子")
        p.wait_for_timeout(300)
        shot(p, "j-day-5-profile-filled", full=True)
        el(p, "#btnRegister", "l-btn-register-go")
        p.click("#btnRegister")
        p.wait_for_timeout(1800)
        shot(p, "j-day-6-checkin-before")
        el(p, "#btnCheckin", "l-btn-checkin")
        p.click("#btnCheckin")
        p.wait_for_timeout(1200)
        shot(p, "j-day-7-checkin-done")
        ctx.close()

        # ── D) 会員: ホーム・ナビ・注文・履歴・カート・料金 ──
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2800)
        shot(p, "m-checkin-home")
        p.evaluate("document.getElementById('nav').style.display='flex'")
        p.wait_for_timeout(300)
        el(p, "#nav", "c-liff-footer-nav", to_btn=False)
        el(p, "#navHome", "l-nav-home")
        el(p, "#navOrder", "l-nav-order")
        el(p, "#navMyCart", "l-nav-mycart")
        el(p, "#navHistory", "l-nav-history")
        el(p, "#navFacilityGuide", "l-nav-facility")
        # 注文メニュー
        try:
            p.click("#navOrder")
        except Exception:
            p.evaluate("goOrder()")
        p.wait_for_timeout(2000)
        shot(p, "m-order-menu")
        el(p, "#spInfoBar", "l-bar-location")
        el(p, "#catTabs", "l-cat-tabs-row")
        try:
            row = p.locator("#orderSearch").locator("xpath=ancestor::div[1]")
            row.screenshot(path=f"{OUT}/btn/l-search-row.png")
            print("el: l-search-row")
        except Exception as e:
            print("EL-FAIL l-search-row", str(e)[:70])
        # フリードリンクタブ
        try:
            p.click("text=フリードリンク", timeout=2500)
            p.wait_for_timeout(700)
            shot(p, "m-order-fd-tab")
            p.locator("#catTabs .tab, #catTabs button").first.click()
            p.wait_for_timeout(500)
        except Exception as e:
            print("FAIL fd-tab", str(e)[:70])
        # 商品モーダル
        try:
            p.click("text=ブレンドコーヒー", timeout=2500)
            p.wait_for_timeout(800)
            shot(p, "m-product-modal")
            p.evaluate("closeProductModal()")
            p.wait_for_timeout(400)
        except Exception as e:
            print("FAIL product-modal", str(e)[:70])
        # カートに追加（メニューカードの＋ボタンをUIで押す）
        added = 0
        try:
            plus = p.locator("#menuGrid button:has-text('＋'), #menuGrid .qty-plus, #menuGrid button:has-text('+')")
            n = min(plus.count(), 3)
            for i in range(n):
                plus.nth(0).click()
                p.wait_for_timeout(300)
                added += 1
        except Exception as e:
            print("cart add fail", str(e)[:70])
        print("cart added:", added)
        try:
            p.click("#cartHeader")
            p.wait_for_timeout(700)
            shot(p, "m-order-cart-open")
            el(p, "#cartHeader", "l-cart-item-qty")
            el(p, "#cartList", "l-cart-list")
            el(p, ".cart-bar button:has-text('注文を確定する')", "l-btn-order")
            el(p, "#cartHeader", "l-bar-cart")
        except Exception as e:
            print("FAIL cart-open", str(e)[:70])
        # 注文確定
        try:
            p.click("text=注文を確定する", timeout=2500)
            p.wait_for_timeout(2800)
            shot(p, "m-order-confirm")
        except Exception as e:
            print("FAIL order-confirm", str(e)[:70])
        # 履歴
        try:
            p.click("#navHistory")
            p.wait_for_timeout(1800)
            shot(p, "m-history")
            el(p, "#historyList", "c-liff-history-items", to_btn=False)
            try:
                hdr = p.locator("#historyList").locator("xpath=preceding-sibling::*[1]")
                pass
            except Exception:
                pass
            el(p, "text=📜 全履歴を見る", "l-hist-item-badge")
            p.click("text=📜 全履歴を見る", timeout=2500)
            p.wait_for_timeout(1500)
            shot(p, "m-history-all")
        except Exception as e:
            print("FAIL history", str(e)[:70])
        # 予約カート
        try:
            p.click("#navMyCart")
            p.wait_for_timeout(2000)
            shot(p, "m-mycart")
            el(p, "#myCartList .pill, #myCartList span", "l-pill-reservation")
        except Exception as e:
            print("FAIL mycart", str(e)[:70])
        # 料金確認
        try:
            p.click("#navHome")
            p.wait_for_timeout(1200)
            p.click("#btnFeeCheck", timeout=2500)
            p.wait_for_timeout(1800)
            shot(p, "m-feecheck")
            el(p, "#feeCheckSummary", "l-fee-summary")
            el(p, "#feeCheckList", "c-liff-fee-groups", to_btn=False)
        except Exception as e:
            print("FAIL feecheck", str(e)[:70])
        # 館内案内図
        try:
            p.click("#navFacilityGuide")
            p.wait_for_timeout(2200)
            shot(p, "m-facility-guide")
        except Exception as e:
            print("FAIL facility", str(e)[:70])
        ctx.close()

        # ── E) 未受付ホーム（案内バナー） ──
        ctx, p = new_page("precheckin")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2600)
        shot(p, "m-home-precheckin")
        ctx.close()

        # ── F) エラー・案内画面 ──
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?page=order")
        p.wait_for_timeout(1800)
        p.evaluate("show('scrNoQr')")
        p.wait_for_timeout(400)
        shot(p, "m-noqr")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-99")
        p.wait_for_timeout(2400)
        shot(p, "m-noassign")
        p.evaluate("""
          showPickHall([{id:'HALL-15MY',name:'町屋斎場'},{id:'HALL-16OC',name:'落合斎場'},
            {id:'HALL-17YY',name:'代々幡斎場'},{id:'HALL-18YT',name:'四ツ木斎場'},
            {id:'HALL-19KR',name:'桐ヶ谷斎場'},{id:'HALL-20HR',name:'堀ノ内斎場'},
            {id:'HALL-21OH',name:'お花茶屋会館'}])
        """)
        p.wait_for_timeout(500)
        shot(p, "m-pickhall")
        p.evaluate("show('scrAuthError')")
        p.wait_for_timeout(400)
        shot(p, "m-auth-error")
        ctx.close()

        browser.close()


if __name__ == '__main__':
    main()
