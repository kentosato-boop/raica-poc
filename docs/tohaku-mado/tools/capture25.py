#!/usr/bin/env python3
"""v24.0: 設定メニュー展開/イベントログ/オーダー上部バー/全て提供済みに/代理注文の補足情報/任意金額品目"""
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
    menu_ext["menu"].setdefault("その他", [])
    menu_ext["menu"]["その他"].append(
        {"id": "MI-900110", "name": "お心づけ（任意金額）", "price": 1, "emoji": "🎁",
         "category": "その他", "available": True})

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

        def menu_route(route):
            route.fulfill(content_type="application/json", body=json.dumps(menu_ext, ensure_ascii=False))
        ctx.route("**/api/menu*", menu_route)

        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(3000)
        page.evaluate("const s=document.getElementById('globalHallSelect'); if(s){s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();} 1")
        page.wait_for_timeout(1500)

        # a105: 設定▾ ドロップダウン展開
        try:
            page.evaluate("document.getElementById('settingsDropdown').classList.add('open'); const m=document.getElementById('settingsMenu'); m.style.display='block'; 1")
            page.wait_for_timeout(400)
            dd = page.locator('#settingsDropdown')
            box = dd.bounding_box()
            mb = page.locator('#settingsMenu').bounding_box()
            x0 = min(box['x'], mb['x']) - 10; y0 = min(box['y'], mb['y']) - 8
            x1 = max(box['x'] + box['width'], mb['x'] + mb['width']) + 10
            y1 = max(box['y'] + box['height'], mb['y'] + mb['height']) + 10
            page.screenshot(path=f"{OUT}/a105-settings-dropdown.png",
                            clip={"x": max(0, x0), "y": max(0, y0), "width": x1 - x0, "height": y1 - y0})
            print("shot: a105")
            page.evaluate("document.getElementById('settingsMenu').style.display=''; document.getElementById('settingsDropdown').classList.remove('open'); 1")
        except Exception as e:
            print("FAIL a105", str(e)[:200])

        # a106: イベントログ（初期設定内）
        try:
            page.evaluate("showSettingsPanel('initial'); 1") if page.evaluate("typeof showSettingsPanel==='function'") else None
        except Exception:
            pass
        try:
            page.evaluate("""
              addLog('受付 #1 を作成しました','ok');
              addLog('予約 TEST-2500200 を確定しました','ok');
              addLog('ログインしました（管理者）','');
              addLog('SAP商品同期が完了しました（124件）','ok');
              1""")
            page.wait_for_timeout(300)
            el = page.locator('#eventLog')
            el.scroll_into_view_if_needed(timeout=5000)
            el.screenshot(path=f"{OUT}/a106-event-log.png", timeout=8000)
            print("shot: a106")
        except Exception as e:
            print("FAIL a106", str(e)[:200])

        # a107: オーダー上部バー全体（SAP受注チップ＋お会計済み件数）
        try:
            page.evaluate("showPanel('orders', document.querySelectorAll('.tab-btn')[3]); 1")
            page.wait_for_timeout(2000)
            bar = page.locator('#panelOrders > div').first
            bar.screenshot(path=f"{OUT}/a107-orders-topbar.png", timeout=8000)
            print("shot: a107")
        except Exception as e:
            print("FAIL a107", str(e)[:200])

        # a108: ✅ 全て提供済みに（お会計精算カード内）
        try:
            page.evaluate("showPanel('payment', document.querySelectorAll('.tab-btn')[5]); 1")
            page.wait_for_timeout(2500)
            btn = page.locator("button:has-text('✅ 全て提供済みに')").first
            btn.scroll_into_view_if_needed(timeout=8000)
            page.wait_for_timeout(300)
            box = btn.bounding_box()
            page.screenshot(path=f"{OUT}/a108-mark-all-served.png",
                            clip={"x": max(0, box['x'] - 160), "y": max(0, box['y'] - 70),
                                  "width": box['width'] + 320, "height": box['height'] + 110})
            print("shot: a108")
        except Exception as e:
            print("FAIL a108", str(e)[:200])

        # a110/a111: 代理注文
        try:
            page.evaluate("showPanel('proxy', document.querySelectorAll('.tab-btn')[4]); 1")
            page.wait_for_timeout(1200)
            page.select_option('#proxySP', 'SP-YT01')
            page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange(); 1")
            page.wait_for_timeout(1200)
            page.fill('#proxyBookingIdInput', 'TEST-2500200')
            page.evaluate("lookupProxyBookingId(); 1")
            page.wait_for_timeout(3500)
            lab = page.locator('#proxyLabel')
            lab.scroll_into_view_if_needed(timeout=6000)
            page.fill('#proxyLabel', '机1')
            page.fill('#proxyName', '東博 一郎')
            page.wait_for_timeout(300)
            b1 = page.locator('#proxyLabel').bounding_box()
            b3 = page.locator('#proxyReceiptName').bounding_box()
            x0 = min(b1['x'], b3['x']) - 14; y0 = b1['y'] - 56
            x1 = max(b1['x'] + b1['width'], b3['x'] + b3['width']) + 14
            y1 = max(b1['y'] + b1['height'], b3['y'] + b3['height']) + 14
            page.screenshot(path=f"{OUT}/a110-proxy-note-fields.png",
                            clip={"x": max(0, x0), "y": max(0, y0), "width": x1 - x0, "height": y1 - y0})
            print("shot: a110")
            card = page.locator("div.proxy-order-grid >> text=お心づけ（任意金額）").first
            card.scroll_into_view_if_needed(timeout=6000)
            page.wait_for_timeout(300)
            cb = page.evaluate("""(()=>{
              const els=[...document.querySelectorAll('.proxy-order-grid > *')];
              const t=els.find(e=>e.textContent.includes('お心づけ（任意金額）'));
              if(!t) return null; const r=t.getBoundingClientRect();
              return {x:r.x-8,y:r.y-8,width:r.width+16,height:r.height+16};})()""")
            if cb:
                page.screenshot(path=f"{OUT}/a111-proxy-manual-price.png", clip=cb)
                print("shot: a111")
            else:
                print("FAIL a111: card not found")
        except Exception as e:
            print("FAIL a110/a111", str(e)[:250])

        page.close()
        browser.close()


if __name__ == '__main__':
    main()
