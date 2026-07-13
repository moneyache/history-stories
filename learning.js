/**
 * 上下五千年 - 学习记录模块
 * 
 * 星星规则：
 *   1 个人物 = 1 ⭐
 *   1 个朝代 = 3 ⭐
 *   10 ⭐ = 1 🌙（月亮）
 *   10 🌙 = 1 ☀️（太阳）
 * 
 * 幂等：同一用户 + 同一内容（content_type + content_id）不会重复加星
 */

// ==========================================
// Supabase（复用 auth.js 的配置）
// ==========================================
function getSB() {
  return supabase.createClient(
    'https://sucecjwfpslxnisvyetq.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN1Y2VjandmcHNseG5pc3Z5ZXRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1Mjk2ODcsImV4cCI6MjA5NzEwNTY4N30.sF6wjjDLkzY7kNg_etNhqYjvdtEwdr3TAGkdVnjl3QE'
  );
}

const TABLE_LEARNING = 'hs_learning_records';

// ==========================================
// 星星 → 月亮 → 太阳 换算
// ==========================================
function starsToDisplay(totalStars) {
  const suns = Math.floor(totalStars / 100);      // 100 stars = 1 sun
  const remainder = totalStars % 100;
  const moons = Math.floor(remainder / 10);        // 10 stars = 1 moon
  const stars = remainder % 10;
  return { suns, moons, stars, total: totalStars };
}

function formatStarsDisplay(summary) {
  let s = '';
  if (summary.suns > 0) s += '☀️'.repeat(summary.suns);
  if (summary.moons > 0) s += '🌙'.repeat(summary.moons);
  if (summary.stars > 0) s += '⭐'.repeat(summary.stars);
  if (s === '') s = '—';
  return s;
}

// ==========================================
// 音频：鼓励音效（Web Audio API）
// ==========================================
function playCelebrationSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5 E5 G5 C6
    notes.forEach(function(freq, i) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.25, ctx.currentTime + i * 0.12);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.12 + 0.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime + i * 0.12);
      osc.stop(ctx.currentTime + i * 0.12 + 0.5);
    });
  } catch(e) {
    // 静默失败（某些浏览器限制 AudioContext）
  }
}

// ==========================================
// 星星动画：从屏幕下方飞入并闪烁
// ==========================================
function showStarAnimation(starCount) {
  // 创建固定容器
  var container = document.getElementById('star-anim-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'star-anim-container';
    container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;';
    document.body.appendChild(container);
  }

  // 延迟 0.3s 让用户看到得分
  setTimeout(function() {
    for (var i = 0; i < starCount; i++) {
      (function(idx) {
        setTimeout(function() {
          var star = document.createElement('span');
          star.textContent = '⭐';
          star.style.cssText = [
            'position:fixed',
            'font-size:' + (40 + Math.random() * 30) + 'px',
            'left:' + (15 + Math.random() * 70) + '%',
            'bottom:-60px',
            'pointer-events:none',
            'animation: starFlyUp ' + (0.8 + Math.random() * 0.6) + 's cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards',
            'animation-delay: 0s',
            'z-index:9999'
          ].join(';');
          container.appendChild(star);

          // 自动清理
          setTimeout(function() {
            if (star.parentNode) star.parentNode.removeChild(star);
          }, 1800);
        }, idx * 120);
      })(i);
    }
  }, 300);
}

// 注入星星动画 CSS
(function injectStarCSS() {
  if (document.getElementById('star-anim-style')) return;
  var style = document.createElement('style');
  style.id = 'star-anim-style';
  style.textContent = '@keyframes starFlyUp{0%{bottom:-60px;opacity:0;transform:scale(0.3) rotate(-20deg);}30%{opacity:1;transform:scale(1.3) rotate(10deg);}70%{opacity:1;transform:scale(1) rotate(0deg);}100%{bottom:105%;opacity:0;transform:scale(0.5) rotate(20deg);}}';
  document.head.appendChild(style);
})();

// ==========================================
// 保存学习记录（幂等）
// ==========================================
async function saveLearningRecord(contentType, contentId, contentName, starsEarned) {
  var username = getCookie('hs_user');
  if (!username) {
    console.log('[学习记录] 未登录，跳过保存');
    return { success: false, reason: 'not_logged_in' };
  }

  var sb = getSB();
  var now = new Date().toISOString();

  // 幂等：依赖数据库 UNIQUE(username, content_type, content_id)
  var { data, error } = await sb
    .from(TABLE_LEARNING)
    .insert({
      username: username,
      content_type: contentType,
      content_id: contentId,
      content_name: contentName,
      stars_earned: starsEarned,
      completed_at: now
    })
    .select('id')
    .maybeSingle();

  if (error) {
    if (error.code === '23505') {
      // 唯一约束冲突 → 已经加过星了，静默返回
      console.log('[学习记录] 已存在，跳过: ' + contentType + '/' + contentId);
      return { success: false, reason: 'duplicate' };
    }
    console.error('[学习记录] 保存失败:', error.message);
    return { success: false, reason: 'error', error: error.message };
  }

  console.log('[学习记录] 保存成功: ' + contentType + '/' + contentId + ' +' + starsEarned + '⭐');
  return { success: true, id: data.id };
}

/**
 * 测验完成后调用：保存记录 + 播放音效 + 星星动画
 */
async function onQuizComplete(contentType, contentId, contentName, starsEarned) {
  var result = await saveLearningRecord(contentType, contentId, contentName, starsEarned);
  if (result.success) {
    playCelebrationSound();
    showStarAnimation(starsEarned);
  }
  return result;
}

// ==========================================
// 获取学习记录
// ==========================================
async function getLearningRecords(username) {
  if (!username) return [];
  var sb = getSB();
  var { data, error } = await sb
    .from(TABLE_LEARNING)
    .select('content_type, content_id, content_name, stars_earned, completed_at')
    .eq('username', username)
    .order('completed_at', { ascending: false });

  if (error) {
    console.error('[学习记录] 查询失败:', error.message);
    return [];
  }
  return data || [];
}

/**
 * 获取用户的星星汇总
 */
async function getStarSummary(username) {
  var records = await getLearningRecords(username);
  var total = 0;
  records.forEach(function(r) { total += r.stars_earned; });
  return starsToDisplay(total);
}

/**
 * 获取已学内容的集合 { "dynasty/han": true, "figure/zhugeliang": true }
 */
async function getLearnedSet(username) {
  var records = await getLearningRecords(username);
  var set = {};
  records.forEach(function(r) {
    set[r.content_type + '/' + r.content_id] = true;
  });
  return set;
}

// ==========================================
// 学习记录页面渲染
// ==========================================
async function renderLearningPage() {
  var username = getCookie('hs_user');
  var mainEl = document.getElementById('learning-main');
  if (!mainEl) return;

  if (!username) {
    mainEl.innerHTML = '<div class="lr-empty">请先<a href="login.html">登录</a>查看学习记录</div>';
    return;
  }

  // 显示加载中
  mainEl.innerHTML = '<div class="lr-loading">加载中...</div>';

  try {
    var [records, summary] = await Promise.all([
      getLearningRecords(username),
      getStarSummary(username)
    ]);

    var display = formatStarsDisplay(summary);
    var learnedSet = {};
    records.forEach(function(r) { learnedSet[r.content_type + '/' + r.content_id] = true; });

    // ===== 顶部：星星汇总 =====
    var topHTML = '<div class="lr-header">' +
      '<h1 class="lr-title">📚 ' + escapeHtml(username) + ' 的学习记录</h1>' +
      '<div class="lr-stars-box">' +
        '<div class="lr-stars-display">' + display + '</div>' +
        '<div class="lr-stars-count">共 ' + summary.total + ' 颗星星</div>' +
        '<div class="lr-stars-legend">⭐×10 = 🌙 &nbsp;|&nbsp; 🌙×10 = ☀️</div>' +
      '</div>';

    // 换算明细
    if (summary.suns > 0 || summary.moons > 0) {
      var parts = [];
      if (summary.suns > 0) parts.push(summary.suns + ' ☀️');
      if (summary.moons > 0) parts.push(summary.moons + ' 🌙');
      if (summary.stars > 0) parts.push(summary.stars + ' ⭐');
      topHTML += '<div class="lr-breakdown">' + parts.join(' &nbsp;+&nbsp; ') + ' = ' + summary.total + ' ⭐</div>';
    }
    topHTML += '</div>';

    // ===== 已学内容 =====
    topHTML += '<div class="lr-section"><h2 class="lr-sec-title">✅ 已完成</h2>';

    if (records.length === 0) {
      topHTML += '<div class="lr-empty">还没有完成任何学习，去<a href="dynasties.html">朝代总览</a>开始吧！</div>';
    } else {
      // 按 content_type 分组
      var dynastyRecs = records.filter(function(r) { return r.content_type === 'dynasty'; });
      var figureRecs = records.filter(function(r) { return r.content_type === 'figure'; });

      if (dynastyRecs.length > 0) {
        topHTML += '<h3 class="lr-sub">🏯 朝代（每题3⭐）</h3><div class="lr-grid">';
        dynastyRecs.forEach(function(r) {
          topHTML += '<div class="lr-card done">' +
            '<span class="lr-icon">🏯</span>' +
            '<span class="lr-name">' + escapeHtml(r.content_name) + '</span>' +
            '<span class="lr-stars">' + '⭐'.repeat(r.stars_earned) + '</span>' +
            '<span class="lr-date">' + formatDate(r.completed_at) + '</span>' +
            '</div>';
        });
        topHTML += '</div>';
      }

      if (figureRecs.length > 0) {
        topHTML += '<h3 class="lr-sub">🧑 人物（每题1⭐）</h3><div class="lr-grid">';
        figureRecs.forEach(function(r) {
          topHTML += '<div class="lr-card done">' +
            '<span class="lr-icon">🧑</span>' +
            '<span class="lr-name">' + escapeHtml(r.content_name) + '</span>' +
            '<span class="lr-stars">' + '⭐'.repeat(r.stars_earned) + '</span>' +
            '<span class="lr-date">' + formatDate(r.completed_at) + '</span>' +
            '</div>';
        });
        topHTML += '</div>';
      }
    }
    topHTML += '</div>';

    // ===== 未学内容 =====
    topHTML += '<div class="lr-section"><h2 class="lr-sec-title">📖 待学习</h2><div class="lr-grid">';

    // 从全局数据取（页面注入）
    var allDynasties = window.__ALL_DYNASTIES__ || [];
    var allFigures = window.__ALL_FIGURES__ || [];

    var unlearnedCount = 0;

    // 朝代
    allDynasties.forEach(function(d) {
      if (!learnedSet['dynasty/' + d.id]) {
        unlearnedCount++;
        topHTML += '<a class="lr-card todo" href="' + d.id + '.html">' +
          '<span class="lr-icon">' + (d.emoji || '🏯') + '</span>' +
          '<span class="lr-name">' + escapeHtml(d.name) + '</span>' +
          '<span class="lr-go">去学习 →</span>' +
          '</a>';
      }
    });

    // 人物
    allFigures.forEach(function(f) {
      if (!learnedSet['figure/' + f.id]) {
        unlearnedCount++;
        topHTML += '<a class="lr-card todo" href="' + f.file + '">' +
          '<span class="lr-icon">' + (f.emoji || '🧑') + '</span>' +
          '<span class="lr-name">' + escapeHtml(f.name) + '</span>' +
          '<span class="lr-go">去学习 →</span>' +
          '</a>';
      }
    });

    if (unlearnedCount === 0) {
      topHTML += '<div class="lr-complete">🎉 全部学完！你太棒了！</div>';
    }

    topHTML += '</div></div>';

    mainEl.innerHTML = topHTML;

  } catch(e) {
    mainEl.innerHTML = '<div class="lr-error">加载失败：' + escapeHtml(e.message) + '</div>';
    console.error('[学习记录] 渲染失败:', e);
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  var d = new Date(isoStr);
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var day = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

function escapeHtml(str) {
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ==========================================
// 自动初始化
// ==========================================
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    if (window.__PAGE_TYPE__ === 'learning') renderLearningPage();
  });
} else {
  if (window.__PAGE_TYPE__ === 'learning') renderLearningPage();
}
