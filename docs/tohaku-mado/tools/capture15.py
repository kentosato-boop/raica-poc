#!/usr/bin/env python3
"""v10.0: 管理画面の追加ショット（モーダル・エラー表示・トースト・空状態など）"""
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
                route.abort()

        ctx.route("**/*", route_ext)
        ctx.add_init_script(f"window.__MOCK_COLLECTIONS__ = {json.dumps(collections, ensure_ascii=False)};")
        ctx.add_init_script("try{sessionStorage.setItem('adminToken','MOCK-TOKEN');localStorage.setItem('mado_suppress_autoprint','1');}catch(e){}")
        ctx.add_init_script(LEAFLET_STUB)
        ctx.add_init_script(QRCODE_STUB)

        page = ctx.new_page()
        page.goto(BASE + "/admin.html?noautoprint=1")
        page.wait_for_timeout(2500)
        page.evaluate("const s=document.getElementById('globalHallSelect'); s.style.display=''; s.value='HALL-18YT'; onGlobalHallChange();")
        page.wait_for_timeout(1500)

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def el(sel, name, nth=0, to_btn=False, timeout=4000):
            try:
                loc = page.locator(sel).nth(nth)
                loc.scroll_into_view_if_needed(timeout=timeout)
                page.wait_for_timeout(250)
                path = f"{OUT}/btn/{name}.png" if to_btn else f"{OUT}/{name}.png"
                loc.screenshot(path=path, timeout=5000)
                print("ok:", name)
            except Exception as e:
                print("FAIL", name, str(e)[:90])

        def closemodals():
            page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay],.modal-overlay').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'});document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove());")
            page.wait_for_timeout(300)

        # ── 1) ヘッダー＋タブ帯（画面上部の帯） ──
        try:
            page.screenshot(path=f"{OUT}/a69-tabs-strip.png", clip={"x": 0, "y": 0, "width": 1600, "height": 150})
            print("shot: a69-tabs-strip")
        except Exception as e:
            print("FAIL a69", str(e)[:90])

        # ── 2) トースト表示例（成功・失敗） ──
        try:
            page.evaluate("toast('✅ 振り分けを保存しました','ok',60000)")
            page.wait_for_timeout(500)
            el("#toastZone", "a66-toast-ok")
            page.evaluate("document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove())")
            page.evaluate("toast('SAP登録失敗: 代表品目分類 \"17\" の支払割当が見つかりません（品目: 3579）','err',60000)")
            page.wait_for_timeout(500)
            el("#toastZone", "a67-toast-err")
            page.evaluate("document.querySelectorAll('#toastZone .toast').forEach(t=>t.remove())")
        except Exception as e:
            print("FAIL toast", str(e)[:90])

        # ── 3) オーダー: 別斎場に切り替えて空の状態 ──
        try:
            other = page.evaluate("(()=>{const s=document.getElementById('globalHallSelect');const o=[...s.options].map(x=>x.value).filter(v=>v&&v!=='HALL-18YT');return o[0]||''})()")
            if other:
                page.evaluate(f"const s=document.getElementById('globalHallSelect'); s.value='{other}'; onGlobalHallChange();")
                page.wait_for_timeout(1800)
                shot("a68-orders-empty")
                page.evaluate("const s=document.getElementById('globalHallSelect'); s.value='HALL-18YT'; onGlobalHallChange();")
                page.wait_for_timeout(1500)
            else:
                print("FAIL a68 no-other-hall")
        except Exception as e:
            print("FAIL a68", str(e)[:90])

        # ── 4) 火葬確認: LINE申込を検索モーダル ──
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(1400)
        try:
            page.locator("#rsvTableWrap button:has-text('LINE申込を検索')").first.click()
            page.wait_for_timeout(1200)
            shot("a60-line-search-modal")
            # 検索を実行した状態（結果 or 該当なし）
            try:
                page.locator("#rsvPreConsentOverlay button:has-text('検索')").first.click()
                page.wait_for_timeout(1500)
                shot("a61-line-search-results")
            except Exception as e:
                print("FAIL a61", str(e)[:90])
            closemodals()
        except Exception as e:
            print("FAIL a60", str(e)[:90])
            closemodals()

        # ── 5) 予約: 編集モーダル（収骨容器の選択を含む） ──
        page.evaluate("showPanel('reservations',document.getElementById('tabReservations'))")
        page.wait_for_timeout(800)
        page.fill('#rsvTabFrom', TODAY)
        page.fill('#rsvTabTo', TODAY)
        page.evaluate("loadRsvTab()")
        page.wait_for_timeout(1500)
        try:
            page.locator("#panelReservations button:has-text('✏')").first.click()
            page.wait_for_timeout(1500)
            shot("a62-rsv-edit-modal", full=False)
            closemodals()
        except Exception as e:
            print("FAIL a62 (✏)", str(e)[:90])
            try:
                rid = page.evaluate("(rsvTabCache&&rsvTabCache[0]&&(rsvTabCache[0].id||rsvTabCache[0].bookingId))||''")
                if rid:
                    page.evaluate(f"openRsvEditFromTab('{rid}')")
                    page.wait_for_timeout(1500)
                    shot("a62-rsv-edit-modal")
                closemodals()
            except Exception as e2:
                print("FAIL a62 fallback", str(e2)[:90])
                closemodals()

        # ── 6) お会計精算: 精算QRモーダル（税込確定=QR表示 / 未確定=発行不可） ──
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1400)
        try:
            page.evaluate("openPriceSimModal([{sapSalesOrder:'783'}], '1', 'CK-01')")
            page.wait_for_timeout(2200)
            shot("a64-priceqr-ok")
            closemodals()
        except Exception as e:
            print("FAIL a64", str(e)[:90])
            closemodals()
        try:
            page.evaluate("openPriceSimModal([{sapSalesOrder:'784'}], '1', 'CK-01')")
            page.wait_for_timeout(2200)
            shot("a65-priceqr-blocked")
            closemodals()
        except Exception as e:
            print("FAIL a65", str(e)[:90])
            closemodals()

        # ── 7) 精算ロック管理: 入力した状態 ──
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
            print("FAIL a72", str(e)[:90])

        # ── 8) 設定: ユーザー編集（権限・担当斎場） ──
        page.evaluate("showPanelFromMenu('users')")
        page.wait_for_timeout(1400)
        try:
            page.locator("#userList button:has-text('設定')").first.click()
            page.wait_for_timeout(1200)
            shot("a70-user-edit")
            closemodals()
        except Exception as e:
            print("FAIL a70", str(e)[:90])
            closemodals()

        # ── 9) 初期設定: UAT隔離予約ボタンの周辺 ──
        page.evaluate("showPanelFromMenu('settings')")
        page.wait_for_timeout(1600)
        try:
            btn = page.locator("#outsystemsUatCreateBtn")
            btn.scroll_into_view_if_needed(timeout=3000)
            page.wait_for_timeout(300)
            page.evaluate("""(()=>{const b=document.getElementById('outsystemsUatCreateBtn');const c=b.closest('.settings-card')||b.parentElement.parentElement;c.id='uatCard';})()""")
            el("#uatCard", "a73-uat-quarantine")
        except Exception as e:
            print("FAIL a73", str(e)[:90])

        # ── 10) 受付票印刷（ポップアップ・自動印刷抑止） ──
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(1300)
        try:
            with ctx.expect_page(timeout=8000) as pop_info:
                page.locator("button:has-text('受付票印刷')").first.click()
            pop = pop_info.value
            pop.wait_for_timeout(2500)
            pop.screenshot(path=f"{OUT}/a71-checkin-slip.png", full_page=True)
            print("shot: a71-checkin-slip")
            pop.close()
        except Exception as e:
            print("FAIL a71", str(e)[:90])
            closemodals()

        browser.close()


if __name__ == '__main__':
    main()
