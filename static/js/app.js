/**
 * 第五人格主题 Todo App — 双人独立版 前端交互
 * 欧利蒂斯庄园 - 求生任务手册
 *
 * 架构：TaskPanel 类封装每个玩家的完整面板逻辑
 *   - 零全局变量存储任务数据
 *   - 所有 DOM 查询通过 this.container.querySelector 作用域隔离
 *   - 每个实例拥有独立的 modals / stats / task list
 *   - API 调用附带 ?player=A 或 ?player=B 实现后端数据隔离
 */

// ════════════════ 工具函数 ════════════════

function escapeHtml(str) {
  const el = document.createElement('span');
  el.textContent = str;
  return el.innerHTML;
}

function priorityLabel(p) {
  const labels = { 1: '✦ 求生者级', 2: '✦✦ 监管者级', 3: '✦✦✦ 梦之女巫级' };
  return labels[p] || labels[1];
}

function getPriorityFromBadge(className) {
  if (className.includes('priority-1')) return '1';
  if (className.includes('priority-2')) return '2';
  if (className.includes('priority-3')) return '3';
  return '2';
}


// ════════════════ TaskPanel 类 ════════════════

class TaskPanel {

  /**
   * @param {Object}  options
   * @param {Element} options.container  - 面板根 DOM 元素 (.player-panel)
   * @param {string}  options.playerKey  - 'A' 或 'B'，用于 API 查询参数
   * @param {string}  options.playerName - 显示用的玩家名（如 '求生者A'）
   */
  constructor({ container, playerKey, playerName }) {
    this.container = container;
    this.playerKey = playerKey;       // 'A' | 'B'
    this.playerName = playerName;     // 显示名
    this.apiParam = '?player=' + playerKey;

    try {
      // ── 缓存 DOM 引用（全部作用域内查询）──
      this._cacheDom();

      // ── 事件绑定 ──
      this._bindEvents();

      // ── 注册到全局实例列表 ──
      TaskPanel._instances.push(this);

      // ── 初始统计刷新 ──
      this.refreshStats();

      console.log('[TaskPanel] ' + playerName + ' 初始化成功');
    } catch (err) {
      console.error('[TaskPanel] ' + playerName + ' 初始化失败:', err);
    }
  }

  // 静态实例列表（用于全局键盘事件等）
  // 兼容旧浏览器：不用 static 类字段语法
  static get _instances() {
    if (!this.__instances) this.__instances = [];
    return this.__instances;
  }

  // ════════════ DOM 缓存 ════════════
  _cacheDom() {
    const c = this.container;

    // 添加表单
    this.addForm      = c.querySelector('.js-add-form');
    this.taskInput    = c.querySelector('.js-task-input');
    this.taskPriority = c.querySelector('.js-priority-select');
    this.addError     = c.querySelector('.js-add-error');
    this.addBtn       = c.querySelector('.js-add-btn');
    this.cipherToast  = c.querySelector('.js-cipher-toast');
    this.cipherIcon   = c.querySelector('.js-cipher-icon');
    this.cipherMsg    = c.querySelector('.js-cipher-msg');

    // 任务列表
    this.taskList   = c.querySelector('.js-task-list');
    this.emptyState = c.querySelector('.js-empty-state');

    // 统计
    this.statTotal    = c.querySelector('.js-stat-total');
    this.statDone     = c.querySelector('.js-stat-done');
    this.statPending  = c.querySelector('.js-stat-pending');
    this.statHighPri  = c.querySelector('.js-stat-high-pri');
    this.progressFill = c.querySelector('.js-progress-fill');
    this.progressText = c.querySelector('.js-progress-text');
    this.statsHint    = c.querySelector('.js-stats-hint');

    // 编辑弹窗
    this.editModal      = c.querySelector('.js-edit-modal');
    this.editTaskId     = c.querySelector('.js-edit-task-id');
    this.editContent    = c.querySelector('.js-edit-content');
    this.editPriority   = c.querySelector('.js-edit-priority');
    this.editError      = c.querySelector('.js-edit-error');
    this.saveEditBtn    = c.querySelector('.js-save-edit-btn');
    this.cancelEditBtn  = c.querySelector('.js-cancel-edit-btn');

    // 删除弹窗
    this.deleteModal        = c.querySelector('.js-delete-modal');
    this.deleteTaskId       = c.querySelector('.js-delete-task-id');
    this.confirmDeleteBtn   = c.querySelector('.js-confirm-delete-btn');
    this.cancelDeleteBtn    = c.querySelector('.js-cancel-delete-btn');
  }

  // ════════════ 事件绑定 ════════════
  _bindEvents() {
    // 添加任务
    if (this.addForm) {
      this.addForm.addEventListener('submit', (e) => this._handleAddTask(e));
    }

    // 任务列表事件委托（toggle / edit / delete / 拖拽）
    if (this.taskList) {
      this.taskList.addEventListener('click', (e) => this._handleTaskListClick(e));

      // ── 拖拽排序事件（绑定在 taskList 容器上）──
      this.taskList.addEventListener('dragstart', (e) => this._handleDragStart(e));
      this.taskList.addEventListener('dragover', (e) => this._handleDragOver(e));
      this.taskList.addEventListener('dragenter', (e) => this._handleDragEnter(e));
      this.taskList.addEventListener('dragleave', (e) => this._handleDragLeave(e));
      this.taskList.addEventListener('drop', (e) => this._handleDrop(e));
      this.taskList.addEventListener('dragend', (e) => this._handleDragEnd(e));
    }

    // 编辑弹窗
    if (this.saveEditBtn) {
      this.saveEditBtn.addEventListener('click', () => this._handleSaveEdit());
    }
    if (this.cancelEditBtn) {
      this.cancelEditBtn.addEventListener('click', () => this._closeEditModal());
    }
    if (this.editModal) {
      this.editModal.addEventListener('click', (e) => {
        if (e.target === this.editModal) this._closeEditModal();
      });
    }

    // 删除弹窗
    if (this.confirmDeleteBtn) {
      this.confirmDeleteBtn.addEventListener('click', () => this._handleConfirmDelete());
    }
    if (this.cancelDeleteBtn) {
      this.cancelDeleteBtn.addEventListener('click', () => this._closeDeleteModal());
    }
    if (this.deleteModal) {
      this.deleteModal.addEventListener('click', (e) => {
        if (e.target === this.deleteModal) this._closeDeleteModal();
      });
    }
  }

  // ════════════ Toast ════════════
  _showToast(icon, msg, duration = 2500) {
    this.cipherToast.style.display = 'block';
    this.cipherIcon.textContent = icon;
    this.cipherMsg.textContent = msg;

    // 重新触发旋转动画
    this.cipherIcon.style.animation = 'none';
    this.cipherIcon.offsetHeight; // reflow
    this.cipherIcon.style.animation = '';

    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      this.cipherToast.style.display = 'none';
    }, duration);
  }

  // ════════════ 统计刷新 ════════════
  async refreshStats() {
    try {
      const res = await fetch('/api/stats' + this.apiParam);
      const stats = await res.json();
      this.statTotal.textContent = stats.total;
      this.statDone.textContent = stats.done;
      this.statPending.textContent = stats.pending;
      this.statHighPri.textContent = stats.high_pri;
      this.progressFill.style.width = stats.pct + '%';
      this.progressText.textContent = Math.round(stats.pct) + '% (' + stats.done + '/' + stats.total + ')';

      // 进度条满状态
      if (stats.pct >= 100 && stats.total > 0) {
        this.progressFill.classList.add('full');
      } else {
        this.progressFill.classList.remove('full');
      }

      // 提示信息
      if (stats.total === 0) {
        this.statsHint.textContent = '';
        this.statsHint.className = 'stats-hint js-stats-hint';
      } else if (stats.pct === 100) {
        this.statsHint.textContent = '🎉 所有密码机已破译！地窖已开启，快逃离庄园吧！';
        this.statsHint.className = 'stats-hint js-stats-hint success';
      } else if (stats.high_pri > 0) {
        this.statsHint.textContent = '⚡ 警告：还有 ' + stats.high_pri + ' 封梦之女巫级紧急信件待处理！';
        this.statsHint.className = 'stats-hint js-stats-hint warning';
      } else if (stats.pending === 0) {
        this.statsHint.textContent = '✓ 所有任务已完成。';
        this.statsHint.className = 'stats-hint js-stats-hint success';
      } else {
        const hunter = HUNTERS[stats.pending % HUNTERS.length];
        this.statsHint.textContent = '👁 ' + hunter + ' 正在庄园中巡逻……尽快完成任务。';
        this.statsHint.className = 'stats-hint js-stats-hint';
      }
    } catch (e) {
      console.error('[' + this.playerName + '] 刷新统计失败:', e);
    }
  }

  // ════════════ 渲染任务行 ════════════
  _renderTaskRow(task) {
    const div = document.createElement('div');
    div.className = 'task-row' + (task.is_completed ? ' completed' : '');
    div.dataset.id = task.id;
    div.draggable = true;
    div.innerHTML = `
      <span class="drag-handle" title="拖拽排序">⋮⋮</span>
      <button class="toggle-btn js-toggle-btn" data-id="${task.id}" title="切换完成状态">
        <span class="toggle-mark">${task.is_completed ? '✓' : '○'}</span>
      </button>
      <span class="task-id">#${task.id}</span>
      <span class="priority-badge priority-${task.priority}">${task.priority_label}</span>
      <span class="task-content">${escapeHtml(task.content)}</span>
      <div class="task-actions">
        <button class="btn-icon edit-btn js-edit-btn" data-id="${task.id}" title="编辑任务">✎</button>
        <button class="btn-icon delete-btn js-delete-btn" data-id="${task.id}" title="删除任务">⛏</button>
      </div>
    `;
    return div;
  }

  // ════════════ 添加任务 ════════════
  async _handleAddTask(e) {
    e.preventDefault();
    const content = this.taskInput.value.trim();
    const priority = parseInt(this.taskPriority.value);

    if (!content) {
      this.addError.textContent = '信件内容不能为空！';
      return;
    }
    this.addError.textContent = '';

    // 防重复提交
    this.addBtn.disabled = true;
    this.addBtn.textContent = '⚙ 归档中……';

    try {
      const res = await fetch('/api/tasks' + this.apiParam, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, priority }),
      });

      if (!res.ok) {
        const data = await res.json();
        this.addError.textContent = data.error || '添加失败';
        return;
      }

      const task = await res.json();

      // 隐藏空状态
      if (this.emptyState) this.emptyState.style.display = 'none';
      this.taskList.style.display = '';

      // 添加行
      const row = this._renderTaskRow(task);
      this.taskList.appendChild(row);

      // 清空输入
      this.taskInput.value = '';
      this.taskInput.focus();

      // Toast
      const sIcon = task.survivor_icon || '';
      this._showToast('⚙', `密码机破译成功！${sIcon} ${task.survivor} 将协助你完成此任务。`);

      await this.refreshStats();
    } catch (err) {
      this.addError.textContent = '网络错误，请重试。';
      console.error('[' + this.playerName + '] 添加失败:', err);
    } finally {
      this.addBtn.disabled = false;
      this.addBtn.textContent = '⚙ 归档信件';
    }
  }

  // ════════════ 任务列表事件委托 ════════════
  async _handleTaskListClick(e) {
    const target = e.target.closest('button');
    if (!target) return;

    const taskId = parseInt(target.dataset.id);
    if (!taskId) return;

    // ── 切换完成状态 ──
    if (target.classList.contains('js-toggle-btn') || target.classList.contains('toggle-btn')) {
      try {
        const res = await fetch(`/api/tasks/${taskId}/toggle` + this.apiParam, { method: 'POST' });
        if (!res.ok) return;
        const task = await res.json();

        const row = this.taskList.querySelector(`.task-row[data-id="${taskId}"]`);
        if (!row) return;

        if (task.is_completed) {
          row.classList.add('completed');
          row.querySelector('.toggle-mark').textContent = '✓';
          const hunter = task.hunter || '监管者';
          const hIcon = task.hunter_icon || '';
          this._showToast('⚙', `密码机破译成功！${hIcon} ${hunter} 暂时没有发现你。`);
        } else {
          row.classList.remove('completed');
          row.querySelector('.toggle-mark').textContent = '○';
          this._showToast('⚙', '密码机已重置，任务恢复为未完成。');
        }
        row.querySelector('.priority-badge').className = 'priority-badge priority-' + task.priority;
        row.querySelector('.priority-badge').textContent = task.priority_label;

        await this.refreshStats();
      } catch (err) {
        console.error('[' + this.playerName + '] 切换失败:', err);
      }
    }

    // ── 编辑 ──
    if (target.classList.contains('js-edit-btn') || target.classList.contains('edit-btn')) {
      this._openEditModal(taskId);
    }

    // ── 删除 ──
    if (target.classList.contains('js-delete-btn') || target.classList.contains('delete-btn')) {
      this._openDeleteModal(taskId);
    }
  }

  // ════════════ 编辑弹窗 ════════════
  _openEditModal(taskId) {
    const row = this.taskList.querySelector(`.task-row[data-id="${taskId}"]`);
    if (!row) return;

    const contentEl = row.querySelector('.task-content');
    const badgeEl = row.querySelector('.priority-badge');

    this.editTaskId.value = taskId;
    this.editContent.value = contentEl.textContent.trim();
    this.editPriority.value = getPriorityFromBadge(badgeEl.className);
    this.editError.textContent = '';
    this.editModal.style.display = 'flex';
    this.editContent.focus();
  }

  _closeEditModal() {
    this.editModal.style.display = 'none';
  }

  async _handleSaveEdit() {
    const taskId = parseInt(this.editTaskId.value);
    const content = this.editContent.value.trim();
    const priority = parseInt(this.editPriority.value);

    if (!content) {
      this.editError.textContent = '内容不能为空！';
      return;
    }

    try {
      const res = await fetch(`/api/tasks/${taskId}` + this.apiParam, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, priority }),
      });

      if (!res.ok) {
        const data = await res.json();
        this.editError.textContent = data.error || '编辑失败';
        return;
      }

      const task = await res.json();
      const row = this.taskList.querySelector(`.task-row[data-id="${taskId}"]`);
      if (row) {
        row.querySelector('.task-content').textContent = task.content;
        row.querySelector('.priority-badge').className = 'priority-badge priority-' + task.priority;
        row.querySelector('.priority-badge').textContent = task.priority_label;
        if (task.is_completed) {
          row.classList.add('completed');
        } else {
          row.classList.remove('completed');
        }
      }

      this._closeEditModal();
      this._showToast('✎', '密文已修改。');
      await this.refreshStats();
    } catch (err) {
      this.editError.textContent = '网络错误，请重试。';
      console.error('[' + this.playerName + '] 编辑失败:', err);
    }
  }

  // ════════════ 删除弹窗 ════════════
  _openDeleteModal(taskId) {
    this.deleteTaskId.value = taskId;
    this.deleteModal.style.display = 'flex';
  }

  _closeDeleteModal() {
    this.deleteModal.style.display = 'none';
  }

  async _handleConfirmDelete() {
    const taskId = parseInt(this.deleteTaskId.value);

    try {
      const res = await fetch(`/api/tasks/${taskId}` + this.apiParam, { method: 'DELETE' });
      if (!res.ok) return;

      const row = this.taskList.querySelector(`.task-row[data-id="${taskId}"]`);
      if (row) {
        row.classList.add('removing');
        row.addEventListener('transitionend', () => row.remove());
        setTimeout(() => { if (row.parentNode) row.remove(); }, 350);
      }

      this._closeDeleteModal();

      // 检查是否清空
      setTimeout(async () => {
        await this.refreshStats();
        const remaining = this.taskList.querySelectorAll('.task-row').length;
        if (remaining === 0 && this.emptyState) {
          this.emptyState.style.display = '';
          this.taskList.style.display = 'none';
        }
      }, 100);

      this._showToast('⛏', '陷阱已拆除，任务已删除。');
    } catch (err) {
      console.error('[' + this.playerName + '] 删除失败:', err);
    }
  }

  // ════════════ 拖拽排序 ════════════

  /**
   * dragstart — 记录被拖拽任务的 ID 和所属面板标识
   */
  _handleDragStart(e) {
    const row = e.target.closest('.task-row');
    if (!row) return;

    // 标记数据：格式 "panelKey:taskId"，用于防止跨面板拖拽
    const dragData = `${this.playerKey}:${row.dataset.id}`;
    e.dataTransfer.setData('text/plain', dragData);
    e.dataTransfer.effectAllowed = 'move';

    // 延迟添加 dragging 样式（避免拖拽截图立即变透明）
    requestAnimationFrame(() => {
      row.classList.add('dragging');
    });

    // 记录拖拽源面板键（存实例属性，用于 dragover 校验）
    this._dragSourceKey = this.playerKey;
  }

  /**
   * dragover — 计算插入位置并允许 drop
   */
  _handleDragOver(e) {
    e.preventDefault(); // 必须 preventDefault 才能 drop

    // 跨面板拖拽拒绝：检查 dataTransfer 中的面板标识
    const dragData = e.dataTransfer.getData('text/plain');
    if (dragData) {
      const [sourceKey] = dragData.split(':');
      if (sourceKey !== this.playerKey) {
        e.dataTransfer.dropEffect = 'none';
        return;
      }
    }
    e.dataTransfer.dropEffect = 'move';

    // 根据鼠标 Y 坐标判定插入位置（中线上方 = before，下方 = after）
    const row = e.target.closest('.task-row');
    if (!row || row.classList.contains('dragging')) return;

    const rect = row.getBoundingClientRect();
    const midY = rect.top + rect.height / 2;

    // 先清除所有 drag-over
    this.taskList.querySelectorAll('.task-row.drag-over').forEach(r => {
      r.classList.remove('drag-over', 'drag-over-top');
    });

    if (e.clientY < midY) {
      row.classList.add('drag-over', 'drag-over-top');
    } else {
      row.classList.add('drag-over');
    }
  }

  /**
   * dragenter — 视觉反馈
   */
  _handleDragEnter(e) {
    e.preventDefault();
    const row = e.target.closest('.task-row');
    if (!row || row.classList.contains('dragging')) return;
  }

  /**
   * dragleave — 清除当前行的悬停样式
   */
  _handleDragLeave(e) {
    const row = e.target.closest('.task-row');
    if (row) {
      // 仅在真正离开该行时清除（防止子元素冒泡）
      if (!row.contains(e.relatedTarget)) {
        row.classList.remove('drag-over', 'drag-over-top');
      }
    }
  }

  /**
   * drop — 执行 DOM 重排 + 数组重排 + 后端持久化
   */
  async _handleDrop(e) {
    e.preventDefault();

    // 清除拖拽视觉
    this.taskList.querySelectorAll('.task-row.drag-over').forEach(r => {
      r.classList.remove('drag-over', 'drag-over-top');
    });

    const dragData = e.dataTransfer.getData('text/plain');
    if (!dragData) return;

    const [sourceKey, taskIdStr] = dragData.split(':');
    if (sourceKey !== this.playerKey) return; // 跨面板拒绝

    const taskId = parseInt(taskIdStr);
    const draggedRow = this.taskList.querySelector(`.task-row[data-id="${taskId}"]`);
    if (!draggedRow) return;

    // 找到 drop 目标行
    const targetRow = e.target.closest('.task-row');
    if (!targetRow || targetRow === draggedRow) return;

    const rect = targetRow.getBoundingClientRect();
    const midY = rect.top + rect.height / 2;

    // 根据鼠标在中线上方还是下方决定插入位置
    if (e.clientY < midY) {
      this.taskList.insertBefore(draggedRow, targetRow);
    } else {
      this.taskList.insertBefore(draggedRow, targetRow.nextSibling);
    }

    // 持久化新顺序 → 后端保存
    await this._saveOrder();
  }

  /**
   * dragend — 清理所有拖拽状态
   */
  _handleDragEnd(e) {
    const row = e.target.closest('.task-row');
    if (row) row.classList.remove('dragging');

    this.taskList.querySelectorAll('.task-row.drag-over').forEach(r => {
      r.classList.remove('drag-over', 'drag-over-top');
    });

    this._dragSourceKey = null;
  }

  /**
   * 收集当前 taskList 中的所有任务 ID，按 DOM 顺序组成数组，
   * 发送 POST /api/tasks/reorder 持久化
   */
  async _saveOrder() {
    const rows = this.taskList.querySelectorAll('.task-row');
    const orderedIds = Array.from(rows).map(r => parseInt(r.dataset.id));

    try {
      await fetch('/api/tasks/reorder' + this.apiParam, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order: orderedIds }),
      });
    } catch (err) {
      console.error('[' + this.playerName + '] 保存排序失败:', err);
    }
  }

  // ════════════ 全局辅助 ════════════
  /** 关闭该面板所有弹窗（供全局 Escape 调用） */
  closeAllModals() {
    this.editModal.style.display = 'none';
    this.deleteModal.style.display = 'none';
  }

  /** 聚焦输入框 */
  focusInput() {
    this.taskInput.focus();
  }
}


// ════════════════ 共享 UI 逻辑（与面板无关） ════════════════

// ── ASCII 艺术折叠 ──
(function initAsciiArt() {
  const el = document.getElementById('asciiArt');
  if (!el) return;
  el.addEventListener('click', () => el.classList.toggle('collapsed'));
  el.classList.add('collapsed'); // 默认折叠
})();

// ── 角色图鉴折叠 ──
(function initGallery() {
  const toggle = document.getElementById('galleryToggle');
  const content = document.getElementById('galleryContent');
  if (!toggle || !content) return;
  toggle.addEventListener('click', () => {
    content.classList.toggle('collapsed');
    toggle.classList.toggle('open');
  });
  content.classList.add('collapsed'); // 默认折叠
})();

// ── 角色立绘弹窗 ──
(function initPortraitModal() {
  const modal = document.getElementById('portraitModal');
  const box = document.getElementById('portraitBox');
  const img = document.getElementById('portraitImg');
  const fallback = document.getElementById('portraitFallback');
  const nameEl = document.getElementById('portraitName');
  const sideEl = document.getElementById('portraitSide');
  const roleEl = document.getElementById('portraitRole');
  const quoteEl = document.getElementById('portraitQuote');
  const pickBtnA = document.getElementById('pickDailyA');
  const pickBtnB = document.getElementById('pickDailyB');
  const closeBtn = document.getElementById('portraitClose');

  function close() { modal.style.display = 'none'; }

  document.querySelectorAll('.character-card').forEach(card => {
    card.addEventListener('click', () => {
      const name = card.dataset.name;
      const icon = card.dataset.icon;
      const role = card.dataset.role;
      const side = card.dataset.side;
      const imgSrc = '/static/' + card.dataset.img;

      fallback.textContent = icon;
      fallback.style.display = 'block';
      img.style.display = 'none';

      const testImg = new Image();
      testImg.onload = () => {
        img.src = imgSrc;
        img.style.display = 'block';
        fallback.style.display = 'none';
      };
      testImg.onerror = () => {
        fallback.style.display = 'block';
        img.style.display = 'none';
      };
      testImg.src = imgSrc;

      nameEl.textContent = name;
      roleEl.textContent = role;
      quoteEl.textContent = '「' + (CHARACTER_QUOTES[name] || '……') + '」';

      box.classList.remove('survivor', 'hunter');
      box.classList.add(side);

      sideEl.textContent = side === 'survivor' ? '🏃 求 生 者' : '👁 监 管 者';

      // 今日角色按钮 — 两个玩家各一个
      [pickBtnA, pickBtnB].forEach(b => {
        b.dataset.name = name;
        b.dataset.side = side;
      });
      pickBtnA.textContent = '🌟 小木木的今日角色';
      pickBtnB.textContent = '🌟 小E的今日角色';
      pickBtnA.style.background = '';
      pickBtnB.style.background = '';

      modal.style.display = 'flex';
    });
  });

  // 选为今日角色按钮
  async function handlePickDaily(btn) {
    const name = btn.dataset.name;
    const side = btn.dataset.side;
    const playerKey = btn.dataset.player;
    if (!name) return;

    try {
      const res = await fetch('/api/daily-character?player=' + playerKey, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, side: side }),
      });
      if (res.ok) {
        btn.textContent = playerKey === 'A' ? '✓ 小木木已就位' : '✓ 小E已就位';
        btn.style.background = 'linear-gradient(135deg, #2ea043, #238636)';
        updateDailyCharacterUI(playerKey, name, side);
      }
    } catch (e) {
      console.error('Failed to set daily character:', e);
    }
  }

  pickBtnA.addEventListener('click', () => handlePickDaily(pickBtnA));
  pickBtnB.addEventListener('click', () => handlePickDaily(pickBtnB));

  closeBtn.addEventListener('click', close);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) close();
  });
})();

// ── 全局键盘快捷键 ──
document.addEventListener('keydown', (e) => {
  // Escape 关闭所有弹窗
  if (e.key === 'Escape') {
    // 关闭面板弹窗
    TaskPanel._instances.forEach(p => p.closeAllModals());
    // 关闭共享角色弹窗
    const portraitModal = document.getElementById('portraitModal');
    if (portraitModal) portraitModal.style.display = 'none';
  }

  // Ctrl+N / Alt+N 聚焦第一个面板
  if ((e.ctrlKey || e.altKey) && e.key === 'n') {
    e.preventDefault();
    if (TaskPanel._instances.length > 0) {
      TaskPanel._instances[0].focusInput();
    }
  }
});


// ════════════════ 共享函数 ════════════════

/** 更新面板的今日角色 UI */
function updateDailyCharacterUI(playerKey, name, side) {
  const section = document.querySelector(`.js-daily-section[data-player="${playerKey}"]`);
  if (!section) return;

  const imgPath = CHARACTER_IMAGES[name] || '';
  const iconEmoji = side === 'survivor'
    ? (SURVIVOR_ICONS[name] || '')
    : (HUNTER_ICONS[name] || '');

  const quote = CHARACTER_QUOTES[name] || '……';
  section.innerHTML = `
    <div class="daily-card daily-active" data-side="${side}">
      <span class="daily-label">📅 今日角色</span>
      <span class="daily-char-icon">
        <img class="daily-char-img" src="/static/${imgPath}" alt="${name}" loading="lazy"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
        <span class="daily-icon-fallback" style="display:none;">${iconEmoji}</span>
      </span>
      <span class="daily-char-name">${name}</span>
      <span class="daily-char-side">${side === 'survivor' ? '🏃 求生者' : '👁 监管者'}</span>
      <span class="daily-char-quote">「${quote}」</span>
    </div>
  `;
}

// ════════════════ 启动 ════════════════

document.addEventListener('DOMContentLoaded', () => {
  // 实例化小木木面板
  const containerA = document.querySelector('.player-panel[data-player="A"]');
  if (containerA) {
    new TaskPanel({
      container: containerA,
      playerKey: 'A',
      playerName: '小木木',
    });
  }

  // 实例化小E面板
  const containerB = document.querySelector('.player-panel[data-player="B"]');
  if (containerB) {
    new TaskPanel({
      container: containerB,
      playerKey: 'B',
      playerName: '小E',
    });
  }

  // 默认聚焦第一个面板
  if (TaskPanel._instances.length > 0) {
    TaskPanel._instances[0].focusInput();
  }
});
