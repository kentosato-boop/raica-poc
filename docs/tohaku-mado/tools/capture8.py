#!/usr/bin/env python3
"""ボタン・部品単位の要素スクリーンショット（管理画面＋LIFF）"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, ORDERS, CHECKINS, ts, BASE, OUT)
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
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=2,
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
        page.wait_for_timeout(900)

        ok = 0
        def el(sel, name, nth=0, pad=6):
            nonlocal ok
            try:
                loc = page.locator(sel)
                loc = loc.nth(nth)
                loc.scroll_into_view_if_needed(timeout=2000)
                page.wait_for_timeout(120)
                loc.screenshot(path=f"{OUT}/btn/{name}.png", timeout=4000)
                ok += 1
                print("el:", name)
            except Exception as e:
                print("EL-FAIL", name, str(e)[:80])

        import os
        os.makedirs(f"{OUT}/btn", exist_ok=True)

        # ナビタブ個別
        tabs = [("オーダー", "tab-orders"), ("代理注文", "tab-proxy"), ("部屋紐付け", "tab-rooms"),
                ("予約", "tab-rsv"), ("火葬確認", "tab-checkins"), ("お会計精算", "tab-payment"),
                ("事前同意", "tab-preconsents"), ("設定", "tab-settings")]
        for label, nm in tabs:
            el(f".tab-btn:has-text('{label}')", nm)

        # オーダー画面のボタン群
        el("button:has-text('👨‍🍳 調理開始')", "o-btn-cook")
        el("button:has-text('🍽️ 提供済み')", "o-btn-served")
        el(".kanban-card button:has-text('✕'), button.s-btn-red:has-text('✕')", "o-btn-cancel")
        el("button:has-text('お会計準備完了')", "o-btn-ready-to-pay")
        el("button:has-text('お会計済み')", "o-btn-paid")
        el("button:has-text('✏')", "o-btn-edit")
        el("button:has-text('注文詳細')", "o-btn-detail")
        el("button:has-text('SAP再送')", "o-btn-sap-retry")
        el("button:has-text('送信内容')", "o-btn-sap-payload")
        el("#sapOrderRetryAllBtn", "o-btn-retry-all")
        el("button:has-text('提供済みに戻す')", "o-btn-back-served")
        # 列ヘッダー
        for i, nm in enumerate(["o-col-pending", "o-col-preparing", "o-col-ready", "o-col-billing"]):
            el(".kanban-col-header, .kanban-column h3, .col-header", nm, nth=i)

        # 代理注文
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[1])")
        page.wait_for_timeout(700)
        el("#panelProxy button:has-text('デフォルト保存')", "p-btn-save-default")
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1100)
        el("#panelProxy button:has-text('紐付け')", "p-btn-link")
        el("#panelProxy >> text=📋 予約一覧から選ぶ", "p-btn-from-list")
        el("#panelProxy >> text=🚶 予約なし", "p-btn-no-rsv")
        page.fill('#proxyBookingIdInput', 'TEST-2500200')
        page.click("text=🔍 紐付け")
        page.wait_for_timeout(1100)
        el("#panelProxy button:has-text('✕ クリア'), #panelProxy button:has-text('×クリア'), #panelProxy button:has-text('クリア')", "p-btn-clear")
        el("#panelProxy button:has-text('＋'), #panelProxy button:has-text('+')", "p-btn-plus")
        el("#panelProxy button:has-text('−'), #panelProxy button:has-text('-')", "p-btn-minus")
        try:
            page.locator("#panelProxy button:has-text('＋'), #panelProxy button:has-text('+')").nth(0).click()
            page.wait_for_timeout(400)
        except Exception:
            pass
        el("button:has-text('注文を送信')", "p-btn-submit")

        # 部屋紐付け
        page.evaluate("showPanel('roomAssignments',document.querySelectorAll('.tab-btn')[2])")
        page.wait_for_timeout(900)
        el("#panelRoomAssignments button:has-text('🔄 再読込'), button:has-text('再読込')", "r-btn-reload")
        el("#raList button:has-text('紐付け')", "r-btn-assign")
        el("#raList button:has-text('解除')", "r-btn-release")
        el(".ra-fd", "r-fd-badge")

        # 予約
        page.evaluate("showPanel('reservations',document.getElementById('tabReservations'))")
        page.wait_for_timeout(500)
        page.fill('#rsvTabFrom', TODAY)
        page.fill('#rsvTabTo', TODAY)
        page.evaluate("loadRsvTab()")
        page.wait_for_timeout(1000)
        el("#panelReservations button:has-text('📋確定')", "v-btn-confirm")
        el("#panelReservations >> text=✅確定済", "v-btn-confirmed")

        # 火葬確認
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(900)
        el("#panelCheckins label:has-text('未承諾のみ')", "k-toggle-unconsent")
        el("#panelCheckins button:has-text('🔍 検索')", "k-btn-search")
        el("#panelCheckins button:has-text('再読込')", "k-btn-reload")
        el("#panelCheckins button:has-text('受付票印刷')", "k-btn-print")
        el("#panelCheckins button:has-text('QR')", "k-btn-qr")
        el("#panelCheckins button:has-text('LINE申込を検索')", "k-btn-line-search")
        el("#panelCheckins >> text=承諾", "k-badge-ok")
        el("#panelCheckins >> text=未承諾", "k-badge-ng")

        # お会計精算
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1000)
        el("#panelPayment button:has-text('✅ 受付')", "y-btn-checkin")
        el("#panelPayment button:has-text('支払い準備完了')", "y-btn-ready")
        el("#panelPayment button:has-text('割引')", "y-btn-discount")
        el("#panelPayment button:has-text('支払い済み')", "y-btn-paid")
        el("#panelPayment >> text=▼ 詳細 (3)", "y-btn-detail")
        el("#panelPayment button:has-text('全て提供済みに')", "y-btn-serve-all")
        el("#panelPayment button:has-text('状態確認')", "y-btn-lock-check")
        el("#panelPayment >> text=🔥 火葬同意済", "y-badge-consent-ok")
        el("#panelPayment >> text=⚠ 火葬未同意", "y-badge-consent-ng")

        # 事前同意
        page.evaluate("showPanel('preConsents',document.querySelectorAll('.tab-btn')[6])")
        page.wait_for_timeout(1100)
        el("#panelPreConsents button:has-text('紐付け')", "c-btn-link")
        el("#panelPreConsents button:has-text('🔍 検索'), #panelPreConsents button:has-text('検索')", "c-btn-search")
        el("#pcStatusFilter", "c-filter-status")

        # 設定配下の各セクション（初期設定フルページから section 単位）
        page.evaluate("showPanelFromMenu('settings')")
        page.wait_for_timeout(1200)
        for kw, nm in [("リッチメニュー", "s-sec-richmenu"), ("Webhook", "s-sec-webhook"),
                       ("会員情報登録", "s-sec-member-api"), ("SAP連携", "s-sec-sap"),
                       ("イベントログ", "s-sec-eventlog"), ("APIキー", "s-sec-apikey"),
                       ("場所", "s-sec-rooms"), ("味バリエーション", "s-sec-flavor")]:
            el(f"#panelSettings .settings-card:has-text('{kw}'), #panelSettings section:has-text('{kw}'), #panelSettings .card:has-text('{kw}'), #panelSettings div.table-card:has-text('{kw}')", nm)

        print("TOTAL-OK", ok)
        browser.close()


if __name__ == '__main__':
    main()
