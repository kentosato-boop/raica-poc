#!/usr/bin/env python3
"""火葬同意フローのお客様導線を一気通貫で撮影（前日=事前同意 / 当日=火葬同意）"""
import datetime
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = "/tmp/claude-0/-home-user-raica-poc/42e3a875-5e6e-5197-9d02-6c0b7e5e05c7/scratchpad/shots"
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()

def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(f"{OUT}/btn", exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')

        def new_page(scenario="member"):
            ctx = browser.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=2,
                                      locale="ja-JP", timezone_id="Asia/Tokyo",
                                      extra_http_headers={"X-Scenario": scenario})
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE) else r.abort())
            p = ctx.new_page()
            p.on("pageerror", lambda e: print("PAGE-ERR:", str(e)[:150]))
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

        def el(p, sel, name, pad=None):
            hide_badges(p)
            try:
                loc = p.locator(sel).first
                loc.scroll_into_view_if_needed(timeout=2000)
                p.wait_for_timeout(150)
                loc.screenshot(path=f"{OUT}/btn/{name}.png", timeout=4000)
                print("el:", name)
            except Exception as e:
                print("EL-FAIL", name, str(e)[:80])

        # ── A) 前日: 事前同意フロー（mode=pre・新規ユーザー） ──
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?mode=pre&page=preconsent")
        p.wait_for_timeout(2200)
        shot(p, "j-pre-1-top")
        el(p, "#topBtn", "l-btn-pre-next2")
        p.click("text=申込にすすむ")
        p.wait_for_timeout(1500)
        shot(p, "j-pre-2-info-empty", full=True)
        # 入力
        p.select_option("#preHall", "HALL-18YT")
        p.fill("#preDate", TODAY)
        p.fill("#preDeceasedLast", "東博"); p.fill("#preDeceasedFirst", "太郎")
        p.fill("#preDeceasedLastKana", "とうはく"); p.fill("#preDeceasedFirstKana", "たろう")
        p.fill("#preAppLast", "東博"); p.fill("#preAppFirst", "花子")
        p.fill("#preAppLastKana", "とうはく"); p.fill("#preAppFirstKana", "はなこ")
        p.fill("#prePhone", "090-1234-5678")
        p.fill("#prePostal", "124-0012")
        p.fill("#preAddress", "東京都葛飾区立石8-1-1")
        p.select_option("#preRelationship", "子")
        p.wait_for_timeout(300)
        shot(p, "j-pre-3-info-filled", full=True)
        el(p, "#btnPreNext", "l-btn-pre-goterms")
        p.click("#btnPreNext")
        p.wait_for_timeout(1200)
        shot(p, "j-pre-4-consent-unchecked", full=True)
        el(p, "#masterAgreeLabel", "l-chk-master")
        el(p, "#btnAgree", "l-btn-agree-off")
        # マスターチェックON
        p.check("#checkAll")
        p.wait_for_timeout(400)
        shot(p, "j-pre-5-consent-checked")
        el(p, "#btnAgree", "l-btn-agree-on")
        p.click("#btnAgree")
        p.wait_for_timeout(1500)
        shot(p, "j-pre-6-complete")
        el(p, "#scrPreComplete button", "l-btn-close")
        ctx.close()

        # ── B) 友だち追加画面（未追加時に表示） ──
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?preview=friend")
        p.wait_for_timeout(1800)
        shot(p, "j-friend")
        el(p, "#btnAddFriend", "l-btn-addfriend")
        el(p, "#scrFriend .btn-outline", "l-btn-friend-recheck")
        ctx.close()

        # ── C) 当日: 火葬同意フロー（当日QR rsvId・未同意会員） ──
        ctx, p = new_page("unconsented")
        p.goto(BASE + "/index.html?rsvId=RSV-001&hallId=HALL-18YT")
        p.wait_for_timeout(2400)
        shot(p, "j-day-1-top")
        el(p, "#topDeceasedInfo", "l-sec-deceased2")
        el(p, "#topBtn", "l-btn-day-next2")
        p.click("text=同意にすすむ")
        p.wait_for_timeout(1500)
        shot(p, "j-day-2-consent", full=True)
        p.check("#checkAll")
        p.wait_for_timeout(400)
        shot(p, "j-day-3-consent-checked")
        p.click("#btnAgree")
        p.wait_for_timeout(2000)
        # 申込者情報が予約に無い → scrProfile へ誘導される
        shot(p, "j-day-4-profile", full=True)
        p.fill("#regName", "東博　花子")
        p.fill("#regKana", "とうはく　はなこ")
        p.fill("#regPhone", "090-1234-5678")
        p.fill("#regPostal", "124-0012")
        p.fill("#regAddress", "東京都葛飾区立石8-1-1")
        p.select_option("#regRelationship", "子")
        p.wait_for_timeout(300)
        shot(p, "j-day-5-profile-filled", full=True)
        el(p, "#btnRegister", "l-btn-register-go")
        p.click("#btnRegister")
        p.wait_for_timeout(1500)
        shot(p, "j-day-6-checkin-before")
        el(p, "#btnCheckin", "l-btn-checkin")
        p.click("#btnCheckin")
        p.wait_for_timeout(900)
        shot(p, "j-day-7-checkin-done")
        ctx.close()

        browser.close()


if __name__ == '__main__':
    main()
