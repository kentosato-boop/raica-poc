#!/usr/bin/env python3
"""v22.0: 予約カードのマーク群/タイコウ不一致モーダル/参照モード/エラー明細/代理注文の非表示件数バー"""
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
        if r.get("id") == "RSV-001":
            r["reservationPattern"] = "cremation_only"
            r["confirmed"] = True
            r["lastSapConflict"] = {
                "at": {"_seconds": int(time.time()) - 1800},
                "source": "taikou-sync",
                "reason": "document_locked",
                "fields": [
                    {"key": "cremationTime", "current": "11:30", "incoming": "13:00"},
                    {"key": "funeralCompany", "current": "幕内祭典", "incoming": "幕内祭典 本社"},
                ],
            }
            r["editLock"] = {"locked": True, "code": "RESERVATION_EDIT_LOCKED",
                              "reasons": ["受付がお知らせ済みのため（金額の根拠を保護しています）"]}
    collections = {"orders": ORDERS2, "checkins": copy.deepcopy(CHECKINS), "reservations": rs}

    menu = json.loads(urllib.request.urlopen(BASE + "/api/products").read())
    extra = [
        {"sapItemCode": "900101", "name": "ようかん（単品）", "price": 0, "categoryCode": "お菓子", "code": "900101"},
        {"sapItemCode": "900102", "name": "仕入/おしぼりロール", "price": 120, "categoryCode": "小物", "code": "900102"},
    ]
    menu_ext = dict(menu)
    menu_ext["products"] = list(menu.get("products", [])) + extra
    menu_ext["items"] = menu_ext["products"]

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

        # ── a98: 予約カード（マーク群・タイコウ不一致バッジ入り） ──
        try:
            page.evaluate("showPanel('reservations', document.getElementById('tabReservations')); 1")
            page.wait_for_timeout(800)
            page.fill('#rsvTabFrom', '2026-10-01')
            page.fill('#rsvTabTo', '2026-10-01')
            page.evaluate("loadRsvTab(); 1")
            page.wait_for_timeout(2500)
            loc = page.locator('.rsv-compact[data-rsv-id="RSV-001"]').first
            loc.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            loc.screenshot(path=f"{OUT}/a98-rsv-card-marks.png", timeout=8000)
            print("shot: a98-rsv-card-marks")
        except Exception as e:
            print("FAIL a98", str(e)[:200])

        # ── a99: タイコウ不一致 詳細モーダル ──
        try:
            page.evaluate("openConflictDetail('RSV-001'); 1")
            page.wait_for_timeout(1200)
            loc = page.locator('#conflictDetailModal > div').first
            loc.screenshot(path=f"{OUT}/a99-taikou-conflict-modal.png", timeout=8000)
            print("shot: a99-taikou-conflict-modal")
            page.evaluate("closeConflictDetail(); 1")
        except Exception as e:
            print("FAIL a99", str(e)[:200])

        # ── a100: 実施済み予約の参照モード（ロックバナー＋事務項目だけ保存） ──
        try:
            page.evaluate("openRsvEdit('RSV-001'); 1")
            page.wait_for_timeout(2000)
            box = page.evaluate("""(()=>{
              const b=document.getElementById('rsvEditLockBanner');
              const btn=[...document.querySelectorAll('#rsvEditModal button')].find(x=>x.textContent.includes('事務項目だけ保存'));
              if(!b) return null;
              const r1=b.getBoundingClientRect();
              let r2=r1; if(btn){btn.scrollIntoView({block:'center'});}
              return true;})()""")
            page.wait_for_timeout(400)
            loc = page.locator('#rsvEditLockBanner')
            loc.scroll_into_view_if_needed()
            loc.screenshot(path=f"{OUT}/a100-rsv-readonly-banner.png", timeout=8000)
            print("shot: a100-rsv-readonly-banner")
            btn = page.locator('#rsvEditModal button', has_text='事務項目だけ保存').first
            btn.scroll_into_view_if_needed()
            btn.screenshot(path=f"{OUT}/btn/s-btn-clerical-save.png", timeout=6000)
            print("shot: btn/s-btn-clerical-save")
            page.evaluate("closeRsvEdit(); 1")
        except Exception as e:
            print("FAIL a100", str(e)[:200])

        # ── a101: エラー明細のバナー＋「この明細を外す」 ──
        def cart_err_route(route):
            route.fulfill(content_type="application/json", body=json.dumps({
                "success": True, "cart": {
                    "status": "SUCCESS", "externalOrderId": "TEST-2500200",
                    "items": [
                        {"lineNumber": 10, "materialCode": "3579", "text": "ブレンドコーヒー", "quantity": 2, "unit": "個",
                         "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "喪主",
                         "sapAmounts": {"grossAmount": 800, "discount": 0, "netAmount": 800, "netPriceAmount": 400,
                                          "taxAmount": 80, "totalAmount": 880}},
                        {"lineNumber": 20, "materialCode": "3581", "text": "オレンジジュース", "quantity": 2, "unit": "本",
                         "thirdSalesSpecProductGroup": "1", "thirdSalesSpecProductGroupLabel": "喪主",
                         "status": "ERROR", "errorMessage": "MATERIAL_NOT_IN_SLOC（保管場所に品目がありません）"},
                    ],
                }}, ensure_ascii=False))
        ctx.route("**/api/admin/checkin/CK-001/cart", cart_err_route)
        try:
            page.evaluate("openOrderDetailPanel('CK-001'); 1")
            page.wait_for_timeout(4000)
            loc = page.locator('#orderDetailContent .order-detail-item', has_text='オレンジジュース').first
            loc.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            loc.screenshot(path=f"{OUT}/a101-error-cart-item.png", timeout=8000)
            print("shot: a101-error-cart-item")
        except Exception as e:
            print("FAIL a101", str(e)[:200])
        ctx.unroute("**/api/admin/checkin/CK-001/cart")

        # ── a103: 代理注文の件数バー（価格未設定・仕入専用品の非表示） ──
        def menu_route(route):
            route.fulfill(content_type="application/json", body=json.dumps(menu_ext, ensure_ascii=False))
        ctx.route("**/api/products*", menu_route)
        ctx.route("**/api/admin/products*", menu_route)
        try:
            page.evaluate("showPanel('proxy', document.querySelectorAll('.tab-btn')[4]); 1")
            page.wait_for_timeout(1200)
            page.select_option('#proxySP', 'SP-YT01')
            page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange(); 1")
            page.wait_for_timeout(1200)
            page.fill('#proxyBookingIdInput', 'TEST-2500200')
            page.click("text=🔍 紐付け")
            page.wait_for_timeout(3000)
            st = page.locator('#proxyMenuStatus')
            txt = st.text_content() or ''
            print('proxyMenuStatus:', txt[:120])
            box = st.bounding_box()
            if box:
                page.screenshot(path=f"{OUT}/a103-proxy-hidden-counts.png",
                                clip={"x": max(0, box["x"] - 12), "y": max(0, box["y"] - 10),
                                      "width": min(1600, box["width"] + 24), "height": box["height"] + 20})
                print("shot: a103-proxy-hidden-counts")
        except Exception as e:
            print("FAIL a103", str(e)[:200])

        page.close()
        browser.close()


if __name__ == '__main__':
    main()
