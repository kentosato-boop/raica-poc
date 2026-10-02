#!/usr/bin/env python3
"""撮影第3弾: 代理注文カート投入・予約確定モーダル・ピッカー行"""
import json, sys, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB,
                     ORDERS, CHECKINS, ts, BASE, OUT)
from playwright.sync_api import sync_playwright
import urllib.request

TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()

def main():
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections = {"orders": ORDERS, "checkins": CHECKINS, "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5,
                                  locale="ja-JP", timezone_id="Asia/Tokyo")

        def route_ext(route):
            url = route.request.url
            if "firebase-app-compat" in url:
                route.fulfill(content_type="application/javascript", body=FIREBASE_STUB)
            elif "firebase-firestore-compat" in url:
                route.fulfill(content_type="application/javascript", body="/* stub */")
            elif "qrcode.min.js" in url:
                route.fulfill(content_type="application/javascript", body=QRCODE_STUB)
            elif "xlsx.full.min.js" in url:
                route.fulfill(content_type="application/javascript", body=XLSX_STUB)
            elif url.startswith(BASE):
                route.continue_()
            else:
                route.abort()

        ctx.route("**/*", route_ext)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        page.goto(BASE + "/admin.html")
        page.wait_for_timeout(2500)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(800)

        # --- 代理注文: 紐付け→商品追加→カート/支払下部 ---
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[1])")
        page.wait_for_timeout(600)
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1200)
        page.fill('#proxyBookingIdInput', 'TEST-2500200')
        page.click("text=🔍 紐付け")
        page.wait_for_timeout(1200)
        # 商品を追加 (＋ボタン)
        plus = page.locator("#panelProxy button:has-text('＋'), #panelProxy button:has-text('+')")
        try:
            plus.nth(0).click(); page.wait_for_timeout(200)
            plus.nth(0).click(); page.wait_for_timeout(200)
            plus.nth(1).click(); page.wait_for_timeout(400)
        except Exception as e:
            print("plus fail", e)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        shot("a09-proxy-cart-bottom")
        shot("a09-proxy-full", full=True)

        # --- 予約タブ: 確定モーダル ---
        page.evaluate("window.scrollTo(0,0)")
        page.evaluate("showPanel('reservations',document.getElementById('tabReservations'))")
        page.wait_for_timeout(500)
        page.fill('#rsvTabFrom', TODAY)
        page.fill('#rsvTabTo', TODAY)
        page.evaluate("loadRsvTab()")
        page.wait_for_timeout(1000)
        shot("a12-reservations")
        try:
            page.click("#panelReservations button:has-text('📋確定')", timeout=3000)
            page.wait_for_timeout(800)
            shot("a13-rsv-confirm-modal")
        except Exception as e:
            print("rsv confirm fail:", e)

        browser.close()


if __name__ == '__main__':
    main()
