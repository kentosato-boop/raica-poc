#!/usr/bin/env python3
"""拡大図（c-*）を要素単位で撮り直す（最新ソース対応）"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request

TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()


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
                route.abort()

        ctx.route("**/*", route_ext)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()
        page.goto(BASE + "/admin.html")
        page.wait_for_timeout(2500)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(1200)

        def el(sel, name, nth=0):
            try:
                loc = page.locator(sel).nth(nth)
                loc.scroll_into_view_if_needed(timeout=2500)
                page.wait_for_timeout(150)
                loc.screenshot(path=f"{OUT}/{name}.png", timeout=5000)
                print("crop:", name)
            except Exception as e:
                print("FAIL", name, str(e)[:80])

        # ヘッダー右側
        el(".topbar > div:last-child, header > div:last-child, #topbar", "c-topbar-right")
        # オーダー: SAP受注バー・列ヘッダー・カード
        el("#panelOrders > div:first-child", "c-sap-chips")
        for i, nm in enumerate(["c-col-pending", "c-col-preparing", "c-col-ready", "c-col-billing"]):
            el(".kanban-col .kanban-header", nm, nth=i)
        el(".order-card", "c-order-card")
        el(".order-card:has-text('SAP失敗')", "c-sap-error-card")

        # 代理注文
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[1])")
        page.wait_for_timeout(800)
        el("#panelProxy .settings-card, #panelProxy > div:first-child", "c-proxy-step0")
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1000)
        page.fill('#proxyBookingIdInput', 'TEST-2500200')
        page.click("text=🔍 紐付け")
        page.wait_for_timeout(1400)
        el("#proxyStep3 .s-row, #proxyStep3 > div:nth-child(2)", "c-proxy-filters")

        # 部屋紐付け
        page.evaluate("showPanel('roomAssignments',document.querySelectorAll('.tab-btn')[2])")
        page.wait_for_timeout(1000)
        page.wait_for_timeout(800)
        el("#raList .ra-group, #raList > div", "c-room-rows")

        # 予約
        page.evaluate("showPanel('reservations',document.getElementById('tabReservations'))")
        page.wait_for_timeout(600)
        page.fill('#rsvTabFrom', TODAY); page.fill('#rsvTabTo', TODAY)
        page.evaluate("loadRsvTab()")
        page.wait_for_timeout(1200)
        el("#panelReservations .pc-toolbar", "c-rsv-toolbar")
        el("#panelReservations table", "c-rsv-rows")

        # 火葬確認
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(1100)
        el("#panelCheckins .pc-toolbar", "c-checkins-toolbar")
        el("#rsvTableWrap table", "c-checkins-rows")

        # お会計精算
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1200)
        el("#panelPayment .settings-card:has-text('精算ロック管理')", "c-settlement-lock")
        el("#ckAwaiting > div", "c-payment-card")
        el(".kanban-col.col-completed", "c-payment-done-col")

        # 事前同意
        page.evaluate("showPanel('preConsents',document.querySelectorAll('.tab-btn')[6])")
        page.wait_for_timeout(1300)
        el("#panelPreConsents table", "c-pc-rows")

        # 会員 / 商品 / 斎場
        page.evaluate("showPanelFromMenu('members')")
        page.wait_for_timeout(1200)
        el("#panelMembers table, #panelMembers .s-list", "c-member-rows")
        page.evaluate("showPanelFromMenu('products')")
        page.wait_for_timeout(1300)
        el("#panelProducts .s-row, #panelProducts .settings-card > div", "c-product-filters")
        page.evaluate("showPanelFromMenu('halls')")
        page.wait_for_timeout(1300)
        el("#panelHalls .s-list, #panelHalls table", "c-hall-rows")

        browser.close()

        # ── LIFF 側 ──
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        lctx = browser.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=2,
                                   locale="ja-JP", timezone_id="Asia/Tokyo",
                                   extra_http_headers={"X-Scenario": "member"})
        lctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE) else r.abort())
        lp = lctx.new_page()
        lp.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        lp.wait_for_timeout(2500)
        lp.evaluate("""
          const db=document.getElementById('devBanner'); if(db)db.style.display='none';
          const mb=document.getElementById('modeBadge'); if(mb)mb.style.display='none';
          const hs=document.getElementById('headerStatus'); if(hs)hs.style.display='none';
        """)

        def lel(sel, name):
            try:
                loc = lp.locator(sel).first
                loc.scroll_into_view_if_needed(timeout=2500)
                lp.wait_for_timeout(150)
                loc.screenshot(path=f"{OUT}/{name}.png", timeout=5000)
                print("crop:", name)
            except Exception as e:
                print("FAIL", name, str(e)[:80])

        lp.evaluate("document.getElementById('nav').style.display='flex'")
        lel("#nav", "c-liff-footer-nav")
        lp.evaluate("goHistory()")
        lp.wait_for_timeout(1400)
        lel("#historyList", "c-liff-history-items")
        lp.evaluate("openFeeCheck()")
        lp.wait_for_timeout(1400)
        lel("#feeCheckList", "c-liff-fee-groups")
        browser.close()


if __name__ == '__main__':
    main()
