"""
从第五人格 B站Wiki 下载角色头像 (width=810 的角色立绘)
逐页访问 → 匹配 810px 宽度的角色肖像 → 下载保存
"""
import os
import time
import requests
from bs4 import BeautifulSoup

SAVE_DIR = os.path.join(os.path.dirname(__file__), "static", "images", "characters")
WIKI_BASE = "https://wiki.biligame.com/dwrg/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://wiki.biligame.com/dwrg/",
}

# 中文名 → 文件名
NAME_MAP = {
    # 求生者
    "医生": "doctor.png", "园丁": "gardener.png", "律师": "lawyer.png",
    "慈善家": "philanthropist.png", "机械师": "mechanic.png", "前锋": "forward.png",
    "佣兵": "mercenary.png", "调香师": "perfumer.png",
    "空军": "coordinator.png", "祭司": "priestess.png", "盲女": "mindseye.png",
    "先知": "seer.png", "入殓师": "embalmer.png", "咒术师": "enchantress.png",
    "勘探员": "prospector.png", "野人": "wildling.png", "杂技演员": "acrobat.png",
    "大副": "firstofficer.png", "守墓人": "gravekeeper.png", "囚徒": "prisoner.png",
    "昆虫学者": "entomologist.png", "击球手": "batter.png",
    "心理学者": "psychologist.png", "病患": "patient.png",
    "哭泣小丑": "weepingclown.png", "教授": "professor.png",
    "古董商": "antiquarian.png", "作曲家": "composer.png",
    "记者": "journalist.png", "拉拉队员": "cheerleader.png", "消防员": "firefighter.png",
    # 监管者
    "杰克": "jack.png", "小丑": "joker.png", "蜘蛛": "spider.png",
    "红蝶": "geisha.png", "黄衣之主": "feaster.png", "宿伞之魂": "wuchang.png",
    "摄影师": "photographer.png", "梦之女巫": "dreamwitch.png",
    "厂长": "hellember.png", "鹿头": "gamekeeper.png", "疯眼": "madeyes.png",
    "爱哭鬼": "axeboy.png", "红夫人": "bloodyqueen.png", "小提琴家": "violinist.png",
    "雕刻家": "sculptor.png", "邦邦": "guard26.png", "使徒": "disciple.png",
    "渔女": "naiad.png", "博士": "undead.png", "蜡像师": "waxartist.png",
    "破轮": "breakingwheel.png", "噩梦": "nightmare.png", "记录员": "clerk.png",
    "隐士": "hermit.png", "守夜人": "nightwatch.png", "歌剧演员": "operasinger.png",
    "时空之影": "shadowoftime.png", "艾维": "ivy.png",
}


def download_image(img_url, filepath):
    """下载图片，已存在则跳过"""
    if os.path.exists(filepath):
        return "SKIP (exists)"
    try:
        resp = requests.get(img_url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 2048:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return f"OK ({len(resp.content)} bytes)"
        return f"FAIL (status={resp.status_code}, size={len(resp.content)})"
    except Exception as e:
        return f"ERR: {e}"


def fetch_portrait(name):
    """访问角色 wiki 页面，找到 width=810 的肖像图并下载"""
    filename = NAME_MAP.get(name)
    if not filename:
        return f"WARN not in map"

    filepath = os.path.join(SAVE_DIR, filename)

    # 已存在就跳过
    if os.path.exists(filepath):
        return f"⏭ 已有 {filename}"

    try:
        resp = requests.get(WIKI_BASE + name, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return f"FAIL 页面HTTP{resp.status_code}"

        soup = BeautifulSoup(resp.text, "html.parser")

        # 找 width=810 的图片（角色肖像标准尺寸）
        for img in soup.find_all("img"):
            w = img.get("width", "")
            if w == "810" or w == 810:
                src = img.get("src") or img.get("data-src") or ""
                if not src:
                    continue
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = "https://wiki.biligame.com" + src

                result = download_image(src, filepath)
                mark = "OK" if "OK" in result else "FAIL"
                return f"[{mark}] {filename} ({result})"

        # fallback: 找所有大图，取第一张 width >= 800 的非logo图
        for img in soup.find_all("img"):
            w = img.get("width", "0")
            try:
                wi = int(w)
            except (ValueError, TypeError):
                continue
            if 400 <= wi <= 1200:
                src = img.get("src") or img.get("data-src") or ""
                if not src or "logo" in src.lower():
                    continue
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = "https://wiki.biligame.com" + src
                result = download_image(src, filepath)
                return f"[FALLBACK] {filename} (w={wi}, {result})"

        return f"FAIL 未找到肖像图"

    except Exception as e:
        return f"FAIL 异常: {e}"


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)

    # 只下载缺失的（已有16张跳过）
    existing = set(os.listdir(SAVE_DIR))
    todo = [n for n, f in NAME_MAP.items() if f not in existing]

    if not todo:
        print("All character portraits already exist!")
        return

    print(f"Total: {len(NAME_MAP)} chars, Have: {len(existing)}, Need: {len(todo)}\n")

    ok = 0
    fail = 0
    skip = 0

    for i, name in enumerate(todo, 1):
        print(f"[{i:02d}/{len(todo)}] {name}  ", end="", flush=True)
        result = fetch_portrait(name)
        print(result)

        if result.startswith("[OK]") or result.startswith("[FALLBACK]"):
            ok += 1
        elif result.startswith("SKIP"):
            skip += 1
        else:
            fail += 1

        time.sleep(0.6)

    print(f"\n{'='*50}")
    print(f"Done! OK: {ok}  Skip: {skip}  Fail: {fail}")
    print(f"Saved to: {SAVE_DIR}")


if __name__ == "__main__":
    main()
