#!/usr/bin/env python3
"""v22.0 補: a102=LIFF酒類購入の確認ダイアログ / a103=代理注文の件数バー（価格未設定・仕入専用品の非表示）"""
import json
import copy
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request


def main():
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections = {"orders": ORDERS2, "checkins": copy.deepcopy(CHECKINS), "reservations": rs}

    menu = json.loads(urllib.request.urlopen(BASE + "/api/menu").read())
    menu_ext = dict(menu)
    menu_ext["menu"] = {k: list(v) for k, v in menu.get("menu", {}).items()}
    menu_ext["menu"].setdefault("お菓子・小物", [])
    menu_ext["menu"]["お菓子・小物"] += [
        {"id": "MI-900101", "name": "ようかん（単品）", "price": 0, "emoji": "🍡",
         "category": "お菓子", "available": True},
        {"id": "MI-900102", "name": "仕入/おしぼりロール", "price": 120, "emoji": "🧻",
         "category": "小物", "available": True},
    ]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')

        # ── a102: LIFF 酒類購入の確認 ──
        ctx = browser.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=2,
                                  locale="ja-JP", timezone_id="Asia/Tokyo",
                                  extra_http_headers={"X-Scenario": "member"})
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE)
                  else r.fulfill(status=200, content_type="application/octet-stream", body=b""))
        p = ctx.new_page()
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2800)
        try:
            p.evaluate("_showAlcoholConsentDialog(); 1")
            p.wait_for_timeout(600)
            loc = p.locator('div[role="dialog"][aria-labelledby="alcTitle"]').first
            loc.screenshot(path=f"{OUT}/a102-liff-alcohol-consent.png", timeout=8000)
            print("shot: a102-liff-alcohol-consent")
        except Exception as e:
            print("FAIL a102", str(e)[:200])
        ctx.close()

        # ── a103: 代理注文の件数バー ──
        ctx2 = browser.new_context(viewport={"width": 1600, "height": 1400}, device_scale_factor=2,
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

        ctx2.route("**/*", route_ext)

        def menu_route(route):
            route.fulfill(content_type="application/json", body=json.dumps(menu_ext, ensure_ascii=False))
        ctx2.route("**/api/menu*", menu_route)

        ctx2.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx2.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx2.add_init_script(LEAFLET_STUB)
        ctx2.add_init_script(QRCODE_STUB)

        page = ctx2.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(3000)
        page.evaluate("const s=document.getElementById('globalHallSelect'); if(s){s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();} 1")
        page.wait_for_timeout(1500)
        try:
            page.evaluate("showPanel('proxy', document.querySelectorAll('.tab-btn')[4]); 1")
            page.wait_for_timeout(1200)
            page.select_option('#proxySP', 'SP-YT01')
            page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange(); 1")
            page.wait_for_timeout(1200)
            page.fill('#proxyBookingIdInput', 'TEST-2500200')
            page.evaluate("lookupProxyBookingId(); 1")
            page.wait_for_timeout(3500)
            st = page.locator('#proxyMenuStatus')
            txt = (st.text_content() or '').strip()
            print('proxyMenuStatus:', txt[:200])
            if '非表示' in txt:
                box = st.bounding_box()
                page.screenshot(path=f"{OUT}/a103-proxy-hidden-counts.png",
                                clip={"x": max(0, box["x"] - 14), "y": max(0, box["y"] - 12),
                                      "width": min(1600 - max(0, box["x"] - 14), box["width"] + 28),
                                      "height": box["height"] + 24})
                print("shot: a103-proxy-hidden-counts")
            else:
                print("SKIP a103: counts not shown")
        except Exception as e:
            print("FAIL a103", str(e)[:200])

        page.close()
        browser.close()


if __name__ == '__main__':
    main()
