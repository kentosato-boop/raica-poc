#!/usr/bin/env python3
"""v11.1: CRM内部タブ（LINEチャット/チケット/サブチケット/統計）＋staff権限ビュー＋外部API設定カード"""
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
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');sessionStorage.setItem('crmToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        # ── 1) CRM 内部タブ ──
        page = ctx.new_page()
        page.goto(BASE + "/crm.html")
        page.wait_for_timeout(3000)
        views = [
            ("lineChat", "navLineChat", "a84-crm-linechat"),
            ("tickets", "navTickets", "a85-crm-tickets"),
            ("subTickets", "navSubs", "a86-crm-subtickets"),
            ("stats", None, "a87-crm-stats"),
        ]
        for v, navid, name in views:
            try:
                if navid:
                    page.evaluate(f"showView('{v}', document.getElementById('{navid}'))")
                else:
                    page.evaluate(f"showView('{v}', [...document.querySelectorAll('.nav-item')].find(n=>n.textContent.includes('統計')))")
                page.wait_for_timeout(1800)
                page.screenshot(path=f"{OUT}/{name}.png")
                print("shot:", name)
            except Exception as e:
                print("FAIL", name, str(e)[:100])
        page.close()

        # ── 2) staff 権限のタブバー（予約・設定▾・ユーザーが非表示） ──
        def staff_route(route):
            route.fulfill(content_type="application/json", body=json.dumps({
                "success": True,
                "user": {"id": "U-002", "username": "staff01", "displayName": "スタッフ 太郎",
                         "role": "staff", "allowedHallIds": ["HALL-18YT"], "defaultSalesPointId": "SP-YT01"},
            }, ensure_ascii=False))

        ctx.route("**/api/admin/me", staff_route)
        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(3000)
        try:
            page.evaluate("const s=document.getElementById('globalHallSelect'); if(s){s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();}")
        except Exception:
            pass
        page.wait_for_timeout(1500)
        try:
            page.screenshot(path=f"{OUT}/a88-admin-staff-view.png", clip={"x": 0, "y": 0, "width": 1600, "height": 260})
            print("shot: a88-admin-staff-view")
        except Exception as e:
            print("FAIL a88", str(e)[:100])
        page.close()
        ctx.unroute("**/api/admin/me")

        # ── 3) 設定パネルの外部API設定カード（superadmin専用） ──
        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(3000)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(1200)
        try:
            page.evaluate("showPanel('settings', null)")
            page.wait_for_timeout(2000)
            box = page.evaluate("""(()=>{
              const card = document.getElementById('accountMgmtApiSettingsCard');
              if (!card || !card.offsetParent) return null;
              const prev = card.previousElementSibling;
              const r1 = (prev && prev.classList.contains('settings-card')) ? prev.getBoundingClientRect() : card.getBoundingClientRect();
              const r2 = card.getBoundingClientRect();
              card.scrollIntoView({block:'center'});
              return true;})()""")
            page.wait_for_timeout(600)
            box = page.evaluate("""(()=>{
              const card = document.getElementById('accountMgmtApiSettingsCard');
              if (!card || !card.offsetParent) return null;
              const prev = card.previousElementSibling;
              const top = (prev && prev.classList.contains('settings-card')) ? prev : card;
              const r1 = top.getBoundingClientRect(); const r2 = card.getBoundingClientRect();
              const x = Math.max(0, Math.min(r1.x, r2.x) - 8);
              const y = Math.max(0, Math.min(r1.y, r2.y) - 8);
              return {x, y, width: Math.min(1600 - x, Math.max(r1.right, r2.right) - x + 8),
                      height: Math.min(1100 - y, Math.max(r1.bottom, r2.bottom) - y + 8)};})()""")
            if box and box.get("height", 0) > 60:
                page.screenshot(path=f"{OUT}/a89-settings-extapi.png", clip=box)
                print("shot: a89-settings-extapi")
            else:
                print("FAIL a89: card not visible", box)
        except Exception as e:
            print("FAIL a89", str(e)[:120])
        page.close()

        browser.close()


if __name__ == '__main__':
    main()
