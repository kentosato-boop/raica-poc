#!/usr/bin/env python3
"""8/12ビルド: 失敗分の撮り直し＋新規追加ショット"""
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

        def el(sel, name, nth=0, to_btn=True, timeout=4000):
            try:
                loc = page.locator(sel).nth(nth)
                loc.scroll_into_view_if_needed(timeout=timeout)
                page.wait_for_timeout(200)
                path = f"{OUT}/btn/{name}.png" if to_btn else f"{OUT}/{name}.png"
                loc.screenshot(path=path, timeout=5000)
                print("ok:", name)
            except Exception as e:
                print("FAIL", name, str(e)[:90])

        def shot(name, full=False):
            page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        def closemodals():
            page.evaluate("document.querySelectorAll('div[id*=Modal],div[id*=Overlay],div[id*=overlay],.modal-overlay').forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.display='none'})")
            page.wait_for_timeout(250)

        # ── オーダー: 撮り直し ──
        el("text=💳 お会計精算へ移す", "o-btn-ready-to-pay")
        el(".order-card button:has-text('✕')", "o-btn-cancel")

        # ── 代理注文: 長め待ちで撮り直し＋新規 ──
        page.evaluate("showPanel('proxy',document.querySelectorAll('.tab-btn')[1])")
        page.wait_for_timeout(900)
        page.select_option('#proxySP', 'SP-YT01')
        page.evaluate("if(typeof onProxySPChange==='function')onProxySPChange()")
        page.wait_for_timeout(1500)
        page.fill('#proxyBookingIdInput', 'TEST-2500200')
        page.click("text=🔍 紐付け")
        page.wait_for_timeout(3000)
        el("#panelProxy button:has-text('✕ クリア'), #panelProxy button:has-text('クリア')", "p-btn-clear")
        el("#proxyMenuArea button:has-text('＋'), #panelProxy button:has-text('＋')", "p-btn-plus")
        el("#proxyMenuArea button:has-text('−'), #panelProxy button:has-text('−')", "p-btn-minus")
        try:
            page.locator("#proxyMenuArea button:has-text('＋'), #panelProxy button:has-text('＋')").first.click()
            page.wait_for_timeout(500)
        except Exception:
            pass
        el("button:has-text('注文を送信')", "p-btn-submit")
        # 絞り込み行（カテゴリフィルタの親行）
        el("xpath=//select[@id='proxyCategoryFilter']/ancestor::div[1]", "c-proxy-filters", to_btn=False, timeout=6000)

        # ── 予約: 確定ボタン（✅確定）と確定済み表示 ──
        page.evaluate("showPanel('reservations',document.getElementById('tabReservations'))")
        page.wait_for_timeout(700)
        page.fill('#rsvTabFrom', TODAY)
        page.fill('#rsvTabTo', TODAY)
        page.evaluate("loadRsvTab()")
        page.wait_for_timeout(1500)
        el("#panelReservations button:has-text('✅確定')", "v-btn-confirm")
        el("#panelReservations td:has-text('確定済み'), #panelReservations span:has-text('確定済み')", "v-btn-confirmed")

        # ── 火葬確認: 2段バッジ（新規） ──
        page.evaluate("showPanel('checkins',document.querySelectorAll('.tab-btn')[4])")
        page.wait_for_timeout(1300)
        el("td.col-link-status", "c-link-badges", to_btn=False)
        # 受付票（別ウィンドウ・自動印刷抑止済み）
        try:
            with ctx.expect_page(timeout=6000) as pop_info:
                page.locator("#rsvTableWrap .rsv-qr-btn:has-text('QR')").first.click()
            pop = pop_info.value
            pop.wait_for_timeout(2500)
            pop.screenshot(path=f"{OUT}/a56-checkin-slip.png", full_page=True)
            print("shot: a56-checkin-slip")
            pop.close()
        except Exception as e:
            print("FAIL a56-checkin-slip", str(e)[:90])
            closemodals()

        # ── お会計精算: 振り分け・領収書分割案内・精算QRモーダル ──
        page.evaluate("showPanel('payment',document.querySelectorAll('.tab-btn')[5])")
        page.wait_for_timeout(1300)
        # 振り分けモーダル（葬儀社受付カード）
        try:
            page.evaluate("const c=(allCheckins||[]).find(x=>x.checkinType==='funeral_company')||((allCheckins||[])[0]); if(c) openAssignModal(c.id);")
            page.wait_for_timeout(1600)
            shot("a51-assign-modal")
            closemodals()
        except Exception as e:
            print("FAIL a51", str(e)[:90])
        # 領収書分割（受注分割へ）案内
        try:
            page.evaluate("const c=(allCheckins||[]).find(x=>x.sapStatus==='sent')||((allCheckins||[])[0]); if(c) openReceiptSplitModal(c.id);")
            page.wait_for_timeout(1800)
            shot("a53-receipt-split-guide")
            closemodals()
        except Exception as e:
            print("FAIL a53", str(e)[:90])
        # 精算QR（自動精算機ご利用票 or モーダル）
        try:
            done = False
            try:
                with ctx.expect_page(timeout=5000) as pop2_info:
                    page.evaluate("generateSettlementQR('64260','783','JPY','喪主')")
                pop2 = pop2_info.value
                pop2.wait_for_timeout(2200)
                pop2.screenshot(path=f"{OUT}/a52-settlement-slip.png", full_page=True)
                print("shot: a52-settlement-slip (window)")
                pop2.close(); done = True
            except Exception:
                pass
            if not done:
                page.wait_for_timeout(1200)
                shot("a52-settlement-slip")
                closemodals()
        except Exception as e:
            print("FAIL a52", str(e)[:90])

        browser.close()

        # ── LIFF: 全履歴表示（新規） ──
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
        lp.evaluate("goHistory()")
        lp.wait_for_timeout(1500)
        try:
            lp.click("text=📜 全履歴を見る", timeout=3000)
            lp.wait_for_timeout(1500)
            lp.screenshot(path=f"{OUT}/m-history-all.png")
            print("shot: m-history-all")
        except Exception as e:
            print("FAIL m-history-all", str(e)[:90])
        browser.close()


if __name__ == '__main__':
    main()
