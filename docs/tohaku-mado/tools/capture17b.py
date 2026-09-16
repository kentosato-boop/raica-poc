#!/usr/bin/env python3
"""v11.0: capture17の失敗分の撮り直し"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request

TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()


def main():
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections = {"orders": ORDERS2, "checkins": CHECKINS, "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1100}, device_scale_factor=2,
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
                route.fulfill(status=200, content_type="application/octet-stream", body=b"")

        ctx.route("**/*", route_ext)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        def newpage():
            p = ctx.new_page()
            p.goto(BASE + "/admin.html?noautoprint=1")
            p.wait_for_timeout(2800)
            p.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
            p.wait_for_timeout(1500)
            return p

        # 1) カード印刷（受付QRモーダル内）
        page = newpage()
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[2])")
        page.wait_for_timeout(1500)
        try:
            page.locator("#rsvTableWrap .rsv-qr-btn:has-text('QR')").first.click()
            page.wait_for_timeout(2000)
            btn = page.locator("button:has-text('カード印刷'):visible").first
            btn.screenshot(path=f"{OUT}/btn/k-btn-card-print.png", timeout=6000)
            print("ok: k-btn-card-print")
        except Exception as e:
            print("FAIL k-btn-card-print", str(e)[:100])
            try:
                info = page.evaluate("[...document.querySelectorAll('button')].filter(b=>b.offsetParent&&b.textContent.includes('印刷')).map(b=>b.textContent.trim())")
                print("  visible print buttons:", info)
            except Exception:
                pass
        page.close()

        # 2) 従業員ボタン＋a59（得意先なし予約）
        page = newpage()
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(900)
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1200)
        try:
            page.fill('#proxyBookingIdInput', 'TEST-2500201')
            page.click("text=🔍 紐付け")
            page.wait_for_timeout(2800)
            page.screenshot(path=f"{OUT}/a59-proxy-step2-nocust.png")
            print("shot: a59-proxy-step2-nocust")
        except Exception as e:
            print("FAIL a59", str(e)[:90])
        page.close()

        page = newpage()
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(900)
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1200)
        try:
            page.click("text=🚶 予約なし", timeout=3000)
            page.wait_for_timeout(1300)
            btn = page.locator("#panelProxy button:has-text('👔 従業員'):visible").first
            btn.scroll_into_view_if_needed(timeout=4000)
            page.wait_for_timeout(300)
            btn.screenshot(path=f"{OUT}/btn/p-btn-payer-employee.png")
            print("ok: p-btn-payer-employee")
        except Exception as e:
            print("FAIL p-btn-payer-employee", str(e)[:100])
            try:
                info = page.evaluate("[...document.querySelectorAll('#panelProxy button')].map(b=>({t:b.textContent.trim().slice(0,20), vis:!!b.offsetParent})).filter(x=>x.t.includes('従業員')||x.t.includes('喪主'))")
                print("  payer buttons:", info)
            except Exception:
                pass

        # 3) 予約番号QR読取モーダル（参考: 導線未接続のため直接起動）
        try:
            page.evaluate("openQrScanModal()")
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{OUT}/a80-qr-scan-modal.png")
            print("shot: a80-qr-scan-modal")
        except Exception as e:
            print("FAIL a80", str(e)[:80])
        page.close()

        browser.close()


if __name__ == '__main__':
    main()
