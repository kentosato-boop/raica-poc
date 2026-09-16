#!/usr/bin/env python3
"""v11.0: 9/3ビルドの管理画面 欠落分＋新機能の撮影"""
import json, datetime
from capture import (FIREBASE_STUB, QRCODE_STUB, LEAFLET_STUB, XLSX_STUB, CHECKINS, ts, BASE, OUT)
from capture6 import ORDERS2
from playwright.sync_api import sync_playwright
import urllib.request, os

TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date().isoformat()


def main():
    os.makedirs(f"{OUT}/btn", exist_ok=True)
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
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(2800)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(1500)

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def el(sel, name, nth=0, to_btn=True, timeout=4000):
            try:
                loc = page.locator(sel).nth(nth)
                loc.scroll_into_view_if_needed(timeout=timeout)
                page.wait_for_timeout(250)
                path = f"{OUT}/btn/{name}.png" if to_btn else f"{OUT}/{name}.png"
                loc.screenshot(path=path, timeout=6000)
                print("ok:", name)
            except Exception as e:
                print("FAIL", name, str(e)[:90])

        def closemodals():
            page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay],.modal-overlay').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'});document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove());")
            page.wait_for_timeout(300)

        # ── ヘッダー帯・トースト ──
        page.screenshot(path=f"{OUT}/a69-tabs-strip.png", clip={"x": 0, "y": 0, "width": 1600, "height": 150})
        print("shot: a69-tabs-strip")
        page.evaluate("toast('振り分けを保存しました','ok',60000)")
        page.wait_for_timeout(400)
        el("#toastZone", "a66-toast-ok", to_btn=False)
        page.evaluate("document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove())")
        page.evaluate("toast('SAP登録失敗: 代表品目分類 \"17\" の支払割当が見つかりません（品目: 3579）','err',60000)")
        page.wait_for_timeout(400)
        el("#toastZone", "a67-toast-err", to_btn=False)
        page.evaluate("document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove())")

        # ── オーダー: 空状態 ──
        try:
            other = page.evaluate("(()=>{const s=document.getElementById('globalHallSelect');const o=[...s.options].map(x=>x.value).filter(v=>v&&v!=='HALL-18YT');return o[0]||''})()")
            if other:
                page.evaluate(f"const s=document.getElementById('globalHallSelect'); s.value='{other}'; onGlobalHallChange();")
                page.wait_for_timeout(1800)
                shot("a68-orders-empty")
                page.evaluate("const s=document.getElementById('globalHallSelect'); s.value='HALL-18YT'; onGlobalHallChange();")
                page.wait_for_timeout(1500)
        except Exception as e:
            print("FAIL a68", str(e)[:80])

        # ── 部屋紐付け: 行 ──
        page.evaluate("showPanel('roomAssignments',document.querySelectorAll('.tab-btn')[1])")
        page.wait_for_timeout(1800)
        el("#raList .ra-group", "c-room-rows", to_btn=False)

        # ── 予約: 確定・編集モーダル ──
        page.evaluate("showPanel('reservations',document.getElementById('tabReservations'))")
        page.wait_for_timeout(800)
        page.fill('#rsvTabFrom', TODAY)
        page.fill('#rsvTabTo', TODAY)
        page.evaluate("loadRsvTab()")
        page.wait_for_timeout(1500)
        el("#panelReservations button:has-text('未確定')", "v-btn-confirm")
        el("#panelReservations span:has-text('✅確定')", "v-btn-confirmed")
        el("#panelReservations button:has-text('⚠ 葬儀社 未選択')", "v-btn-nocust")
        try:
            page.locator("#panelReservations button:has-text('✏️')").first.click()
            page.wait_for_timeout(1600)
            shot("a62-rsv-edit-modal")
            # 施設予約情報・予約品目のセクションまでスクロール
            try:
                page.locator("text=🏗 施設予約情報（手動入力）").first.scroll_into_view_if_needed(timeout=3000)
                page.wait_for_timeout(400)
                shot("a62b-rsv-edit-facility")
            except Exception as e:
                print("FAIL a62b", str(e)[:80])
            try:
                page.locator("text=📦 予約品目（火葬種別・式場・骨壺など）").first.scroll_into_view_if_needed(timeout=3000)
                page.wait_for_timeout(400)
                shot("a62c-rsv-edit-items")
            except Exception as e:
                print("FAIL a62c", str(e)[:80])
            closemodals()
        except Exception as e:
            print("FAIL a62", str(e)[:80])
            closemodals()

        # ── 火葬確認: LINE申込検索・QRモーダル(カード印刷)・2段バッジ ──
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[2])")
        page.wait_for_timeout(1500)
        el("td.col-link-status", "c-link-badges", nth=0, to_btn=False)
        el("td.col-link-status", "c-link-badges-linked", nth=1, to_btn=False)
        try:
            page.locator("#rsvTableWrap .rsv-qr-btn:has-text('QR')").first.click()
            page.wait_for_timeout(1500)
            shot("a16-checkin-qr-modal")
            el("button:has-text('🖨 カード印刷')", "k-btn-card-print")
            closemodals()
        except Exception as e:
            print("FAIL qr-modal", str(e)[:80])
            closemodals()
        try:
            page.locator("#rsvTableWrap button:has-text('LINE申込を検索')").first.click()
            page.wait_for_timeout(1400)
            shot("a60-line-search-modal")
            closemodals()
        except Exception as e:
            print("FAIL a60", str(e)[:80])
            closemodals()

        # ── お会計精算: 支払い準備完了モーダル・振り分け一括・割引・精算QR・ロック ──
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1600)
        el("#panelPayment button:has-text('💰 支払い準備完了にする')", "y-btn-ready")
        el("#panelPayment button:has-text('✅ 受付する')", "y-btn-checkin")
        # 支払い準備完了にする → 確認モーダル
        try:
            page.locator("#panelPayment button:has-text('💰 支払い準備完了にする')").first.click()
            page.wait_for_timeout(1800)
            shot("a76-payment-start-modal")
            closemodals()
        except Exception as e:
            print("FAIL a76", str(e)[:80])
            closemodals()
        # 振り分けモーダル（一括ボタン付き）
        try:
            page.evaluate("const c=(allCheckins||[]).find(x=>x.checkinType==='funeral_company')||((allCheckins||[])[0]); if(c) openAssignModal(c.id);")
            page.wait_for_timeout(1800)
            shot("a51-assign-modal")
            el("#assignModal button:has-text('全て👤 喪主')", "y-btn-bulk-mourner")
            el("#assignModal button:has-text('✅ 振り分けを確定')", "y-btn-assign-confirm")
            closemodals()
        except Exception as e:
            print("FAIL a51", str(e)[:80])
            closemodals()
        # 割引モーダル
        try:
            page.locator("#panelPayment button:has-text('🏷 割引')").first.click()
            page.wait_for_timeout(1500)
            shot("a30-discount-modal")
            closemodals()
        except Exception as e:
            try:
                page.evaluate("const c=(allCheckins||[])[0]; if(c) openDiscountModal(c.id);")
                page.wait_for_timeout(1500)
                shot("a30-discount-modal")
                closemodals()
            except Exception as e2:
                print("FAIL a30", str(e2)[:80])
                closemodals()
        # 精算QRモーダル（税込確定/未確定）
        try:
            page.evaluate("openPriceSimModal([{sapSalesOrder:'783'}], '1', 'CK-01')")
            page.wait_for_timeout(2200)
            shot("a64-priceqr-ok")
            closemodals()
            page.evaluate("openPriceSimModal([{sapSalesOrder:'784'}], '1', 'CK-01')")
            page.wait_for_timeout(2200)
            shot("a65-priceqr-blocked")
            closemodals()
        except Exception as e:
            print("FAIL priceqr", str(e)[:80])
            closemodals()
        # 精算ロック入力
        try:
            card = page.locator("#panelPayment .settings-card:has-text('精算ロック管理')").first
            card.scroll_into_view_if_needed(timeout=3000)
            inputs = card.locator("input")
            if inputs.count() >= 2:
                inputs.nth(0).fill("TEST-2500200")
                inputs.nth(1).fill("900000")
                page.wait_for_timeout(300)
            card.screenshot(path=f"{OUT}/a72-lock-filled.png")
            print("shot: a72-lock-filled")
        except Exception as e:
            print("FAIL a72", str(e)[:80])

        # ── 代理注文: 予約なし→購入者4種・得意先なし予約・QR読取 ──
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(900)
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1200)
        el("#panelProxy button:has-text('📷 予約番号QR読取'), #panelProxy button:has-text('QR読取')", "p-btn-qr-scan")
        try:
            page.click("text=🚶 予約なし", timeout=3000)
            page.wait_for_timeout(1300)
            shot("a50-proxy-step2-norsv")
            el("#panelProxy button:has-text('🏢 葬儀社')", "p-btn-payer-funeral")
            el("#panelProxy button:has-text('👤 喪主')", "p-btn-payer-mourner")
            el("#panelProxy button:has-text('🚶 お連れ様')", "p-btn-payer-guest")
            el("#panelProxy button:has-text('👔 従業員')", "p-btn-payer-employee")
            try:
                sec = page.locator("#panelProxy h3:has-text('購入者を選択'), #panelProxy div:has-text('購入者を選択')").last
                sec.screenshot(path=f"{OUT}/btn/p-sec-step2.png")
                print("ok: p-sec-step2")
            except Exception as e:
                print("FAIL p-sec-step2", str(e)[:80])
        except Exception as e:
            print("FAIL a50", str(e)[:80])
        # 得意先コード無し予約 → ②が開く
        try:
            page.fill('#proxyBookingIdInput', 'TEST-2500201')
            page.click("text=🔍 紐付け")
            page.wait_for_timeout(2500)
            shot("a59-proxy-step2-nocust")
        except Exception as e:
            print("FAIL a59", str(e)[:80])

        # ── 設定: ユーザー・UAT・在庫・商品・QRコード発行 ──
        page.evaluate("showPanelFromMenu('users')")
        page.wait_for_timeout(1400)
        try:
            page.locator("#userList button:has-text('設定')").first.click()
            page.wait_for_timeout(1200)
            shot("a70-user-edit")
            closemodals()
        except Exception as e:
            print("FAIL a70", str(e)[:80])
        page.evaluate("showPanelFromMenu('settings')")
        page.wait_for_timeout(1800)
        try:
            page.evaluate("""(()=>{const b=document.getElementById('outsystemsUatCreateBtn');const c=b.closest('.settings-card')||b.parentElement.parentElement;c.id='uatCard';})()""")
            el("#uatCard", "a73-uat-quarantine", to_btn=False)
        except Exception as e:
            print("FAIL a73", str(e)[:80])
        # 在庫（刷新後）
        page.evaluate("showPanelFromMenu('inventory')")
        page.wait_for_timeout(2000)
        shot("a42-inventory")
        # 商品（同期ボタン群）
        page.evaluate("showPanelFromMenu('products')")
        page.wait_for_timeout(1800)
        shot("a23-products")
        try:
            bar = page.locator("#panelProducts button:has-text('🔄 全同期')").first
            row = bar.locator("xpath=ancestor::div[1]")
            row.screenshot(path=f"{OUT}/c-products-sync.png")
            print("ok: c-products-sync")
        except Exception as e:
            print("FAIL c-products-sync", str(e)[:80])

        browser.close()


if __name__ == '__main__':
    main()
