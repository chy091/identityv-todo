import json
import os
import sys
import io
from datetime import datetime

# 强制 UTF-8 输出，解决 Windows GBK 终端编码问题
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except (AttributeError, OSError):
        pass

DATA_FILE = "todos.json"

# ── 第五人格主题角色映射 ──
SURVIVORS = ["医生", "园丁", "律师", "慈善家", "机械师", "前锋", "佣兵", "调香师"]
HUNTERS = ["杰克", "小丑", "蜘蛛", "红蝶", "黄衣之主", "宿伞之魂", "摄影师", "梦之女巫"]

TITLE_ART = r"""
  +=============================================================+
  |  |~|~|~|  |~|~|~|~|  |~|~|~|~| |~|~|~|~|~| |~| |~|~| |~|  |
  |  |~| |__|~| |~|_____| |~|_____| |__|~|__| |~| |__|~| |~|~| |
  |  |~| |  |~| |~|____  |~|_____    |~|    |~| |~|~|~| |~|~|  |
  |  |~| |  |~| |~|___|  |_____|~|   |~|    |~| |~| |_|~| |~|   |
  |  |~|~|~|~|  |~|~|~|~| |~|~|~|~|   |~|     |~|  |~| |~| |~|  |
  |  |_______| |_______| |_______|   |_|     |_|  |_| |_| |_|  |
  |                                                               |
  |     * 欧 利 蒂 斯 庄 园 - 求 生 任 务 手 册 *                 |
  +=============================================================+
"""

QUOTES = [
    "「唯有破译密码机，才能打开逃生之门。」",
    "「监管者正在靠近……保持警惕。」",
    "「庄园的秘密，藏在地窖之下。」",
    "「完美的救援，需要完美的时机。」",
    "「别回头，一直跑。」—— 瑟维 · 勒 · 罗伊",
    "「真相就在庄园深处，你会去寻找吗？」",
]


class Task:
    """单条任务 — 庄园中的一封信件"""

    def __init__(self, task_id: int, content: str, priority: int = 1):
        self.id = task_id
        self.content = content
        self.priority = priority  # 1-低 2-中 3-高
        self.is_completed = False
        self.created_at = datetime.now().isoformat()

    def mark_done(self):
        self.is_completed = True

    def mark_undone(self):
        self.is_completed = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "priority": self.priority,
            "is_completed": self.is_completed,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Task":
        t = Task(d["id"], d["content"], d.get("priority", 1))
        t.is_completed = d.get("is_completed", False)
        t.created_at = d.get("created_at", datetime.now().isoformat())
        return t


class TodoManager:
    """任务管家 — 庄园管家"""

    def __init__(self, data_file: str = None):
        self._data_file = data_file or DATA_FILE
        self.tasks: list[Task] = []
        self.counter = 1
        self.load()

    def _next_id(self) -> int:
        """返回下一个可用 ID 并自增计数"""
        c = self.counter
        self.counter += 1
        return c

    def _recalc_counter(self):
        """从已有任务中重新计算 counter（避免保存/加载导致 ID 回退）"""
        if self.tasks:
            self.counter = max(t.id for t in self.tasks) + 1
        else:
            self.counter = 1

    def add_task(self, content: str, priority: int = 1) -> bool:
        content = content.strip()
        if not content:
            return False
        self.tasks.append(Task(self._next_id(), content, priority))
        self.save()
        return True

    def delete_task(self, task_id: int) -> bool:
        new_tasks = [t for t in self.tasks if t.id != task_id]
        if len(new_tasks) == len(self.tasks):
            return False
        self.tasks = new_tasks
        self.save()
        return True

    def mark_completed(self, task_id: int) -> bool:
        for t in self.tasks:
            if t.id == task_id:
                t.mark_done()
                self.save()
                return True
        return False

    def mark_uncompleted(self, task_id: int) -> bool:
        for t in self.tasks:
            if t.id == task_id:
                t.mark_undone()
                self.save()
                return True
        return False

    def edit_task(self, task_id: int, new_content: str) -> bool:
        new_content = new_content.strip()
        if not new_content:
            return False
        for t in self.tasks:
            if t.id == task_id:
                t.content = new_content
                self.save()
                return True
        return False

    def set_priority(self, task_id: int, priority: int) -> bool:
        for t in self.tasks:
            if t.id == task_id:
                t.priority = priority
                self.save()
                return True
        return False

    def reorder_tasks(self, ordered_ids: list[int]) -> bool:
        """按给定的 ID 列表重新排列任务顺序（用于拖拽排序持久化）"""
        id_to_task = {t.id: t for t in self.tasks}
        if set(ordered_ids) != set(id_to_task.keys()):
            return False  # ID 不匹配，拒绝
        self.tasks = [id_to_task[tid] for tid in ordered_ids]
        self.save()
        return True

    def get_all_tasks(self) -> list[Task]:
        return self.tasks

    def get_stats(self) -> tuple[int, int, float]:
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.is_completed)
        progress = (done / total * 100) if total > 0 else 0
        return total, done, progress

    def save(self):
        data = {
            "counter": self.counter,
            "tasks": [t.to_dict() for t in self.tasks],
        }
        try:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load(self):
        if not os.path.exists(self._data_file):
            return
        try:
            with open(self._data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.counter = data.get("counter", 1)
            self.tasks = [Task.from_dict(d) for d in data.get("tasks", [])]
            self._recalc_counter()
        except (json.JSONDecodeError, OSError):
            self.tasks = []
            self.counter = 1


# ── UI 辅助函数 ──

def priority_label(p: int) -> str:
    """优先级 → 第五人格角色标签"""
    labels = {1: "✦ 求生者级", 2: "✦✦ 监管者级", 3: "✦✦✦ 梦之女巫级"}
    return labels.get(p, "✦ 求生者级")


def progress_bar(percent: float, width: int = 20) -> str:
    """第五人格风格进度条 — 模仿密码机破译进度"""
    filled = int(percent / 100 * width)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent:.0f}%"


def cipher_animation():
    """密码机破译动画特效"""
    import time
    frames = ["⚙  ", "⟳⚙ ", " ↻⚙", "  ⚙", "⚙  ", "⟳⚙ "]
    for _ in range(8):
        for f in frames:
            sys.stdout.write(f"\r     {f} 密码机破译中……")
            sys.stdout.flush()
            time.sleep(0.04)
    sys.stdout.write("\r" + " " * 30 + "\r")


def read_int(prompt: str, min_val: int = 1, max_val: int = 999999) -> int | None:
    """安全读取整数，异常时返回 None"""
    try:
        val = int(input(prompt))
        if min_val <= val <= max_val:
            return val
        print(f"  请输入 {min_val} 到 {max_val} 之间的数字。")
        return None
    except ValueError:
        print("  输入无效，请输入一个整数。")
        return None


def press_enter():
    input("\n  按回车键返回主菜单……")


def show_menu():
    print()
    print("  ┌─────────────────────────────────────┐")
    print("  │  1. 📜  查看任务     (侦查庄园)      │")
    print("  │  2. ✉   添加任务     (接收信件)      │")
    print("  │  3. 🔧  标记完成     (破译密码机)    │")
    print("  │  4. ⛏   删除任务     (拆除陷阱)      │")
    print("  │  5. ✎   编辑任务     (修改密文)      │")
    print("  │  6. ⚑   调整优先级   (更换角色)      │")
    print("  │  7. ⛔  取消完成标记 (重置密码机)    │")
    print("  │  8. 📊  任务统计     (庄园情报)      │")
    print("  │  0. 🚪  逃离庄园                     │")
    print("  └─────────────────────────────────────┘")


def show_tasks(manager: TodoManager):
    tasks = manager.get_all_tasks()
    if not tasks:
        print("\n  ⚠ 当前没有信件。庄园静悄悄的……")
        return

    print(f"\n  ════════════════ 庄园信件一览 ════════════════")
    # 排序：未完成优先，高优先级优先
    sorted_tasks = sorted(tasks, key=lambda t: (t.is_completed, -t.priority, t.id))
    for t in sorted_tasks:
        mark = "✓" if t.is_completed else "○"
        strike = "\033[9m" if t.is_completed else ""
        reset = "\033[0m" if t.is_completed else ""
        print(f"  [{mark}] #{t.id:<3} {priority_label(t.priority):<14} "
              f"{strike}{t.content[:32]}{'…' if len(t.content) > 32 else ''}{reset}")
    print("  ═══════════════════════════════════════════════")

    total, done, pct = manager.get_stats()
    print(f"  密码机破译进度：{progress_bar(pct)}  ({done}/{total})")


def add_task_flow(manager: TodoManager):
    print("\n  —— ✉ 接收新信件 ——")
    content = input("  请输入任务内容：").strip()
    if not content:
        print("  ❌ 信件内容不能为空！")
        return

    print("  请选择优先级：")
    print("    1. 求生者级  (普通)")
    print("    2. 监管者级  (重要)")
    print("    3. 梦之女巫级 (紧急)")
    p = read_int("  请输入 1-3：", min_val=1, max_val=3)
    priority = p if p else 1

    if manager.add_task(content, priority):
        cipher_animation()
        survivor = SURVIVORS[content.__hash__() % len(SURVIVORS)]
        print(f"  ✓ 信件已归档。{survivor} 将协助你完成此任务。")
    else:
        print("  ❌ 添加失败。")


def complete_task_flow(manager: TodoManager):
    print("\n  —— 🔧 破译密码机 ——")
    show_tasks(manager)
    tid = read_int("  请输入要标记完成的任务 ID（输入 0 取消）：", min_val=0)
    if tid is None or tid == 0:
        return
    if manager.mark_completed(tid):
        cipher_animation()
        hunter = HUNTERS[tid % len(HUNTERS)]
        print(f"  ✓ 密码机破译成功！{hunter} 暂时没有发现你。")
    else:
        print("  ❌ 未找到该 ID 的任务。")


def delete_task_flow(manager: TodoManager):
    print("\n  —— ⛏ 拆除陷阱 ——")
    show_tasks(manager)
    tid = read_int("  请输入要删除的任务 ID（输入 0 取消）：", min_val=0)
    if tid is None or tid == 0:
        return
    if manager.delete_task(tid):
        print("  ✓ 陷阱已拆除，任务已删除。")
    else:
        print("  ❌ 未找到该 ID 的任务。")


def edit_task_flow(manager: TodoManager):
    print("\n  —— ✎ 修改密文 ——")
    show_tasks(manager)
    tid = read_int("  请输入要编辑的任务 ID（输入 0 取消）：", min_val=0)
    if tid is None or tid == 0:
        return
    # 查找该任务确认存在
    target = next((t for t in manager.get_all_tasks() if t.id == tid), None)
    if target is None:
        print("  ❌ 未找到该 ID 的任务。")
        return
    print(f"  当前内容：{target.content}")
    new_content = input("  请输入新内容：").strip()
    if manager.edit_task(tid, new_content):
        print("  ✓ 密文已修改。")
    else:
        print("  ❌ 内容不能为空。")


def priority_flow(manager: TodoManager):
    print("\n  —— ⚑ 更换角色（调整优先级） ——")
    show_tasks(manager)
    tid = read_int("  请输入要调整的任务 ID（输入 0 取消）：", min_val=0)
    if tid is None or tid == 0:
        return
    target = next((t for t in manager.get_all_tasks() if t.id == tid), None)
    if target is None:
        print("  ❌ 未找到该 ID 的任务。")
        return
    print(f"  当前优先级：{priority_label(target.priority)}")
    print("  新优先级：1-求生者级  2-监管者级  3-梦之女巫级")
    p = read_int("  请输入 1-3：", min_val=1, max_val=3)
    if p and manager.set_priority(tid, p):
        print(f"  ✓ 角色切换为 {priority_label(p)}。")
    else:
        print("  ❌ 操作取消。")


def uncomplete_flow(manager: TodoManager):
    print("\n  —— ⛔ 重置密码机 ——")
    show_tasks(manager)
    tid = read_int("  请输入要取消完成的任务 ID（输入 0 取消）：", min_val=0)
    if tid is None or tid == 0:
        return
    if manager.mark_uncompleted(tid):
        print("  ✓ 密码机已重置，任务恢复为未完成。")
    else:
        print("  ❌ 未找到该 ID 的任务。")


def stats_flow(manager: TodoManager):
    total, done, pct = manager.get_stats()
    pending = total - done
    high_pri = sum(1 for t in manager.get_all_tasks() if t.priority == 3 and not t.is_completed)

    print("\n  ════════════════ 庄园情报 ════════════════")
    print(f"  📬  信件总数：   {total}")
    print(f"  ✓   已完成：     {done}")
    print(f"  ○   待处理：     {pending}")
    print(f"  ⚠   紧急信件：   {high_pri}")
    print(f"  📊  破译进度：   {progress_bar(pct)}")
    print()

    if pct == 100 and total > 0:
        print("  🎉 所有密码机已破译！地窖已开启，快逃离庄园吧！")
    elif high_pri > 0:
        print(f"  ⚡ 警告：还有 {high_pri} 封梦之女巫级紧急信件待处理！")
    elif pending == 0 and total > 0:
        print("  ✓ 所有任务已完成。")
    else:
        hunter = HUNTERS[pending % len(HUNTERS)]
        print(f"  👁  {hunter} 正在庄园中巡逻……尽快完成任务。")

    import random
    print(f"  💬  {random.choice(QUOTES)}")
    print("  ═════════════════════════════════════════════")


def main_loop():
    manager = TodoManager()

    # 首次使用检测
    if not os.path.exists(DATA_FILE):
        print(TITLE_ART)
        print("  ◆ 欢迎来到欧利蒂斯庄园，勇敢的求生者。")
        print("  ◆ 在这座庄园中，你需要完成所有任务才能逃离。")
        print("  ◆ 记住：密码机是你的目标，监管者是你的威胁。")
        press_enter()

    while True:
        show_menu()
        choice = input("\n  请选择操作 [0-8]：").strip()

        if choice == "1":
            show_tasks(manager)
            press_enter()

        elif choice == "2":
            add_task_flow(manager)
            press_enter()

        elif choice == "3":
            complete_task_flow(manager)
            press_enter()

        elif choice == "4":
            delete_task_flow(manager)
            press_enter()

        elif choice == "5":
            edit_task_flow(manager)
            press_enter()

        elif choice == "6":
            priority_flow(manager)
            press_enter()

        elif choice == "7":
            uncomplete_flow(manager)
            press_enter()

        elif choice == "8":
            stats_flow(manager)
            press_enter()

        elif choice == "0":
            total, done, _ = manager.get_stats()
            if total > 0 and done == total:
                print("\n  🎉 所有密码机已破译！你成功逃离了庄园！")
            else:
                remaining = total - done
                print(f"\n  🏃 你逃离了庄园，但还有 {remaining} 台密码机未破译……")
                print("  庄园的秘密，终有一天会揭晓。")
            print("  再见，求生者。\n")
            break

        else:
            print("  ❌ 无效选项，请输入 0 到 8 之间的数字。")


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n\n  ⚡ 求生者突然倒地……程序已退出。\n")
