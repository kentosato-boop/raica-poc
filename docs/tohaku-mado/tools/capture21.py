#!/usr/bin/env python3
"""v17.0: 支払い内訳確認モーダル（現金/売掛内訳・税込合計・SAPに渡る金額の断言行、⛔除外バナー）"""
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
    cks = copy.deepcopy(CHECKINS)
    for c in cks:
        if c["id"] == "CK-001":
            c["itemGroupAssignment"] = {"1": "mourner", "2": "funeral_account"}
            c["applicantName"] = "東博　一郎"
    collections = {"orders": ORDERS2, "checkins": cks, "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1900}, device_scale_factor=2,
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

        def open_modal(page):
            page.goto(BASE + "/admin.html?noautoprint=1")
            page.wait_for_timeout(3000)
            page.evaluate("const s=document.getElementById('globalHallSelect'); if(s){s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();} 1")
            page.wait_for_timeout(1500)
            page.evaluate("showPanel('payment', document.querySelectorAll('.tab-btn')[0]); 1")
            page.wait_for_timeout(1200)
            page.evaluate("confirmNotifyWithAssign('CK-001'); 1")
            page.wait_for_timeout(4500)

        # 1) 通常（成功）状態
        page = ctx.new_page()
        open_modal(page)
        try:
            loc = page.locator('#paymentSummaryModal > div').first
            loc.screenshot(path=f"{OUT}/a94-psm-detailed.png", timeout=8000)
            print("shot: a94-psm-detailed")
        except Exception as e:
            print("FAIL a94", str(e)[:200])
        page.close()

        # 2) SAP失敗注文あり（⛔ 除外バナー）
        def failed_orders_route(route):
            route.fulfill(content_type="application/json", body=json.dumps({
                "success": True,
                "orders": [
                    {"id": "ORD-P1", "status": "billing", "sapStatus": "success", "checkinId": "CK-001",
                     "itemDetails": [
                         {"sapItemCode": "3579", "name": "ブレンドコーヒー", "quantity": 2, "price": 400,
                          "paymentGroupKey": "1", "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "飲料"},
                         {"sapItemCode": "3709", "name": "精進料理膳", "quantity": 1, "price": 3300,
                          "paymentGroupKey": "1", "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "飲料"}]},
                    {"id": "ORD-P2", "status": "billing", "sapStatus": "success", "checkinId": "CK-001",
                     "itemDetails": [
                         {"sapItemCode": "3601", "name": "瓶ビール（中瓶）", "quantity": 2, "price": 770,
                          "paymentGroupKey": "2", "thirdSalesSpecProductGroup": "2", "thirdSalesSpecProductGroupLabel": "酒類"}]},
                    {"id": "ORD-P3", "status": "billing", "sapStatus": "error", "total": 860,
                     "checkinId": "CK-001",
                     "itemDetails": [
                         {"sapItemCode": "3581", "name": "オレンジジュース", "quantity": 2, "price": 430,
                          "paymentGroupKey": "1", "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "飲料"}]},
                ]}, ensure_ascii=False))

        ctx.route("**/api/admin/checkin/CK-001/orders", failed_orders_route)
        page = ctx.new_page()
        open_modal(page)
        try:
            loc = page.locator('#paymentSummaryModal > div').first
            loc.screenshot(path=f"{OUT}/a95-psm-sap-excluded.png", timeout=8000)
            print("shot: a95-psm-sap-excluded")
        except Exception as e:
            print("FAIL a95", str(e)[:200])
        page.close()

        browser.close()


if __name__ == '__main__':
    main()
