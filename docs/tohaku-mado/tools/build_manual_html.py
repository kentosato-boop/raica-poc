#!/usr/bin/env python3
"""東京博善 mado 手順書 MD → 単一HTML（スクショはdata URI埋め込み）"""
import base64, mimetypes, os, re
import markdown

DOCDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # docs/tohaku-mado
SRC = os.path.join(DOCDIR, "東京博善窓口システム_手順書.md")
IMGDIR = DOCDIR
OUT = os.environ.get("MANUAL_HTML_OUT", os.path.join(DOCDIR, "tools", "tohaku-mado-manual.html"))

md = open(SRC, encoding="utf-8").read()

body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"], output_format="html5")

# img src -> data URI, wrap in <figure>
def embed(m):
    src = m.group(1)
    path = os.path.join(IMGDIR, src)
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(open(path, "rb").read()).decode()
    alt = m.group(2)
    return (f'<figure class="shot"><img loading="lazy" src="data:{mime};base64,{data}" alt="{alt}">'
            f'<figcaption>{alt}</figcaption></figure>')

body = re.sub(r'<img alt="([^"]*)" src="(imgs/[^"]+)"\s*/?>',
              lambda m: embed(type("M", (), {"group": lambda self=None, i=0, _m=m: (_m.group(2) if i == 1 else _m.group(1))})()),
              body)

# simpler: markdown emits <img alt="x" src="y"> — redo cleanly
body = markdown.markdown(md, extensions=["tables", "fenced_code"], output_format="html5")
def embed2(m):
    alt, src = m.group(1), m.group(2)
    path = os.path.join(IMGDIR, src)
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return (f'<figure class="shot"><img loading="lazy" src="data:{mime};base64,{data}" alt="{alt}">'
            f'<figcaption>{alt}</figcaption></figure>')
body = re.sub(r'<img alt="([^"]*)" src="(imgs/[^"]+)"\s*/?>', embed2, body)

# raw <img src="imgs/..."> をdata URIへ
def embed_raw(m):
    pre, src, post = m.group(1), m.group(2), m.group(3)
    path = os.path.join(IMGDIR, src)
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return f'<img {pre}src="data:{mime};base64,{data}"{post}>'
body = re.sub(r'<img ([^>]*?)src="(imgs/[^"]+)"([^>]*?)>', embed_raw, body)

# tables scroll container
body = body.replace("<table>", '<div class="tblwrap"><table>').replace("</table>", "</table></div>")
# figures inside <p> -> unwrap
body = re.sub(r'<p>(<figure class="shot">.*?</figure>)</p>', r"\1", body, flags=re.S)

css = """
:root{
  --paper:#ffffff; --ink:#26232f; --muted:#6d6880; --accent:#5b4d9e;
  --accent-soft:#efedf7; --line:#e5e2ee; --code-bg:#f4f3f8; --warn-bg:#fbf7ec;
}
@media (prefers-color-scheme: dark){
  :root{ --paper:#1b1a21; --ink:#e8e6f0; --muted:#a29db8; --accent:#a99ae6;
    --accent-soft:#2a2738; --line:#37344a; --code-bg:#252331; --warn-bg:#2c2820; }
}
:root[data-theme="dark"]{ --paper:#1b1a21; --ink:#e8e6f0; --muted:#a29db8; --accent:#a99ae6;
  --accent-soft:#2a2738; --line:#37344a; --code-bg:#252331; --warn-bg:#2c2820; }
:root[data-theme="light"]{ --paper:#ffffff; --ink:#26232f; --muted:#6d6880; --accent:#5b4d9e;
  --accent-soft:#efedf7; --line:#e5e2ee; --code-bg:#f4f3f8; --warn-bg:#fbf7ec; }
*{box-sizing:border-box}
body{ margin:0; background:var(--paper); color:var(--ink);
  font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Noto Sans JP","Yu Gothic UI",Meiryo,sans-serif;
  line-height:1.85; font-size:15.5px; }
main{ max-width:880px; margin:0 auto; padding:48px 28px 96px; }
header.doc{ border-bottom:3px solid var(--accent); padding-bottom:20px; margin-bottom:36px; }
header.doc .eyebrow{ color:var(--accent); font-size:12px; letter-spacing:.18em; font-weight:700; }
h1{ font-size:27px; line-height:1.4; margin:6px 0 0; text-wrap:balance; }
h2{ font-size:21px; margin:64px 0 16px; padding:6px 0 6px 14px; border-left:5px solid var(--accent);
  line-height:1.4; text-wrap:balance; }
h3{ font-size:17px; margin:36px 0 10px; color:var(--ink); }
h3::before{ content:"▍"; color:var(--accent); margin-right:4px; }
h4{ font-size:15.5px; margin:24px 0 8px; }
p{ margin:10px 0; }
a{ color:var(--accent); }
hr{ border:0; border-top:1px solid var(--line); margin:48px 0; }
strong{ font-weight:700; }
code{ font-family:"SF Mono",Consolas,Menlo,monospace; font-size:.86em; background:var(--code-bg);
  padding:1px 5px; border-radius:4px; }
pre{ background:var(--code-bg); border:1px solid var(--line); border-radius:8px; padding:14px 16px;
  overflow-x:auto; line-height:1.6; }
pre code{ background:none; padding:0; font-size:12.5px; }
blockquote{ margin:14px 0; padding:10px 16px; background:var(--warn-bg); border-left:4px solid #c9a227;
  border-radius:0 8px 8px 0; }
blockquote p{ margin:4px 0; }
.tblwrap{ overflow-x:auto; margin:14px 0; }
table{ border-collapse:collapse; width:100%; font-size:14px; font-variant-numeric:tabular-nums; }
th{ background:var(--accent-soft); color:var(--ink); text-align:left; font-weight:700; }
th,td{ border:1px solid var(--line); padding:7px 11px; vertical-align:top; }
tbody tr:nth-child(even){ background:color-mix(in srgb, var(--accent-soft) 35%, transparent); }
figure.shot{ margin:20px 0; }
figure.shot img{ max-width:100%; height:auto; display:block; border:1px solid var(--line);
  border-radius:10px; box-shadow:0 2px 10px rgba(38,35,47,.08); }
figure.shot figcaption{ font-size:12.5px; color:var(--muted); margin-top:7px; letter-spacing:.04em; }
li{ margin:4px 0; }
@media (prefers-reduced-motion: reduce){ *{scroll-behavior:auto!important} }
"""

html = f"""<title>東京博善「窓口（mado）」システム手順書</title>
<style>{css}</style>
<main>
<header class="doc">
  <div class="eyebrow">TOKYO HAKUZEN — MADO OPERATION MANUAL</div>
</header>
{body}
</main>
"""
open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, len(html))
