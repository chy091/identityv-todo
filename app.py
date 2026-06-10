"""
第五人格主题 Todo Web 应用
欧利蒂斯庄园 - 求生任务手册
"""

import os
import random
from flask import Flask, render_template, request, jsonify

import todo  # 复用现有数据模型

app = Flask(__name__)

# 生产环境配置
is_production = os.environ.get("RENDER", False)
app.config["DEBUG"] = not is_production  # debug=False in production

# 数据文件路径（支持 Render 持久磁盘）
DATA_DIR = os.environ.get("DATA_DIR", ".")
todo.DATA_FILE = os.path.join(DATA_DIR, "todos.json")

manager = todo.TodoManager()

# ── 角色本地图片路径（放图后自动用，没图则用 emoji）──
CHARACTER_IMAGES = {
    "医生": "images/characters/doctor.png",
    "园丁": "images/characters/gardener.png",
    "律师": "images/characters/lawyer.png",
    "慈善家": "images/characters/philanthropist.png",
    "机械师": "images/characters/mechanic.png",
    "前锋": "images/characters/forward.png",
    "佣兵": "images/characters/mercenary.png",
    "调香师": "images/characters/perfumer.png",
    "杰克": "images/characters/jack.png",
    "小丑": "images/characters/joker.png",
    "蜘蛛": "images/characters/spider.png",
    "红蝶": "images/characters/geisha.png",
    "黄衣之主": "images/characters/feaster.png",
    "宿伞之魂": "images/characters/wuchang.png",
    "摄影师": "images/characters/photographer.png",
    "梦之女巫": "images/characters/dreamwitch.png",
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
}

CHARACTER_ROLES = {
    "医生": "救援型 · 随身携带镇静剂，可治疗自己",
    "园丁": "破译型 · 擅长拆除狂欢之椅",
    "律师": "辅助型 · 携带地图，不会被震慑",
    "慈善家": "牵制型 · 手电筒照射可眩晕监管者",
    "机械师": "破译型 · 可操控傀儡同时破译",
    "前锋": "救援型 · 橄榄球冲刺可撞晕监管者",
    "佣兵": "救援型 · 身手敏捷，铁屁股",
    "调香师": "牵制型 · 喷洒香水可回溯位置",
    "杰克": "追击型 · 雾刃远程攻击",
    "小丑": "追击型 · 火箭冲刺快速追击",
    "蜘蛛": "守尸型 · 蛛网陷阱减速求生者",
    "红蝶": "追击型 · 刹那生灭瞬移至求生者背后",
    "黄衣之主": "控场型 · 触手攻击范围压制",
    "宿伞之魂": "控场型 · 双形态切换传送全图",
    "摄影师": "控场型 · 开启相中世界造成伤害",
    "梦之女巫": "控场型 · 操控信徒分身围猎",
}


def _task_to_dict(t: todo.Task) -> dict:
    """将 Task 对象转为前端友好的 dict，附带优先级标签"""
    d = t.to_dict()
    d["priority_label"] = todo.priority_label(t.priority)
    return d


def _get_stats() -> dict:
    """获取统计信息"""
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


# ── 页面路由 ──────────────────────────────────────────────

@app.route("/")
def index():
    """主页"""
    tasks = manager.get_all_tasks()
    sorted_tasks = sorted(tasks, key=lambda t: (t.is_completed, -t.priority, t.id))
    stats = _get_stats()
    return render_template(
        "index.html",
        tasks=[_task_to_dict(t) for t in sorted_tasks],
        stats=stats,
        survivors=todo.SURVIVORS,
        hunters=todo.HUNTERS,
        survivor_icons=SURVIVOR_ICONS,
        hunter_icons=HUNTER_ICONS,
        character_roles=CHARACTER_ROLES,
        character_images=CHARACTER_IMAGES,
        title_art=todo.TITLE_ART,
    )


# ── API 路由 ──────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    """获取所有任务"""
    tasks = manager.get_all_tasks()
    sorted_tasks = sorted(tasks, key=lambda t: (t.is_completed, -t.priority, t.id))
    return jsonify([_task_to_dict(t) for t in sorted_tasks])


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    """添加新任务"""
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
    ok = manager.delete_task(task_id)
    if ok:
        return jsonify({"ok": True})
    return jsonify({"error": "未找到任务"}), 404


@app.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
def api_toggle_task(task_id):
    """切换任务完成状态"""
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


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """获取统计数据"""
    return jsonify(_get_stats())


# ── 启动入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    print(todo.TITLE_ART)
    if is_production:
        print("  ◆ 生产模式启动 (gunicorn 请直接 import app)")
    else:
        print("  ◆ Web 版已启动，打开浏览器访问 http://127.0.0.1:5000")
        print()
        app.run(debug=True, host="127.0.0.1", port=5000)
