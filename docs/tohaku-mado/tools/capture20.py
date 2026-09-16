#!/usr/bin/env python3
"""v16.1: 注文詳細パネルの SAP金額サマリー（割引内訳・[別枠]キャッシュバック・支払者別明細）"""
import json
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request


def main():
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections = {"orders": ORDERS2, "checkins": CHECKINS, "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 2400}, device_scale_factor=2,
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
        page.wait_for_timeout(3000)
        page.evaluate("const s=document.getElementById('globalHallSelect'); if(s){s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();} 1")
        page.wait_for_timeout(1500)
        page.evaluate("openOrderDetailPanel('CK-001'); 1")
        page.wait_for_timeout(4000)

        # 1) SAP金額サマリー全体（totals + [別枠]CB + 支払者別カード + grandTotals）
        try:
            loc = page.locator('#orderDetailContent div[style*="background:#f0fdf4"]').first
            loc.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            loc.screenshot(path=f"{OUT}/a92-order-detail-money-summary.png", timeout=8000)
            print("shot: a92-order-detail-money-summary")
        except Exception as e:
            print("FAIL a92", str(e)[:200])

        # 2) 品目行の割引表示（打消し線 + 🏷 -¥ + SAP割引内訳ボックス）
        try:
            loc = page.locator('#orderDetailContent .order-detail-item').first
            loc.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            loc.screenshot(path=f"{OUT}/a93-order-detail-item-discount.png", timeout=8000)
            print("shot: a93-order-detail-item-discount")
        except Exception as e:
            print("FAIL a93", str(e)[:200])

        page.close()
        browser.close()


if __name__ == '__main__':
    main()
