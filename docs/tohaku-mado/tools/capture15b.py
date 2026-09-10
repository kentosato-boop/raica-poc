#!/usr/bin/env python3
"""v10.0: a66トースト撮り直し＋a71受付票（トークンAPI修正後）"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request, os

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

        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(2500)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(1500)

        # a66: 成功トースト（本文に絵文字を含めない）
        try:
            page.evaluate("toast('振り分けを保存しました','ok',60000)")
            page.wait_for_timeout(500)
            page.locator("#toastZone").screenshot(path=f"{OUT}/a66-toast-ok.png")
            print("ok: a66-toast-ok")
            page.evaluate("document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove())")
        except Exception as e:
            print("FAIL a66", str(e)[:90])

        # a71: 受付票印刷（ポップアップ）
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(1400)
        try:
            with ctx.expect_page(timeout=8000) as pop_info:
                page.locator("button:has-text('受付票印刷')").first.click()
            pop = pop_info.value
            pop.wait_for_timeout(2800)
            import base64 as _b64
            cdp = ctx.new_cdp_session(pop)
            res = cdp.send("Page.captureScreenshot", {"captureBeyondViewport": True})
            open(f"{OUT}/a71-checkin-slip.png", "wb").write(_b64.b64decode(res["data"]))
            print("shot: a71-checkin-slip")
            pop.close()
        except Exception as e:
            print("FAIL a71", str(e)[:120])

        browser.close()


if __name__ == '__main__':
    main()
