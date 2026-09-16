#!/usr/bin/env python3
"""代理注文 STEP2（購入者を選択）と関連ボタンの撮影"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request

def main():
    import os
    os.makedirs(f"{OUT}/btn", exist_ok=True)
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections = {"orders": ORDERS2, "checkins": CHECKINS, "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5,
                                  locale="ja-JP", timezone_id="Asia/Tokyo")

        def route_ext(route):
            url = route.request.url
            if "firebase-app-compat" in url:
                route.fulfill(content_type="application/javascript", body=FIREBASE_STUB)
            elif "firebase-firestore-compat" in url:
                route.fulfill(content_type="application/javascript", body="/*s*/")
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
        page.goto(BASE + "/admin.html")
        page.wait_for_timeout(2500)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(900)

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def el(sel, name):
            try:
                loc = page.locator(sel).first
                loc.scroll_into_view_if_needed(timeout=2500)
                page.wait_for_timeout(150)
                loc.screenshot(path=f"{OUT}/btn/{name}.png", timeout=4000)
                print("el:", name)
            except Exception as e:
                print("EL-FAIL", name, str(e)[:90])

        # 代理注文へ
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[1])")
        page.wait_for_timeout(700)
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1000)
        # 予約番号で紐付け → STEP2が開く
        page.fill('#proxyBookingIdInput', 'TEST-2500200')
        page.click("text=🔍 紐付け")
        page.wait_for_timeout(1400)
        shot("a48-proxy-step2-payer", full=True)
        el("#proxyStep2", "p-sec-step2")
        for sel, nm in [("#proxyStep2Buttons button:has-text('葬儀社')", "p-btn-payer-funeral"),
                        ("#payerMournerBtn", "p-btn-payer-mourner"),
                        ("#payerGuestBtn", "p-btn-payer-guest"),
                        ("#payerEmployeeBtn", "p-btn-payer-employee")]:
            el(sel, nm)
        # 喪主を選ぶ → STEP3
        try:
            page.click("#payerMournerBtn", timeout=3000)
            page.wait_for_timeout(1300)
            shot("a49-proxy-step3-items", full=True)
        except Exception as e:
            print("payer click fail", str(e)[:90])

        browser.close()


if __name__ == '__main__':
    main()
