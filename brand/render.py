"""Krinmed Instagram carousel renderer.
Usage: python3 render.py day.json
JSON: {out, foot, slides:[{fa, en, tag?, tagcolor? (red|green|maroon), image?, eep?, foot?}]}
Assets expected in ./assets: krinmed-logo.png, eep-logo.png, product photos.
Brand palette (sampled from official logos): red #E73432, green #8DBF22, lime #C3D201, EEP maroon #761114.
"""
import json, sys, pathlib, base64, mimetypes
from playwright.sync_api import sync_playwright

S = pathlib.Path(__file__).parent
F = S / "fonts/node_modules/@fontsource"
A = S / "assets"
def b64(f): return base64.b64encode(pathlib.Path(f).read_bytes()).decode()
def uri(f):
    f = pathlib.Path(f); m = mimetypes.guess_type(f.name)[0] or "image/webp"
    return f"data:{m};base64,{b64(f)}"
data = json.loads((S / sys.argv[1]).read_text())
out = S / data["out"]; out.mkdir(exist_ok=True)

def font(fam, pkg, sub, w): return f"@font-face{{font-family:{fam};src:url(data:font/woff2;base64,{b64(F/pkg/'files'/f'{pkg}-{sub}-{w}-normal.woff2')});font-weight:{w}}}"
FONTS = "".join(font("Vaz","vazirmatn","arabic",w) for w in (400,700,800)) + "".join(font("Int","inter","latin",w) for w in (400,600,800))
LOGO, EEP, PHX = uri(A/"krinmed-logo.png"), uri(A/"eep-logo.png"), uri(A/"phoenix.png")
TAG = {"red":"#E73432","green":"#8DBF22","maroon":"#761114"}

CSS = FONTS + """
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1350px;background:#fff;font-family:Int,Vaz;color:#1E1E1E;position:relative;overflow:hidden}
.side{position:absolute;top:0;bottom:0;left:0;width:18px;background:#8DBF22}
.side:after{content:"";position:absolute;top:0;left:0;width:18px;height:220px;background:#E73432}
.top{position:absolute;top:56px;left:90px;right:80px;display:flex;justify-content:space-between;align-items:center}
.top img{height:92px}
.num{font-weight:800;font-size:26px;letter-spacing:3px;color:#B5B5B5}
.wrap{position:absolute;top:210px;left:90px;right:80px;bottom:200px;display:flex;flex-direction:column;justify-content:center;gap:44px}
.photo{width:100%;height:470px;border-radius:28px;overflow:hidden;background:#F2F5EC}
.photo img{width:100%;height:100%;object-fit:cover}
.fa{direction:rtl;text-align:right;font-family:Vaz,Int;font-weight:800;font-size:60px;line-height:1.55;color:#1E1E1E}
.en{font-weight:600;font-size:42px;line-height:1.3;color:#555;border-left:8px solid #8DBF22;padding-left:26px}
.hook .fa{font-size:76px;color:#E73432}
.hook .en{font-size:46px}
.row{display:flex;align-items:center;gap:28px}
.tag{display:inline-block;color:#fff;font-weight:800;font-size:30px;padding:14px 26px;border-radius:12px}
.row img{height:62px}
.foot{position:absolute;bottom:56px;left:90px;right:80px;border-top:3px solid #C3D201;padding-top:24px;font-size:23px;color:#777;line-height:1.5;display:flex;justify-content:space-between;gap:30px}
.foot b{color:#8DBF22;white-space:nowrap}
.wm{position:absolute;right:-90px;bottom:120px;width:620px;opacity:.07}
.swipe{position:absolute;bottom:150px;right:80px;font-weight:800;font-size:28px;color:#8DBF22}
"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    pg = b.new_page(viewport={"width":1080,"height":1350})
    n = len(data["slides"])
    for i, s in enumerate(data["slides"], 1):
        hook = "hook" if i == 1 else ""
        photo = f'<div class="photo"><img src="{uri(A/s["image"])}"></div>' if s.get("image") else ""
        tag = f'<span class="tag" style="background:{TAG[s.get("tagcolor","maroon")]}">{s["tag"]}</span>' if s.get("tag") else ""
        eep = f'<img src="{EEP}">' if s.get("eep") else ""
        row = f'<div class="row">{eep}{tag}</div>' if (tag or eep) else ""
        swipe = '<div class="swipe"><span dir="rtl">ورق بزنید</span> &nbsp;·&nbsp; <span dir="ltr">swipe →</span></div>' if i == 1 and n > 1 else ""
        html = f"""<html><head><style>{CSS}</style></head><body><div class="side"></div>{"" if s.get("image") else f'<img class="wm" src="{PHX}">'}
<div class="top"><img src="{LOGO}"><span class="num">{i:02d} / {n:02d}</span></div>
<div class="wrap {hook}">{photo}<div class="fa">{s['fa']}</div><div class="en">{s['en']}</div>{row}</div>
{swipe}<div class="foot"><span>{s.get('foot', data['foot'])}</span><b>krinmed.com</b></div></body></html>"""
        pg.set_content(html); pg.wait_for_timeout(500)
        pg.screenshot(path=str(out / f"slide-{i}.png"))
    b.close()
print("ok", out)
