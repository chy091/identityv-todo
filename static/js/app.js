/**
 * 第五人格主题 Todo App — 前端交互
 * 欧利蒂斯庄园 - 求生任务手册
 */

// ════════════════ DOM 引用 ════════════════
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const addForm = $('#addTaskForm');
const taskContent = $('#taskContent');
const taskPriority = $('#taskPriority');
const addError = $('#addError');
const addBtn = $('#addBtn');
const cipherToast = $('#cipherToast');
const cipherMsg = $('#cipherMsg');
const taskList = $('#taskList');
const emptyState = $('#emptyState');

const editModal = $('#editModal');
const editTaskId = $('#editTaskId');
const editContent = $('#editContent');
const editPriority = $('#editPriority');
const editError = $('#editError');

const deleteModal = $('#deleteModal');
const deleteTaskId = $('#deleteTaskId');

// Stats
const statTotal = $('#statTotal');
const statDone = $('#statDone');
const statPending = $('#statPending');
const statHighPri = $('#statHighPri');
const progressFill = $('#progressFill');
const progressText = $('#progressText');
const statsHint = $('#statsHint');
const quoteBox = $('#quoteBox');

// ════════════════ 工具函数 ════════════════

function priorityLabel(p) {
  const labels = { 1: '✦ 求生者级', 2: '✦✦ 监管者级', 3: '✦✦✦ 梦之女巫级' };
  return labels[p] || labels[1];
}

function showToast(icon, msg, duration = 2500) {
  cipherToast.style.display = 'block';
  cipherToast.querySelector('.cipher-icon').textContent = icon;
  cipherMsg.textContent = msg;
  // 重新触发动画
  const iconEl = cipherToast.querySelector('.cipher-icon');
  iconEl.style.animation = 'none';
  iconEl.offsetHeight; // reflow
  iconEl.style.animation = '';
  setTimeout(() => { cipherToast.style.display = 'none'; }, duration);
}

// ════════════════ 统计刷新 ════════════════

async function refreshStats() {
  try {
    const res = await fetch('/api/stats');
    const stats = await res.json();
    statTotal.textContent = stats.total;
    statDone.textContent = stats.done;
    statPending.textContent = stats.pending;
    statHighPri.textContent = stats.high_pri;
    progressFill.style.width = stats.pct + '%';
    progressText.textContent = Math.round(stats.pct) + '% (' + stats.done + '/' + stats.total + ')';
    quoteBox.innerHTML = '「' + stats.quote + '」';

    // 进度条动画类
    if (stats.pct >= 100 && stats.total > 0) {
      progressFill.classList.add('full');
    } else {
      progressFill.classList.remove('full');
    }

    // 提示信息
    if (stats.total === 0) {
      statsHint.textContent = '';
      statsHint.className = 'stats-hint';
    } else if (stats.pct === 100) {
      statsHint.textContent = '🎉 所有密码机已破译！地窖已开启，快逃离庄园吧！';
      statsHint.className = 'stats-hint success';
    } else if (stats.high_pri > 0) {
      statsHint.textContent = '⚡ 警告：还有 ' + stats.high_pri + ' 封梦之女巫级紧急信件待处理！';
      statsHint.className = 'stats-hint warning';
    } else if (stats.pending === 0) {
      statsHint.textContent = '✓ 所有任务已完成。';
      statsHint.className = 'stats-hint success';
    } else {
      const hunter = HUNTERS[stats.pending % HUNTERS.length];
      statsHint.textContent = '👁 ' + hunter + ' 正在庄园中巡逻……尽快完成任务。';
      statsHint.className = 'stats-hint';
    }
  } catch (e) {
    console.error('刷新统计失败:', e);
  }
}

// ════════════════ 渲染任务行 ════════════════

function renderTaskRow(task) {
  const div = document.createElement('div');
  div.className = 'task-row' + (task.is_completed ? ' completed' : '');
  div.dataset.id = task.id;
  div.id = 'taskRow' + task.id;
  div.innerHTML = `
    <button class="toggle-btn" data-id="${task.id}" title="切换完成状态">
      <span class="toggle-mark">${task.is_completed ? '✓' : '○'}</span>
    </button>
    <span class="task-id">#${task.id}</span>
    <span class="priority-badge priority-${task.priority}">${task.priority_label}</span>
    <span class="task-content">${escapeHtml(task.content)}</span>
    <div class="task-actions">
      <button class="btn-icon edit-btn" data-id="${task.id}" title="编辑任务">✎</button>
      <button class="btn-icon delete-btn" data-id="${task.id}" title="删除任务">⛏</button>
    </div>
  `;
  return div;
}

function escapeHtml(str) {
  const el = document.createElement('span');
  el.textContent = str;
  return el.innerHTML;
}

// ════════════════ 添加任务 ════════════════

addForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const content = taskContent.value.trim();
  const priority = parseInt(taskPriority.value);

  if (!content) {
    addError.textContent = '信件内容不能为空！';
    return;
  }
  addError.textContent = '';

  // 禁用按钮防重复提交
  addBtn.disabled = true;
  addBtn.textContent = '⚙ 归档中……';

  try {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, priority }),
    });

    if (!res.ok) {
      const data = await res.json();
      addError.textContent = data.error || '添加失败';
      return;
    }

    const task = await res.json();

    // 隐藏空状态
    if (emptyState) emptyState.style.display = 'none';
    taskList.style.display = '';

    // 添加行到列表
    const row = renderTaskRow(task);
    taskList.appendChild(row);

    // 清空输入
    taskContent.value = '';
    taskContent.focus();

    // 显示动画
    const sIcon = task.survivor_icon || '';
    showToast('⚙', `密码机破译成功！${sIcon} ${task.survivor} 将协助你完成此任务。`);

    // 刷新统计
    await refreshStats();
  } catch (err) {
    addError.textContent = '网络错误，请重试。';
    console.error(err);
  } finally {
    addBtn.disabled = false;
    addBtn.textContent = '⚙ 归档信件';
  }
});

// ════════════════ 任务列表事件委托 ════════════════

taskList.addEventListener('click', async (e) => {
  const target = e.target.closest('button');
  if (!target) return;

  const taskId = parseInt(target.dataset.id);
  if (!taskId) return;

  // ── 切换完成状态 ──
  if (target.classList.contains('toggle-btn')) {
    try {
      const res = await fetch(`/api/tasks/${taskId}/toggle`, { method: 'POST' });
      if (!res.ok) return;
      const task = await res.json();

      const row = document.getElementById('taskRow' + taskId);
      if (!row) return;

      if (task.is_completed) {
        row.classList.add('completed');
        row.querySelector('.toggle-mark').textContent = '✓';
        const hunter = task.hunter || '监管者';
        const hIcon = task.hunter_icon || '';
        showToast('⚙', `密码机破译成功！${hIcon} ${hunter} 暂时没有发现你。`);
      } else {
        row.classList.remove('completed');
        row.querySelector('.toggle-mark').textContent = '○';
        showToast('⚙', '密码机已重置，任务恢复为未完成。');
      }
      row.querySelector('.priority-badge').className = 'priority-badge priority-' + task.priority;
      row.querySelector('.priority-badge').textContent = task.priority_label;

      await refreshStats();
    } catch (err) {
      console.error('切换失败:', err);
    }
  }

  // ── 编辑任务 ──
  if (target.classList.contains('edit-btn')) {
    openEditModal(taskId);
  }

  // ── 删除任务 ──
  if (target.classList.contains('delete-btn')) {
    openDeleteModal(taskId);
  }
});

// ════════════════ 编辑弹窗 ════════════════

function openEditModal(taskId) {
  const row = document.getElementById('taskRow' + taskId);
  if (!row) return;

  const contentEl = row.querySelector('.task-content');
  const badgeEl = row.querySelector('.priority-badge');

  editTaskId.value = taskId;
  editContent.value = contentEl.textContent.trim();
  editPriority.value = getPriorityFromBadge(badgeEl.className);
  editError.textContent = '';
  editModal.style.display = 'flex';
  editContent.focus();
}

function getPriorityFromBadge(className) {
  if (className.includes('priority-1')) return '1';
  if (className.includes('priority-2')) return '2';
  if (className.includes('priority-3')) return '3';
  return '2';
}

$('#saveEditBtn').addEventListener('click', async () => {
  const taskId = parseInt(editTaskId.value);
  const content = editContent.value.trim();
  const priority = parseInt(editPriority.value);

  if (!content) {
    editError.textContent = '内容不能为空！';
    return;
  }

  try {
    const res = await fetch(`/api/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, priority }),
    });

    if (!res.ok) {
      const data = await res.json();
      editError.textContent = data.error || '编辑失败';
      return;
    }

    const task = await res.json();
    const row = document.getElementById('taskRow' + taskId);
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

    editModal.style.display = 'none';
    showToast('✎', '密文已修改。');
    await refreshStats();
  } catch (err) {
    editError.textContent = '网络错误，请重试。';
    console.error(err);
  }
});

$('#cancelEditBtn').addEventListener('click', () => {
  editModal.style.display = 'none';
});

// 点击遮罩关闭
editModal.addEventListener('click', (e) => {
  if (e.target === editModal) editModal.style.display = 'none';
});

// ════════════════ 删除弹窗 ════════════════

function openDeleteModal(taskId) {
  deleteTaskId.value = taskId;
  deleteModal.style.display = 'flex';
}

$('#confirmDeleteBtn').addEventListener('click', async () => {
  const taskId = parseInt(deleteTaskId.value);

  try {
    const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
    if (!res.ok) return;

    const row = document.getElementById('taskRow' + taskId);
    if (row) {
      row.classList.add('removing');
      row.addEventListener('transitionend', () => row.remove());
      // fallback: 如果 transitionend 不触发，300ms 后强制移除
      setTimeout(() => { if (row.parentNode) row.remove(); }, 350);
    }

    deleteModal.style.display = 'none';

    // 检查是否清空
    setTimeout(async () => {
      await refreshStats();
      const remaining = taskList.querySelectorAll('.task-row').length;
      if (remaining === 0 && emptyState) {
        emptyState.style.display = '';
        taskList.style.display = 'none';
      }
    }, 100);

    showToast('⛏', '陷阱已拆除，任务已删除。');
  } catch (err) {
    console.error('删除失败:', err);
  }
});

$('#cancelDeleteBtn').addEventListener('click', () => {
  deleteModal.style.display = 'none';
});

deleteModal.addEventListener('click', (e) => {
  if (e.target === deleteModal) deleteModal.style.display = 'none';
});

// ════════════════ 键盘快捷键 ════════════════

document.addEventListener('keydown', (e) => {
  // Escape 关闭弹窗
  if (e.key === 'Escape') {
    editModal.style.display = 'none';
    deleteModal.style.display = 'none';
    portraitModal.style.display = 'none';
  }

  // Ctrl+N / Alt+N 聚焦输入框
  if ((e.ctrlKey || e.altKey) && e.key === 'n') {
    e.preventDefault();
    taskContent.focus();
  }
});

// ════════════════ ASCII 艺术折叠 ════════════════

const asciiArt = $('#asciiArt');
if (asciiArt) {
  asciiArt.addEventListener('click', () => {
    asciiArt.classList.toggle('collapsed');
  });
  // 默认折叠
  asciiArt.classList.add('collapsed');
}

// ════════════════ 角色图鉴折叠 ════════════════

const galleryToggle = $('#galleryToggle');
const galleryContent = $('#galleryContent');
if (galleryToggle && galleryContent) {
  galleryToggle.addEventListener('click', () => {
    galleryContent.classList.toggle('collapsed');
    galleryToggle.classList.toggle('open');
  });
  // 默认折叠
  galleryContent.classList.add('collapsed');
}

// ════════════════ 角色立绘弹窗 ════════════════

const portraitModal = $('#portraitModal');
const portraitBox = $('#portraitBox');
const portraitIcon = $('#portraitIcon');
const portraitName = $('#portraitName');
const portraitSide = $('#portraitSide');
const portraitRole = $('#portraitRole');

// 绑定角色卡片点击
document.querySelectorAll('.character-card').forEach((card) => {
  card.addEventListener('click', () => {
    const name = card.dataset.name;
    const icon = card.dataset.icon;
    const role = card.dataset.role;
    const side = card.dataset.side;
    const imgSrc = '/static/' + card.dataset.img;

    // 尝试加载图片
    const img = $('#portraitImg');
    const fallback = $('#portraitFallback');
    fallback.textContent = icon;
    fallback.style.display = 'block';
    img.style.display = 'none';

    // 检测图片是否存在
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

    portraitName.textContent = name;
    portraitRole.textContent = role;

    // 阵营样式
    portraitBox.classList.remove('survivor', 'hunter');
    portraitBox.classList.add(side);

    if (side === 'survivor') {
      portraitSide.textContent = '🏃 求 生 者';
    } else {
      portraitSide.textContent = '👁 监 管 者';
    }

    portraitModal.style.display = 'flex';
  });
});

function closePortrait() {
  portraitModal.style.display = 'none';
}

$('#portraitClose').addEventListener('click', closePortrait);
portraitModal.addEventListener('click', (e) => {
  if (e.target === portraitModal) closePortrait();
});

// ════════════════ 初始化 ════════════════

document.addEventListener('DOMContentLoaded', async () => {
  // 初始提示信息
  await refreshStats();

  // 聚焦输入框
  taskContent.focus();
});
