#!/usr/bin/env python3
"""管理画面 追加状態の撮影（SAPエラー・在庫不具合・各モーダル・検索状態）"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, ORDERS, CHECKINS, ts, BASE, OUT)
from playwright.sync_api import sync_playwright
import urllib.request

TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()

# SAP失敗カードを追加
ORDERS2 = json.loads(json.dumps(ORDERS))
ORDERS2.append({"id": "O-006", "orderNumber": 6, "status": "ready_to_pay", "orderSource": "line", "date": TODAY,
    "hallId": "HALL-18YT", "hallName": "四ツ木斎場", "salesPointName": "控室", "qrLabel": "月の間2",
    "bookingId": "TEST-2500201", "total": 3300, "sapStatus": "error",
    "sapError": '代表品目分類 "17" の支払割当が見つかりません（品目: 3579）',
    "items": [{"emoji": "🍱", "name": "精進料理膳", "quantity": 1, "price": 3300}],
    "createdAt": {"__ms": ORDERS[0]["createdAt"]["__ms"] - 3600000}})

def main():
    rs = json.loads(urllib.request.urlopen(BASE + "/api/admin/reservations").read())["reservations"]
    for r in rs:
        r.setdefault("createdAt", ts(600))
    collections = {"orders": ORDERS2, "checkins": CHECKINS, "reservations": rs}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5,
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
                route.abort()

        ctx.route("**/*", route_ext)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def closemodals():
            page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay],.modal-overlay').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
            page.wait_for_timeout(200)

        page.goto(BASE + "/admin.html")
        page.wait_for_timeout(2500)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(800)

        # SAP失敗チップ + エラー詳細
        shot("a33-orders-sap-error-chip")
        try:
            page.click("text=⚠ SAP失敗", timeout=2500)
            page.wait_for_timeout(700)
            shot("a34-sap-error-modal")
            closemodals()
        except Exception as e:
            print("sap modal fail", e)
        # 日付ピッカー
        try:
            page.evaluate("openViewDatePicker()")
            page.wait_for_timeout(500)
            shot("a35-view-date-picker")
            closemodals()
        except Exception as e:
            print("datepicker fail", e)

        # 代理注文: 予約なし（お連れ様/得意先選択）
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[1])")
        page.wait_for_timeout(600)
        try:
            page.select_option('#proxySP', 'SP-YT03')
            page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
            page.wait_for_timeout(1000)
            page.click("text=🚶 予約なし", timeout=2500)
            page.wait_for_timeout(900)
            shot("a36-proxy-no-rsv-payer")
        except Exception as e:
            print("guest fail", e)
        # ピッカー行あり
        try:
            page.evaluate("resetProxyStep1&&resetProxyStep1()")
            page.click("text=📋 予約一覧から選ぶ", timeout=2500)
            page.wait_for_timeout(1000)
            shot("a37-proxy-rsv-picker-rows")
            closemodals()
        except Exception as e:
            print("picker rows fail", e)

        # 火葬確認: 検索
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(800)
        try:
            page.fill('#rsvSearchInput', '東博')
            page.wait_for_timeout(500)
            shot("a38-checkins-search")
            page.fill('#rsvSearchInput', '')
        except Exception as e:
            print("checkins search fail", e)

        # 部屋紐付け: 上書き警告
        page.evaluate("showPanel('roomAssignments',document.querySelectorAll('.tab-btn')[2])")
        page.wait_for_timeout(900)
        try:
            page.click("#raList button:has-text('紐付け')", timeout=2500)
            page.wait_for_timeout(800)
            shot("a39-ra-overwrite-warning")
            closemodals()
        except Exception as e:
            print("ra overwrite fail", e)

        # 事前同意: カナ検索ライブ
        page.evaluate("showPanel('preConsents',document.querySelectorAll('.tab-btn')[6])")
        page.wait_for_timeout(1000)
        try:
            page.fill('#pcSearchInput, input[id*=pcSearch]', 'とうはく')
        except Exception:
            try:
                page.evaluate("const i=[...document.querySelectorAll('#panelPreConsents input[type=text]')][0]; i.value='とうはく'; i.dispatchEvent(new Event('input'))")
            except Exception as e:
                print("kana input fail", e)
        page.wait_for_timeout(600)
        shot("a40-pc-kana-search")

        # お会計精算: 詳細展開→領収書分割
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(900)
        try:
            page.click("#panelPayment >> text=▼ 詳細 (3)", timeout=2500)
            page.wait_for_timeout(900)
            for label in ['領収書', '分割', '🧾']:
                try:
                    page.click(f"#panelPayment button:has-text('{label}')", timeout=1500)
                    page.wait_for_timeout(800)
                    shot("a41-receipt-split-modal")
                    closemodals()
                    break
                except Exception:
                    continue
        except Exception as e:
            print("receipt fail", e)

        # 在庫タブ（既知の不具合 E-5 の実証）
        try:
            page.evaluate("try{showPanelFromMenu('inventory')}catch(e){}")
            page.wait_for_timeout(800)
            shot("a42-inventory-broken")
        except Exception as e:
            print("inventory fail", e)

        # 斎場設定: 部屋管理・売上場所設定モーダル
        page.evaluate("showPanelFromMenu('halls')")
        page.wait_for_timeout(1100)
        try:
            page.click("#panelHalls button:has-text('部屋管理')", timeout=2500)
            page.wait_for_timeout(800)
            shot("a43-room-editor-modal")
            closemodals()
        except Exception as e:
            print("room editor fail", e)
        try:
            page.click("#panelHalls button:has-text('⚙')", timeout=2500)
            page.wait_for_timeout(800)
            shot("a44-sp-settings-modal")
            closemodals()
        except Exception as e:
            print("sp settings fail", e)

        browser.close()


if __name__ == '__main__':
    main()
