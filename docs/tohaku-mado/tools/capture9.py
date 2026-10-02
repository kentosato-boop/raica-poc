#!/usr/bin/env python3
"""LIFFのボタン・部品単位の要素撮影"""
import os
from playwright.sync_api import sync_playwright
BASE="http://127.0.0.1:8787"
OUT=os.path.join(os.environ.get("SHOTS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")), "btn")
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    def new_page(scenario="member"):
        ctx = browser.new_context(viewport={"width":430,"height":932}, device_scale_factor=2,
                                  locale="ja-JP", timezone_id="Asia/Tokyo",
                                  extra_http_headers={"X-Scenario": scenario})
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE) else r.abort())
        return ctx, ctx.new_page()
    ok=0
    def el(p, sel, name, nth=0):
        global ok
        try:
            loc=p.locator(sel).nth(nth)
            loc.scroll_into_view_if_needed(timeout=2000)
            p.wait_for_timeout(120)
            loc.screenshot(path=f"{OUT}/{name}.png", timeout=4000)
            ok+=1; print("el:", name)
        except Exception as e:
            print("EL-FAIL", name, str(e)[:80])
    # 前日TOP
    ctx,p = new_page("new"); p.goto(BASE+"/index.html?mode=pre&page=preconsent"); p.wait_for_timeout(2000)
    el(p, "button:has-text(\'申込にすすむ\')", "l-btn-pre-next")
    el(p, "text=ご利用のルール", "l-sec-rules")
    el(p, "text=各種お問合せ先", "l-sec-contacts")
    p.click("text=申込にすすむ"); p.wait_for_timeout(1200)
    el(p, "button:has-text(\'住所検索\')", "l-btn-zip")
    el(p, "select", "l-select-hall")
    ctx.close()
    # 当日TOP→同意
    ctx,p = new_page("unconsented"); p.goto(BASE+"/index.html?rsvId=RSV-001&hallId=HALL-18YT"); p.wait_for_timeout(2200)
    el(p, "button:has-text(\'同意にすすむ\')", "l-btn-day-next")
    el(p, "text=故人氏名", "l-sec-deceased")
    p.click("text=同意にすすむ"); p.wait_for_timeout(1100)
    el(p, "input[type=checkbox]", "l-chk-consent")
    for t in ["同意して次へ","同意する","同意して進む"]:
        try:
            p.locator(f"button:has-text(\'{t}\')").nth(0).screenshot(path=f"{OUT}/l-btn-agree.png"); print("el: l-btn-agree"); ok+=1; break
        except Exception: pass
    ctx.close()
    # 注文フロー
    ctx,p = new_page("member"); p.goto(BASE+"/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01"); p.wait_for_timeout(2500)
    el(p, "#qrInfoBar", "l-bar-location")
    for t in ["受付する","火葬申込をする"]:
        try:
            p.locator(f"button:has-text(\'{t}\')").nth(0).screenshot(path=f"{OUT}/l-btn-checkin.png"); print("el: l-btn-checkin"); ok+=1; break
        except Exception: pass
    p.evaluate("show(\'scrOrder\');renderCatTabs();renderMenu();refreshCart();"); p.wait_for_timeout(700)
    el(p, ".cat-tabs, #catTabs", "l-cat-tabs-row")
    el(p, "text=申込者情報を入力する", "l-btn-profile-banner")
    p.evaluate("const it=allItems(); S.cart={}; S.cart[it[0].id]=2; refreshCart(); renderMenu();"); p.wait_for_timeout(400)
    el(p, "#cartHeader", "l-bar-cart")
    p.evaluate("toggleCart()"); p.wait_for_timeout(400)
    for t in ["注文を確定する"]:
        try:
            p.locator(f"button:has-text(\'{t}\')").nth(0).screenshot(path=f"{OUT}/l-btn-order.png"); print("el: l-btn-order"); ok+=1; break
        except Exception: pass
    el(p, "#navHome", "l-nav-home")
    el(p, "#navOrder", "l-nav-order")
    el(p, ".nav-btn:has-text(\'予約カート\')", "l-nav-mycart")
    el(p, ".nav-btn:has-text(\'履歴\')", "l-nav-history")
    el(p, ".nav-btn:has-text(\'公式\')", "l-nav-official")
    p.evaluate("goMyCart()"); p.wait_for_timeout(1100)
    el(p, "text=予約品目", "l-pill-reservation")
    p.evaluate("openFeeCheck()"); p.wait_for_timeout(1100)
    el(p, "text=喪主払い合計", "l-fee-summary")
    ctx.close()
    print("TOTAL-OK", ok)
    browser.close()

