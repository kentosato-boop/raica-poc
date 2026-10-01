#!/usr/bin/env python3
"""v22.0 補2: a104=注文詳細パネルの「🔍 SAP診断」セクション（展開状態）"""
import json
import copy
import time
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request


def main():
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    orders = copy.deepcopy(ORDERS2)
    now = int(time.time())
    for o in orders:
        if o.get("id") == "O-003":
            o.update({"sapStatus": "sent", "bookingId": "TEST-2500200", "sapPlantCode": "18YT",
                      "sapSentAt": {"_seconds": now - 3600},
                      "sapRequestBody": {"externalOrderId": "TEST-2500200", "plant": "18YT",
                                          "items": [{"materialCode": "3579", "quantity": 2}]}})
        if o.get("id") == "O-005":
            o.update({"sapStatus": "error", "checkinId": "CK-001", "bookingId": "TEST-2500200",
                      "sapPlantCode": "18YT", "sapSentAt": {"_seconds": now - 1800},
                      "sapError": "cartAdd failed: MATERIAL_NOT_IN_SLOC（保管場所に品目がありません）",
                      "sapRequestBody": {"externalOrderId": "TEST-2500200", "plant": "18YT",
                                          "items": [{"materialCode": "3581", "quantity": 2}]}})
    collections = {"orders": orders, "checkins": copy.deepcopy(CHECKINS), "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1800}, device_scale_factor=2,
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

        diag_orders = [
            {"id": "ORD-P1", "orderNumber": 12, "status": "billing", "sapStatus": "sent",
             "orderSource": "line", "checkinId": "CK-001", "bookingId": "TEST-2500200",
             "sapPlantCode": "18YT", "total": 4100, "sapSentAt": {"_seconds": now - 3600},
             "sapRequestBody": {"externalOrderId": "TEST-2500200", "plant": "18YT",
                                 "items": [{"materialCode": "3579", "quantity": 2},
                                            {"materialCode": "3709", "quantity": 1}]},
             "itemDetails": [
                 {"sapItemCode": "3579", "name": "ブレンドコーヒー", "quantity": 2, "price": 400,
                  "paymentGroupKey": "1", "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "飲料"},
                 {"sapItemCode": "3709", "name": "精進料理膳", "quantity": 1, "price": 3300,
                  "paymentGroupKey": "1", "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "飲料"}]},
            {"id": "ORD-P2", "orderNumber": 13, "status": "billing", "sapStatus": "error",
             "orderSource": "proxy", "checkinId": "CK-001", "bookingId": "TEST-2500200",
             "sapPlantCode": "18YT", "total": 1540, "sapSentAt": {"_seconds": now - 1800},
             "sapError": "cartAdd failed: MATERIAL_NOT_IN_SLOC（保管場所に品目がありません）",
             "sapRequestBody": {"externalOrderId": "TEST-2500200", "plant": "18YT",
                                 "items": [{"materialCode": "3601", "quantity": 2}]},
             "itemDetails": [
                 {"sapItemCode": "3601", "name": "瓶ビール（中瓶）", "quantity": 2, "price": 770,
                  "paymentGroupKey": "2", "thirdSalesSpecProductGroup": "2", "thirdSalesSpecProductGroupLabel": "酒類"}]},
        ]

        def diag_orders_route(route):
            route.fulfill(content_type="application/json",
                          body=json.dumps({"success": True, "orders": diag_orders}, ensure_ascii=False))
        ctx.route("**/api/admin/checkin/CK-001/orders", diag_orders_route)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(3000)
        page.evaluate("const s=document.getElementById('globalHallSelect'); if(s){s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();} 1")
        page.wait_for_timeout(1500)
        try:
            page.evaluate("openOrderDetailPanel('CK-001'); 1")
            page.wait_for_timeout(4000)
            opened = page.evaluate("""(()=>{
              const d=document.querySelector('details[id^=\"sapDiagSection_\"]');
              if(!d) return false; d.open=true; d.scrollIntoView({block:'center'}); return true;})()""")
            print('diag section found:', opened)
            page.wait_for_timeout(600)
            loc = page.locator('details[id^="sapDiagSection_"]').first
            loc.screenshot(path=f"{OUT}/a104-sap-diagnosis.png", timeout=8000)
            print("shot: a104-sap-diagnosis")
        except Exception as e:
            print("FAIL a104", str(e)[:300])

        page.close()
        browser.close()


if __name__ == '__main__':
    main()
