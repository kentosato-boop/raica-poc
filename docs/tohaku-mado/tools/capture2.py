#!/usr/bin/env python3
"""撮影第2弾: 斎場選択後の代理注文フル・火葬確認・予約確定・設定配下"""
import json, sys, time, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB,
                     ORDERS, CHECKINS, ts, BASE, OUT)
from playwright.sync_api import sync_playwright
import urllib.request

TODAY = datetime.date.today().isoformat()

def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ''
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
        page.on("pageerror", lambda e: print("PAGE-ERR:", str(e)[:200]))

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def closemodals():
            page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay],.modal-overlay').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
            page.wait_for_timeout(200)

        page.goto(BASE + "/admin.html")
        page.wait_for_timeout(2500)
        # 斎場を四ツ木に
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(800)

        if only in ('', 'proxy'):
            page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[1])")
            page.wait_for_timeout(600)
            page.select_option('#proxySP', 'SP-YT01')
            page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
            page.wait_for_timeout(1200)
            shot("a05b-proxy-step1-ready")
            try:
                page.click("text=📋 予約一覧から選ぶ", timeout=3000)
                page.wait_for_timeout(800)
                shot("a07-proxy-rsv-picker")
                page.click("button:has-text('この予約で進む'), button:has-text('選択')", timeout=2000)
            except Exception as e:
                print("picker fail:", e)
                closemodals()
                try:
                    page.fill('#proxyBookingIdInput', 'TEST-2500200')
                    page.click("text=🔍 紐付け", timeout=2000)
                except Exception as e2:
                    print("bookingid fail:", e2)
            page.wait_for_timeout(900)
            shot("a08-proxy-step2-payer")
            for label, nm in [("葬儀社", "a09-proxy-step3-funeral"), ]:
                try:
                    page.click(f"#panelProxy button:has-text('{label}')", timeout=2500)
                    page.wait_for_timeout(900)
                    shot(nm)
                except Exception as e:
                    print("payer fail", label, e)
            # add item to cart then shot cart
            try:
                page.click("#panelProxy button:has-text('ブレンドコーヒー')", timeout=2500)
                page.wait_for_timeout(400)
                page.click("#panelProxy button:has-text('ブレンドコーヒー')", timeout=1500)
                page.wait_for_timeout(400)
                shot("a09b-proxy-cart")
            except Exception as e:
                print("cart fail", e)

        if only in ('', 'checkins'):
            page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
            page.wait_for_timeout(900)
            shot("a14-checkins")
            try:
                page.click("label:has-text('未承諾のみ')", timeout=2000)
                page.wait_for_timeout(500)
                shot("a15-checkins-unconsent")
                page.click("label:has-text('未承諾のみ')", timeout=2000)
                page.wait_for_timeout(300)
            except Exception as e:
                print("unconsent fail", e)
            try:
                page.click("#panelCheckins button:has-text('QR')", timeout=2500)
                page.wait_for_timeout(800)
                shot("a16-checkin-qr-modal")
                closemodals()
            except Exception as e:
                print("qr fail", e)

        if only in ('', 'rsv'):
            page.evaluate("showPanel('reservations',document.getElementById('tabReservations'))")
            page.wait_for_timeout(500)
            try:
                page.fill('#rsvTabFrom', TODAY)
                page.fill('#rsvTabTo', TODAY)
                page.evaluate("loadRsvTab()")
                page.wait_for_timeout(900)
                shot("a12-reservations")
                page.click("#panelReservations button:has-text('確定')", timeout=2500)
                page.wait_for_timeout(700)
                shot("a13-rsv-confirm-modal")
                closemodals()
            except Exception as e:
                print("rsv fail", e)

        if only in ('', 'settings'):
            page.click('#tabSettingsMenu')
            page.wait_for_timeout(400)
            shot("a20-settings-dropdown")
            for panel, nm in [("settings", "a21-settings"), ("members", "a22-members"), ("products", "a23-products"),
                              ("customers", "a24-customers"), ("halls", "a25-halls"), ("users", "a26-users"), ("qr", "a27-qr")]:
                try:
                    page.evaluate(f"showPanelFromMenu('{panel}')")
                    page.wait_for_timeout(1100)
                    shot(nm)
                except Exception as e:
                    print("panel fail", panel, e)
            # QR生成の実行例
            try:
                page.evaluate("showPanelFromMenu('qr')")
                page.wait_for_timeout(600)
                page.click("#panelQr button:has-text('QR生成'), button:has-text('QR生成')", timeout=2500)
                page.wait_for_timeout(900)
                shot("a28-qr-generated")
            except Exception as e:
                print("qr gen fail", e)

        if only in ('', 'payment'):
            page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
            page.wait_for_timeout(1000)
            shot("a17-payment-kanban")

        browser.close()


if __name__ == '__main__':
    main()
