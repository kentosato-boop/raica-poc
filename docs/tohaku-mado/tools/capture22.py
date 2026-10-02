#!/usr/bin/env python3
"""v18.0: 予約編集の0円品目「🔄 差替」候補（a96）とカート品目編集の「🔄 差替候補」（a97）"""
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
        if r.get("id") == "RSV-001":
            r["reservedItems"] = [{"sapItemCode": "200100", "name": "火葬料金（最上等）",
                                    "productGroup": "2", "quantity": 1, "price": 0}]
    collections = {"orders": ORDERS2, "checkins": copy.deepcopy(CHECKINS), "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1600}, device_scale_factor=2,
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

        def rsv_route(route):
            route.fulfill(content_type="application/json",
                          body=json.dumps({"success": True, "complete": True, "reservations": rs}, ensure_ascii=False))
        ctx.route("**/api/admin/reservations*", rsv_route)

        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(3000)
        page.evaluate("const s=document.getElementById('globalHallSelect'); if(s){s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();} 1")
        page.wait_for_timeout(1500)

        # ── a96: 予約編集の品目リスト（0円赤字 + 🔄差替 + 候補一覧） ──
        try:
            page.evaluate("showPanel('reservations', document.querySelectorAll('.tab-btn')[0]); 1")
            page.wait_for_timeout(1500)
            page.evaluate("openRsvEdit('RSV-001'); 1")
            page.wait_for_timeout(2000)
            page.evaluate("searchRsvItemReplace(0); 1")
            page.wait_for_timeout(1500)
            sec = page.evaluate("""(()=>{
              const list = document.getElementById('rsvItemList');
              const box = list.closest('div[style]') || list.parentElement;
              box.scrollIntoView({block:'center'});
              const r = box.getBoundingClientRect();
              return {x: Math.max(0,r.x-8), y: Math.max(0,r.y-40), width: Math.min(1600, r.width+16), height: Math.min(1550, r.height+56)};})()""")
            page.wait_for_timeout(400)
            page.screenshot(path=f"{OUT}/a96-rsv-item-replace.png", clip=sec)
            print("shot: a96-rsv-item-replace")
        except Exception as e:
            print("FAIL a96", str(e)[:200])

        # ── a97: カート品目の編集モーダル（差替候補一覧つき） ──
        try:
            page.evaluate("closeRsvEdit(); 1")
            page.wait_for_timeout(500)
            page.evaluate("editCartItem('CK-001','10','200100','火葬料金（最上等）',0,1,'2'); 1")
            page.wait_for_timeout(800)
            page.evaluate("searchCartItemReplace(); 1")
            page.wait_for_timeout(1500)
            loc = page.locator('#cartItemEditModal > div').first
            loc.screenshot(path=f"{OUT}/a97-cart-item-edit-replace.png", timeout=8000)
            print("shot: a97-cart-item-edit-replace")
        except Exception as e:
            print("FAIL a97", str(e)[:200])

        page.close()
        browser.close()


if __name__ == '__main__':
    main()
