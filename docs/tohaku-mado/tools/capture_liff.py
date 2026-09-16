#!/usr/bin/env python3
"""LIFF（index.html）実フロー撮影: DEVモード＋モックAPI"""
import os, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = os.environ.get("SHOTS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots"))
os.makedirs(OUT, exist_ok=True)

HIDE_DEV = """
const st=document.createElement('style');
st.textContent='#devBanner{display:none!important}#modeBadge{display:none!important}';
document.documentElement.appendChild(st);
"""

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')

        def new_page(scenario="member"):
            ctx = browser.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=2,
                                      locale="ja-JP", timezone_id="Asia/Tokyo",
                                      extra_http_headers={"X-Scenario": scenario})
            def route_ext(route):
                url = route.request.url
                if url.startswith(BASE):
                    route.continue_()
                else:
                    route.abort()
            ctx.route("**/*", route_ext)
            
            p = ctx.new_page()
            p.on("pageerror", lambda e: print("PAGE-ERR:", str(e)[:200]))
            return ctx, p

        def shot(p, name, full=False):
            p.evaluate("document.getElementById('devBanner')&&(document.getElementById('devBanner').style.display='none');document.getElementById('modeBadge')&&(document.getElementById('modeBadge').style.display='none');var hs=document.getElementById('headerStatus');if(hs&&/開発|DEV/.test(hs.textContent))hs.style.display='none';")
            p.screenshot(path=f"{OUT}/{name}.png", full_page=full)
            print("shot:", name)

        # 1) 前日TOP（mode=pre）
        ctx, p = new_page("new")
        p.goto(BASE + "/index.html?mode=pre&page=preconsent")
        p.wait_for_timeout(2000)
        shot(p, "m-top-pre")
        # 申込にすすむ → scrPreInfo
        try:
            p.click("text=申込にすすむ", timeout=2500)
            p.wait_for_timeout(1200)
            shot(p, "m-pre-info", full=True)
        except Exception as e:
            print("pre next fail", e)
        ctx.close()

        # 2) 当日TOP（rsvId）＋故人情報 → 同意にすすむ → scrRegister
        ctx, p = new_page("unconsented")
        p.goto(BASE + "/index.html?rsvId=RSV-001&hallId=HALL-18YT")
        p.wait_for_timeout(2200)
        shot(p, "m-top-day")
        try:
            p.click("text=同意にすすむ", timeout=2500)
            p.wait_for_timeout(1200)
            shot(p, "m-register-consent", full=True)
        except Exception as e:
            print("consent fail", e)
        ctx.close()

        # 3) 注文フロー: checkin home → order → cart → confirm → history → mycart → feecheck
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-01&label=%E6%9C%88%E3%81%AE%E9%96%931")
        p.wait_for_timeout(2500)
        shot(p, "m-checkin-home")
        # メニューへ
        try:
            p.evaluate("show('scrOrder');renderCatTabs();renderMenu();refreshCart();")
            p.wait_for_timeout(800)
            shot(p, "m-order-menu")
            # フリードリンクタブ
            try:
                p.click("text=フリードリンク", timeout=2000)
                p.wait_for_timeout(500)
                shot(p, "m-order-fd-tab")
            except Exception as e:
                print("fd tab fail", e)
            # 商品モーダル
            try:
                p.click("text=ブレンドコーヒー", timeout=2000)
                p.wait_for_timeout(600)
                shot(p, "m-product-modal")
                p.evaluate("closeProductModal()")
            except Exception as e:
                print("product modal fail", e)
            # カートに追加
            p.evaluate("""
              const items=allItems();
              S.cart={}; S.cart[items[0].id]=2; S.cart[items[2].id]=1;
              refreshCart(); renderMenu();
            """)
            p.wait_for_timeout(400)
            p.evaluate("toggleCart()")
            p.wait_for_timeout(500)
            shot(p, "m-order-cart-open")
            # 注文確定
            p.evaluate("doOrder()")
            p.wait_for_timeout(2500)
            shot(p, "m-order-confirm")
        except Exception as e:
            print("order flow fail", e)
        # 履歴
        try:
            p.evaluate("goHistory()")
            p.wait_for_timeout(1200)
            shot(p, "m-history")
        except Exception as e:
            print("history fail", e)
        # 予約カート
        try:
            p.evaluate("goMyCart()")
            p.wait_for_timeout(1200)
            shot(p, "m-mycart", full=True)
        except Exception as e:
            print("mycart fail", e)
        # 料金確認（喪主払い）
        try:
            p.evaluate("openFeeCheck()")
            p.wait_for_timeout(1200)
            shot(p, "m-feecheck", full=True)
        except Exception as e:
            print("feecheck fail", e)
        ctx.close()

        # 4) scrNoQr / scrNoAssign / scrPickHall
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?page=order")
        p.wait_for_timeout(1800)
        # DEV_MODEではガードが効かないため直接表示
        p.evaluate("show('scrNoQr')")
        p.wait_for_timeout(300)
        shot(p, "m-noqr")
        p.goto(BASE + "/index.html?hallId=HALL-18YT&spId=SP-YT01&roomId=R-99")
        p.wait_for_timeout(2200)
        shot(p, "m-noassign")
        p.evaluate("""
          showPickHall([{id:'HALL-15MY',name:'町屋斎場'},{id:'HALL-16OC',name:'落合斎場'},
            {id:'HALL-17YY',name:'代々幡斎場'},{id:'HALL-18YT',name:'四ツ木斎場'},
            {id:'HALL-19KR',name:'桐ヶ谷斎場'},{id:'HALL-20HR',name:'堀ノ内斎場'},
            {id:'HALL-21OH',name:'お花茶屋会館'}])
        """)
        p.wait_for_timeout(400)
        shot(p, "m-pickhall")
        ctx.close()

        # 5) エンディングノート（?preview=ending-note・大沼様レビュー用導線）
        ctx, p = new_page("member")
        p.goto(BASE + "/index.html?preview=ending-note")
        p.wait_for_timeout(2000)
        shot(p, "m-ending-note", full=True)
        ctx.close()

        browser.close()


if __name__ == '__main__':
    main()
