"""
第五人格主题 Todo Web 应用 — 双人独立版
欧利蒂斯庄园 - 求生任务手册
"""

import os
import random
from flask import Flask, render_template, request, jsonify

import todo  # 复用现有数据模型

app = Flask(__name__)

# 生产环境配置（Render / PythonAnywhere 均视为生产环境）
is_production = os.environ.get("RENDER") or os.environ.get("PYTHONANYWHERE_DOMAIN")
app.config["DEBUG"] = not is_production  # debug=False in production

# 数据文件路径（支持 Render 持久磁盘）
DATA_DIR = os.environ.get("DATA_DIR", ".")

# ── 双人独立数据源 ─────────────────────────────────────────
manager_a = todo.TodoManager(data_file=os.path.join(DATA_DIR, "playerA_todos.json"))
manager_b = todo.TodoManager(data_file=os.path.join(DATA_DIR, "playerB_todos.json"))


def _get_manager(player: str = "A") -> todo.TodoManager:
    """根据 player 参数返回对应的 TodoManager 实例"""
    return manager_b if player == "B" else manager_a


# ── 角色本地图片路径（放图后自动用，没图则用 emoji）──
CHARACTER_IMAGES = {
    # 求生者
    "医生": "images/characters/doctor.png",
    "园丁": "images/characters/gardener.png",
    "律师": "images/characters/lawyer.png",
    "慈善家": "images/characters/philanthropist.png",
    "机械师": "images/characters/mechanic.png",
    "前锋": "images/characters/forward.png",
    "佣兵": "images/characters/mercenary.png",
    "调香师": "images/characters/perfumer.png",
    "空军": "images/characters/coordinator.png",
    "祭司": "images/characters/priestess.png",
    "盲女": "images/characters/mindseye.png",
    "先知": "images/characters/seer.png",
    "入殓师": "images/characters/embalmer.png",
    "咒术师": "images/characters/enchantress.png",
    "勘探员": "images/characters/prospector.png",
    "野人": "images/characters/wildling.png",
    "杂技演员": "images/characters/acrobat.png",
    "大副": "images/characters/firstofficer.png",
    "守墓人": "images/characters/gravekeeper.png",
    "囚徒": "images/characters/prisoner.png",
    "昆虫学者": "images/characters/entomologist.png",
    "击球手": "images/characters/batter.png",
    "心理学者": "images/characters/psychologist.png",
    "病患": "images/characters/patient.png",
    "哭泣小丑": "images/characters/weepingclown.png",
    "教授": "images/characters/professor.png",
    "古董商": "images/characters/antiquarian.png",
    "作曲家": "images/characters/composer.png",
    "记者": "images/characters/journalist.png",
    "拉拉队员": "images/characters/cheerleader.png",
    "消防员": "images/characters/firefighter.png",
    # 监管者
    "杰克": "images/characters/jack.png",
    "小丑": "images/characters/joker.png",
    "蜘蛛": "images/characters/spider.png",
    "红蝶": "images/characters/geisha.png",
    "黄衣之主": "images/characters/feaster.png",
    "宿伞之魂": "images/characters/wuchang.png",
    "摄影师": "images/characters/photographer.png",
    "梦之女巫": "images/characters/dreamwitch.png",
    "厂长": "images/characters/hellember.png",
    "鹿头": "images/characters/gamekeeper.png",
    "疯眼": "images/characters/madeyes.png",
    "爱哭鬼": "images/characters/axeboy.png",
    "红夫人": "images/characters/bloodyqueen.png",
    "小提琴家": "images/characters/violinist.png",
    "雕刻家": "images/characters/sculptor.png",
    "邦邦": "images/characters/guard26.png",
    "使徒": "images/characters/disciple.png",
    "渔女": "images/characters/naiad.png",
    "博士": "images/characters/undead.png",
    "蜡像师": "images/characters/waxartist.png",
    "破轮": "images/characters/breakingwheel.png",
    "噩梦": "images/characters/nightmare.png",
    "记录员": "images/characters/clerk.png",
    "隐士": "images/characters/hermit.png",
    "守夜人": "images/characters/nightwatch.png",
    "歌剧演员": "images/characters/operasinger.png",
    "时空之影": "images/characters/shadowoftime.png",
    "艾维": "images/characters/ivy.png",
}

# ── 角色图标映射（可用图片时被替代）──────────────────
SURVIVOR_ICONS = {
    "医生": "💉",
    "园丁": "🌿",
    "律师": "⚖️",
    "慈善家": "🔦",
    "机械师": "⚙️",
    "前锋": "🏈",
    "佣兵": "🗡️",
    "调香师": "🧴",
    "空军": "🪂",
    "祭司": "🕳️",
    "盲女": "🦯",
    "先知": "🦉",
    "入殓师": "⚰️",
    "咒术师": "🧿",
    "勘探员": "⛏️",
    "野人": "🐗",
    "杂技演员": "🤹",
    "大副": "🧭",
    "守墓人": "🪦",
    "囚徒": "⚡",
    "昆虫学者": "🦋",
    "击球手": "🏏",
    "心理学者": "🧠",
    "病患": "🩼",
    "哭泣小丑": "🎪",
    "教授": "🧪",
    "古董商": "🏺",
    "作曲家": "🎼",
    "记者": "📰",
    "拉拉队员": "📣",
    "消防员": "🔥",
}

HUNTER_ICONS = {
    "杰克": "🔪",
    "小丑": "🤡",
    "蜘蛛": "🕷️",
    "红蝶": "🦋",
    "黄衣之主": "🐙",
    "宿伞之魂": "☂️",
    "摄影师": "📷",
    "梦之女巫": "👁️",
    "厂长": "🔥",
    "鹿头": "🪝",
    "疯眼": "🏰",
    "爱哭鬼": "🪓",
    "红夫人": "🪞",
    "小提琴家": "🎻",
    "雕刻家": "🗿",
    "邦邦": "🤖",
    "使徒": "🐈",
    "渔女": "🧜",
    "博士": "💀",
    "蜡像师": "🕯️",
    "破轮": "🛞",
    "噩梦": "👻",
    "记录员": "📋",
    "隐士": "⚡",
    "守夜人": "🌙",
    "歌剧演员": "🎭",
    "时空之影": "⏳",
    "艾维": "🪴",
}

# ── 角色经典台词 ──
CHARACTER_QUOTES = {
    # 求生者
    "医生": "救死扶伤是我的天职，别担心，我会治好你的。",
    "园丁": "每一朵花都有它绽放的理由，正如每一个人。",
    "律师": "真相永远只有一个，而我终将找到它。",
    "慈善家": "黑暗中总有一束光，希望永不熄灭。",
    "机械师": "机械不说谎，它比人心更可靠。",
    "前锋": "冲过去，别回头！希望就在前方。",
    "佣兵": "为了活下去，必须战斗到最后。",
    "调香师": "每一缕香气都是一段无法磨灭的记忆。",
    "空军": "天空是我的战场，信号弹会指引方向。",
    "祭司": "神明指引着我的道路，穿越迷雾吧。",
    "盲女": "我看不见，但我能感知这世间的一切。",
    "先知": "未来并非不可改变，相信你的选择。",
    "入殓师": "死亡不是终点，而是另一段旅程的开始。",
    "咒术师": "古老的咒语守护着我，邪恶终将消散。",
    "勘探员": "地下埋藏着无数秘密，磁铁会告诉你答案。",
    "野人": "自然才是最好的伙伴，冲啊！",
    "杂技演员": "生活就是一场表演，精彩永不落幕。",
    "大副": "大海不会背叛勇敢的水手。",
    "守墓人": "安息吧，逝去的灵魂。我将守护这片土地。",
    "囚徒": "牢笼困不住自由的灵魂，电流会为我开路。",
    "昆虫学者": "每一个微小的生命都值得被尊重。",
    "击球手": "挥出漂亮的一击，这就是我的节奏！",
    "心理学者": "人心是最难解的谜题，也是最迷人的。",
    "病患": "疯狂与天才只在一线之间，你分得清吗？",
    "哭泣小丑": "笑容背后藏着多少泪水，你永远不会知道。",
    "教授": "知识是最强大的武器，鳞片会保护我。",
    "古董商": "每一件古物都有它的故事，你听见了吗？",
    "作曲家": "音符是我的语言，旋律中藏着力量。",
    "记者": "真相值得用一切去交换，哪怕生命。",
    "拉拉队员": "加油！你可以的！永远不要放弃！",
    "消防员": "火场中只有向前没有后退，抓紧我！",
    # 监管者
    "杰克": "优雅，才是杀戮真正的艺术。",
    "小丑": "欢笑吧，在绝望中起舞吧！",
    "蜘蛛": "落入网中的猎物，再也无处可逃。",
    "红蝶": "舞姿翩翩，刹那生灭，你逃不掉的。",
    "黄衣之主": "深海之下，不可名状的恐怖在呼唤。",
    "宿伞之魂": "黑白无常，生死之间，无人能逃脱宿命。",
    "摄影师": "时光定格，永恒即是刹那，美永不消逝。",
    "梦之女巫": "你的梦境由我主宰，睡去吧，永远地。",
    "厂长": "庄园的规矩由我制定，反抗是徒劳的。",
    "鹿头": "森林中的猎手从不失手，你跑不掉的。",
    "疯眼": "围墙之内皆是牢笼，困住的不只是身体。",
    "爱哭鬼": "哭泣吧，没有人会来救你……没有人。",
    "红夫人": "美貌与鲜血同样令人窒息，你选哪一个？",
    "小提琴家": "死亡的乐章由我来演奏，请静静聆听。",
    "雕刻家": "石头中藏着永恒，你们不过是过客。",
    "邦邦": "倒计时是最美的旋律，爆炸是最后的掌声。",
    "使徒": "信仰能拯救你吗？让我来验证一下。",
    "渔女": "水下的世界更加冰冷，来陪我吧。",
    "博士": "生与死的界限由我来改写，实验开始了。",
    "蜡像师": "永恒的温度是冰冷，永远定格吧。",
    "破轮": "碾压一切阻挡之物，车轮不会停下。",
    "噩梦": "恐惧才是最真实的，永远不要入睡。",
    "记录员": "你的每一次行动都被记录在案，无处遁形。",
    "隐士": "雷电之中无人能逃，天罚将至。",
    "守夜人": "黑暗中我无处不在，风吹过即是终结。",
    "歌剧演员": "舞台上的每一秒都是绝唱，谢幕吧。",
    "时空之影": "时间的裂痕中藏着无尽的可能。",
    "艾维": "自然的法则不可违背，凋零是必然。",
}

CHARACTER_ROLES = {
    # 求生者
    "医生": "救援型 · 随身携带镇静剂，可治疗自己",
    "园丁": "破译型 · 擅长拆除狂欢之椅",
    "律师": "辅助型 · 携带地图，不会被震慑",
    "慈善家": "牵制型 · 手电筒照射可眩晕监管者",
    "机械师": "破译型 · 可操控傀儡同时破译",
    "前锋": "救援型 · 橄榄球冲刺可撞晕监管者",
    "佣兵": "救援型 · 身手敏捷，铁屁股",
    "调香师": "牵制型 · 喷洒香水可回溯位置",
    "空军": "救援型 · 信号枪可眩晕监管者",
    "祭司": "辅助型 · 开启超长通道传送队友",
    "盲女": "破译型 · 盲杖探测监管者位置",
    "先知": "辅助型 · 役鸟可抵挡一次伤害",
    "入殓师": "辅助型 · 棺材可远程复活队友",
    "咒术师": "牵制型 · 咒像可麻痹监管者",
    "勘探员": "牵制型 · 磁铁吸引或弹开监管者",
    "野人": "救援型 · 骑野猪冲刺救援",
    "杂技演员": "牵制型 · 三种投掷弹灵活牵制",
    "大副": "救援型 · 怀表催眠可隐身救援",
    "守墓人": "救援型 · 铲子遁地救援队友",
    "囚徒": "破译型 · 远程连接破译密码机",
    "昆虫学者": "辅助型 · 虫群推动可跨越地形",
    "击球手": "救援型 · 板球击退监管者",
    "心理学者": "辅助型 · 远程催眠治疗队友",
    "病患": "牵制型 · 钩爪抓取快速位移",
    "哭泣小丑": "救援型 · 火箭加速冲刺救援",
    "教授": "牵制型 · 鳞片硬化阻挡伤害",
    "古董商": "牵制型 · 机关箫击退监管者",
    "作曲家": "破译型 · 音律加速破译密码机",
    "记者": "辅助型 · 相机拍摄获取情报",
    "拉拉队员": "辅助型 · 加油助威提升队友",
    "消防员": "救援型 · 水枪冲射救援队友",
    # 监管者
    "杰克": "追击型 · 雾刃远程攻击",
    "小丑": "追击型 · 火箭冲刺快速追击",
    "蜘蛛": "守尸型 · 蛛网陷阱减速求生者",
    "红蝶": "追击型 · 刹那生灭瞬移至求生者背后",
    "黄衣之主": "控场型 · 触手攻击范围压制",
    "宿伞之魂": "控场型 · 双形态切换传送全图",
    "摄影师": "控场型 · 开启相中世界造成伤害",
    "梦之女巫": "控场型 · 操控信徒分身围猎",
    "厂长": "追击型 · 召唤分身传送追击",
    "鹿头": "追击型 · 锁链钩爪拉回求生者",
    "疯眼": "控场型 · 控制台升起围墙封锁区域",
    "爱哭鬼": "追击型 · 怨灵加速追击",
    "红夫人": "追击型 · 镜像瞬移攻击",
    "小提琴家": "追击型 · 音符减速区域攻击",
    "雕刻家": "控场型 · 石像冲锋封锁走位",
    "邦邦": "守尸型 · 定时炸弹范围压制",
    "使徒": "追击型 · 猫跳跃禁锢求生者",
    "渔女": "控场型 · 水渊减速范围伤害",
    "博士": "追击型 · 能量跳跃范围攻击",
    "蜡像师": "控场型 · 蜡油凝固封锁行动",
    "破轮": "追击型 · 车轮形态加速追击",
    "噩梦": "追击型 · 乌鸦传送突袭",
    "记录员": "控场型 · 记录行为回退操作",
    "隐士": "控场型 · 雷电连锁范围伤害",
    "守夜人": "追击型 · 风刃加速追击",
    "歌剧演员": "追击型 · 暗影穿梭瞬移到背后",
    "时空之影": "控场型 · 时空裂隙操控战场",
    "艾维": "控场型 · 藤蔓缠绕封锁地形",
}


def _task_to_dict(t: todo.Task) -> dict:
    """将 Task 对象转为前端友好的 dict，附带优先级标签"""
    d = t.to_dict()
    d["priority_label"] = todo.priority_label(t.priority)
    return d


def _get_stats(manager: todo.TodoManager) -> dict:
    """获取指定管理器的统计信息"""
    total, done, pct = manager.get_stats()
    tasks = manager.get_all_tasks()
    pending = total - done
    high_pri = sum(1 for t in tasks if t.priority == 3 and not t.is_completed)
    quote = random.choice(todo.QUOTES)
    return {
        "total": total,
        "done": done,
        "pct": round(pct, 1),
        "pending": pending,
        "high_pri": high_pri,
        "quote": quote,
    }


@app.route("/api/daily-character", methods=["GET"])
def api_get_daily_character():
    """获取指定玩家的今日角色"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    dc = manager.get_daily_character()
    return jsonify(dc if dc else {})


@app.route("/api/daily-character", methods=["POST"])
def api_set_daily_character():
    """设置指定玩家的今日角色"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    data = request.get_json()
    name = data.get("name", "").strip()
    side = data.get("side", "survivor")
    if not name:
        return jsonify({"error": "角色名不能为空"}), 400
    manager.set_daily_character(name, side)
    return jsonify({"ok": True, "daily_character": name, "daily_side": side})


# ── 页面路由 ──────────────────────────────────────────────

@app.route("/")
def index():
    """主页 — 双人面板"""
    tasks_a = manager_a.get_all_tasks()
    sorted_a = sorted(tasks_a, key=lambda t: (t.is_completed, -t.priority, t.id))
    stats_a = _get_stats(manager_a)

    tasks_b = manager_b.get_all_tasks()
    sorted_b = sorted(tasks_b, key=lambda t: (t.is_completed, -t.priority, t.id))
    stats_b = _get_stats(manager_b)

    return render_template(
        "index.html",
        playerA_tasks=[_task_to_dict(t) for t in sorted_a],
        playerA_stats=stats_a,
        playerB_tasks=[_task_to_dict(t) for t in sorted_b],
        playerB_stats=stats_b,
        dailyA=manager_a.get_daily_character(),
        dailyB=manager_b.get_daily_character(),
        survivors=todo.SURVIVORS,
        hunters=todo.HUNTERS,
        survivor_icons=SURVIVOR_ICONS,
        hunter_icons=HUNTER_ICONS,
        character_roles=CHARACTER_ROLES,
        character_images=CHARACTER_IMAGES,
        character_quotes=CHARACTER_QUOTES,
        title_art=todo.TITLE_ART,
    )


# ── API 路由 ──────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    """获取所有任务"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    tasks = manager.get_all_tasks()
    sorted_tasks = sorted(tasks, key=lambda t: (t.is_completed, -t.priority))
    return jsonify([_task_to_dict(t) for t in sorted_tasks])


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    """添加新任务"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    data = request.get_json()
    content = data.get("content", "").strip()
    priority = data.get("priority", 1)

    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    if priority not in (1, 2, 3):
        priority = 1

    manager.add_task(content, priority)
    # 新任务在列表末尾
    new_task = manager.get_all_tasks()[-1]

    # 随机分配一个求生者角色
    survivor = todo.SURVIVORS[hash(content) % len(todo.SURVIVORS)]
    survivor_icon = SURVIVOR_ICONS.get(survivor, "")

    return jsonify({**_task_to_dict(new_task), "survivor": survivor, "survivor_icon": survivor_icon}), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_edit_task(task_id):
    """编辑任务内容和/或优先级"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    data = request.get_json()
    content = data.get("content", "").strip()
    priority = data.get("priority")

    t = next((x for x in manager.get_all_tasks() if x.id == task_id), None)
    if t is None:
        return jsonify({"error": "未找到任务"}), 404

    if content:
        manager.edit_task(task_id, content)
    if priority in (1, 2, 3):
        manager.set_priority(task_id, priority)

    t = next((x for x in manager.get_all_tasks() if x.id == task_id), None)
    return jsonify(_task_to_dict(t))


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    """删除任务"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    ok = manager.delete_task(task_id)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"error": "未找到任务"}), 404


@app.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
def api_toggle_task(task_id):
    """切换任务完成状态"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    t = next((x for x in manager.get_all_tasks() if x.id == task_id), None)
    if t is None:
        return jsonify({"error": "未找到任务"}), 404

    if t.is_completed:
        manager.mark_uncompleted(task_id)
    else:
        manager.mark_completed(task_id)

    t = next((x for x in manager.get_all_tasks() if x.id == task_id), None)
    hunter = todo.HUNTERS[task_id % len(todo.HUNTERS)]
    hunter_icon = HUNTER_ICONS.get(hunter, "")
    return jsonify({**_task_to_dict(t), "hunter": hunter, "hunter_icon": hunter_icon})


@app.route("/api/tasks/reorder", methods=["POST"])
def api_reorder_tasks():
    """拖拽排序后批量更新任务顺序"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    data = request.get_json()
    ordered_ids = data.get("order", [])
    if not isinstance(ordered_ids, list) or not ordered_ids:
        return jsonify({"error": "无效的排序数据"}), 400
    ok = manager.reorder_tasks(ordered_ids)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"error": "排序数据与任务列表不匹配"}), 400


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """获取统计数据"""
    player = request.args.get("player", "A")
    manager = _get_manager(player)
    return jsonify(_get_stats(manager))


# ── 启动入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    print(todo.TITLE_ART)
    if is_production:
        print("  ◆ 生产模式启动 (gunicorn 请直接 import app)")
    else:
        print("  ◆ 双人独立版 Web 已启动，打开浏览器访问 http://127.0.0.1:5000")
        print()
        app.run(debug=True, host="127.0.0.1", port=5000)
