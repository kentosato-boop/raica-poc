#!/usr/bin/env python3
"""a71受付票・a52自動精算機ご利用票: document.writeの内容を記録→通常ページで描画して撮影"""
import json
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request

RECORDER = """
const _o = window.open.bind(window);
window.open = (...a) => {
  const w = _o(...a);
  window._slipW = w;
  if (w && w.document) {
    const _w = w.document.write.bind(w.document);
    w.document.write = (s) => { window.__writes = (window.__writes || []); window.__writes.push(String(s)); _w(s); };
  }
  return w;
};
"""


def render_and_shot(ctx, html, path, width=760):
    p2 = ctx.new_page()
    p2.set_viewport_size({"width": width, "height": 1100})
    p2.set_content(html, wait_until="domcontentloaded")
    p2.wait_for_timeout(1800)
    p2.screenshot(path=path, full_page=True)
    p2.close()
    print("saved:", path.split('/')[-1])


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

        # ── a71: 受付票（QRカード形式・1件=1ページ） ──
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(1400)
        page.evaluate(RECORDER)
        page.evaluate("window.__writes=[]; printReceptionList().catch(e=>window.__perr=String(e))")
        page.wait_for_timeout(3000)
        writes = page.evaluate("window.__writes || []")
        print("a71 writes:", len(writes), "err:", page.evaluate("window.__perr||''"))
        final = next((w for w in reversed(writes) if "card" in w and "qr-0" in w), None)
        if final:
            render_and_shot(ctx, final, f"{OUT}/a71-checkin-slip.png", width=700)
        try:
            page.evaluate("if(window._slipW)window._slipW.close()")
        except Exception:
            pass

        # ── a52: 自動精算機ご利用票（精算QR） ──
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1400)
        page.evaluate("window.__writes=[]")
        try:
            page.evaluate("generateSettlementQR('64260','783','JPY','喪主')")
            page.wait_for_timeout(3000)
            writes = page.evaluate("window.__writes || []")
            print("a52 writes:", len(writes))
            final = next((w for w in reversed(writes) if "QR" in w or "精算" in w), None)
            if final:
                render_and_shot(ctx, final, f"{OUT}/a52-settlement-slip.png", width=560)
        except Exception as e:
            print("FAIL a52", str(e)[:120])

        browser.close()


if __name__ == '__main__':
    main()
