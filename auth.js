/**
 * 上下五千年 - 用户认证模块
 * 
 * 密码安全策略：
 *   salt = 用户创建日期的日期部分（YYYY-MM-DD）
 *   password_hash = MD5(密码 + "_" + salt)
 *   cookie token = MD5(用户名 + password_hash + 固定密钥)
 */

// ==========================================
// Supabase 配置
// ==========================================
const SUPABASE_URL = 'https://sucecjwfpslxnisvyetq.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN1Y2VjandmcHNseG5pc3Z5ZXRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1Mjk2ODcsImV4cCI6MjA5NzEwNTY4N30.sF6wjjDLkzY7kNg_etNhqYjvdtEwdr3TAGkdVnjl3QE';
const TABLE_USERS = 'hs_users';
const COOKIE_SECRET = 'hss3cr3t-k1dsh1st0ry-2026';

// ==========================================
// Cookie 工具
// ==========================================
function setCookie(name, value, days) {
  const d = new Date();
  d.setTime(d.getTime() + (days * 86400000));
  document.cookie = name + '=' + encodeURIComponent(value) + ';path=/;expires=' + d.toUTCString() + ';SameSite=Lax';
}
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}
function deleteCookie(name) {
  document.cookie = name + '=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT;SameSite=Lax';
}

// ==========================================
// MD5（使用 crypto-js）
// ==========================================
function md5(str) {
  return CryptoJS.MD5(str).toString();
}

/**
 * 计算密码哈希：MD5(密码 + "_" + 日期盐)
 */
function hashPassword(password, dateSalt) {
  return md5(password + '_' + dateSalt);
}

/**
 * 从 created_at 提取日期部分作为 salt
 */
function extractDateSalt(createdAt) {
  // created_at 可能是 ISO 8601 格式: "2026-07-13T12:00:00+08:00"
  return createdAt ? createdAt.substring(0, 10) : '';
}

/**
 * 计算 cookie token：MD5(用户名 + password_hash + 固定密钥)
 */
function computeToken(username, passwordHash) {
  return md5(username + '_' + passwordHash + '_' + COOKIE_SECRET);
}

// ==========================================
// Supabase 客户端
// ==========================================
let _sbClient = null;
function getSupabase() {
  if (!_sbClient) {
    _sbClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return _sbClient;
}

// ==========================================
// 注册
// ==========================================
async function registerUser(username, password) {
  if (!username || !password) {
    return { success: false, error: '用户名和密码不能为空' };
  }
  if (username.length < 2 || username.length > 30) {
    return { success: false, error: '用户名长度 2-30 个字符' };
  }
  if (password.length < 4) {
    return { success: false, error: '密码至少 4 个字符' };
  }

  const sb = getSupabase();

  // 1. 先检查用户名是否已被注册
  const { data: existing } = await sb
    .from(TABLE_USERS)
    .select('id')
    .eq('username', username)
    .maybeSingle();

  if (existing) {
    return { success: false, error: '用户名已被注册' };
  }

  // 2. 生成日期盐
  const now = new Date();
  const dateSalt = now.toISOString().substring(0, 10); // YYYY-MM-DD
  const passwordHash = hashPassword(password, dateSalt);

  // 3. 插入用户记录
  const createdAt = dateSalt + 'T' +
    String(now.getHours()).padStart(2, '0') + ':' +
    String(now.getMinutes()).padStart(2, '0') + ':' +
    String(now.getSeconds()).padStart(2, '0') + '+08:00';

  const { data, error } = await sb
    .from(TABLE_USERS)
    .insert([{
      username: username,
      password_hash: passwordHash,
      created_at: createdAt
    }])
    .select('created_at')
    .single();

  if (error) {
    if (error.code === '23505') {
      return { success: false, error: '用户名已被注册' };
    }
    return { success: false, error: '注册失败，请稍后重试' };
  }

  // 4. 设置登录态
  setLoginCookie(username, passwordHash);
  return { success: true };
}

// ==========================================
// 登录
// ==========================================
async function loginUser(username, password) {
  if (!username || !password) {
    return { success: false, error: '请输入用户名和密码' };
  }

  const sb = getSupabase();

  // 1. 查询用户
  const { data: user, error } = await sb
    .from(TABLE_USERS)
    .select('password_hash, created_at')
    .eq('username', username)
    .maybeSingle();

  if (error || !user) {
    return { success: false, error: '用户名或密码错误' };
  }

  // 2. 提取日期盐并计算哈希
  const dateSalt = extractDateSalt(user.created_at);
  const inputHash = hashPassword(password, dateSalt);

  // 3. 比对
  if (inputHash !== user.password_hash) {
    return { success: false, error: '用户名或密码错误' };
  }

  // 4. 设置登录态
  setLoginCookie(username, user.password_hash);
  return { success: true };
}

// ==========================================
// Cookie 登录态管理
// ==========================================
function setLoginCookie(username, passwordHash) {
  const token = computeToken(username, passwordHash);
  setCookie('hs_user', username, 30);
  setCookie('hs_token', token, 30);
}

function clearLoginCookie() {
  deleteCookie('hs_user');
  deleteCookie('hs_token');
}

/**
 * 验证当前 cookie 登录态是否有效
 * 返回 { loggedIn: bool, username: string|null }
 */
async function checkLoginStatus() {
  const username = getCookie('hs_user');
  const token = getCookie('hs_token');

  if (!username || !token) {
    return { loggedIn: false, username: null };
  }

  const sb = getSupabase();

  // 查询用户，验证 token
  const { data: user, error } = await sb
    .from(TABLE_USERS)
    .select('password_hash')
    .eq('username', username)
    .maybeSingle();

  if (error || !user) {
    clearLoginCookie();
    return { loggedIn: false, username: null };
  }

  const expectedToken = computeToken(username, user.password_hash);
  if (token !== expectedToken) {
    clearLoginCookie();
    return { loggedIn: false, username: null };
  }

  return { loggedIn: true, username: username };
}

/**
 * 登出
 */
function logoutUser() {
  clearLoginCookie();
  window.location.reload();
}

// ==========================================
// UI 更新：在页面加载后更新认证状态显示
// ==========================================
async function initAuthUI() {
  const status = await checkLoginStatus();

  // 查找所有 auth-status 容器并更新
  const containers = document.querySelectorAll('.auth-status');
  containers.forEach(el => {
    if (status.loggedIn) {
      el.innerHTML = '<span class="auth-user">' + escapeHtml(status.username) + '</span>' +
        '<a href="javascript:void(0)" onclick="logoutUser()" class="auth-logout">退出</a>';
    } else {
      el.innerHTML = '<a href="login.html" class="auth-login">登录</a>' +
        '<a href="register.html" class="auth-register">注册</a>';
    }
    el.classList.add('auth-loaded');
  });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// 页面加载后自动初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAuthUI);
} else {
  initAuthUI();
}
