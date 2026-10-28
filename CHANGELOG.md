# 更新日志（Changelog）

> 按文件修改日期整理。当前工作区改动尚未提交 git，统一标记为 **未发布**。
> 详细提交说明见 [git-commit-log-2026-10-29.md](./git-commit-log-2026-10-29.md)。

## 2026-10-29

### 修复：个人主页进入后跳转卡顿（分页组件参数类型错误）
- 根因：8 个视图共 13 处 `<lay-page>` 分页的 `layout` 误用字符串 `"prev, page, next, count"`，
  组件内部要求数组并执行 `reduce()`；分页器实际渲染（数据超过一页）时抛
  `TypeError: x.value.reduce is not a function` → 页面渲染中断 → 跳转时 `out-in` 过渡解构
  null vnode 崩溃 → 地址栏已变但页面空白，需刷新恢复。
- 修复：全部改为数组绑定 `:layout="['prev', 'page', 'next', 'count']"`。
- 涉及文件（9）：
  - `src/views/profile/ProfileView.vue`（登录记录、收藏 2 处）
  - `src/views/profile/UserRelationView.vue`、`src/views/profile/NotificationsView.vue`
  - `src/views/appeal/AppealView.vue`、`src/views/friends/FriendsView.vue`
  - `src/views/news/NewsView.vue`、`src/views/home/HomeView.vue`
  - `src/views/skills/SkillsView.vue`、`src/views/heroes/HeroesView.vue`（3 处）
- 注：上述 UserRelationView / NotificationsView / AppealView / FriendsView 页面本体为
  10-22 ~ 10-23 开发的存量功能，本日仅修复其分页写法；HomeView 同时含 10-28 公告前台展示改动。

### 文档与清理
- 新增 `README.md` 文档导航、本文件 `CHANGELOG.md`、`git-commit-log-2026-10-29.md`（两份提交总结）。
- 清理调试残留 `_dbg_profile.png`（取消 git 暂存并删除）。

## 2026-10-28

### 新增：后台管理模块（看板 / 用户管理 / 内容管理 / 公告管理）
- **看板**：ECharts 全局统计预览（用户、帖子、评论、资源、求番、番剧、身份申请、申诉等概览与趋势/状态分布图）+ 待办事项聚合区。
- **用户管理**：用户列表、启用 / 禁用 / 封禁。
- **内容管理**：博文审核、评论审核；发布人可看到自己发布的内容，状态为「待审核」，通过前不公开。
- **公告管理**：后台发布 / 编辑 / 上下线，前台首页公告栏展示。
- **配套**：`posts` / `replies` 增加审核状态流转；`schema.sql` 新增审核列与 `announcements` 表；新增 layui 主题样式；引入 `echarts`（6.1.0）。
- 涉及文件（13）：
  - 后端：`server/api/admin.py`、`server/api/announcements.py`、`server/api/__init__.py`、
    `server/api/posts.py`、`server/api/replies.py`、`server/sql/schema.sql`
  - 前端：`src/api/index.js`、`src/styles/layui-theme.scss`、`src/views/admin/AdminView.vue`、
    `src/views/content/ContentManageView.vue`、`src/views/content/PostEditorView.vue`、
    `src/views/home/HomeView.vue`（公告栏）
  - 依赖：`package.json`、`package-lock.json`

## 2026-10-23

### 新增：番剧库 / 资源分享 / 身份申请 / 消息通知
- 番剧库与求番（`animes.py`、`anime_requests.py`）、资源分享（`resources.py`）、
  身份申请（`identity.py`）、消息通知（`notifications.py`）、用户资料接口（`users.py`）、
  统一响应工具（`server/utils/response.py`）。
- 前端：路由扩展（`src/router/index.js`）、顶部导航（`src/views/head.vue`）、
  帖子卡片（`src/components/PostCard.vue`）、身份申请页（`src/views/profile/IdentityView.vue`）。

## 2026-10-22

### 新增：认证与个人中心基础功能
- 认证（`server/api/auth.py`、`server/utils/auth.py`、`LoginView.vue`、`RegisterView.vue`）、
  好友（`friends.py`）、申诉（`appeals.py`）、评论树（`src/components/ReplyNode.vue`）、
  帖子详情（`PostDetailView.vue`）、404 / 关于页、全局壳（`App.vue`、`main.js`、`vite.config.js`）。

---

## 约定

- 条目按改动落盘日期归类；单个文件跨日期多次改动时，归入最后一次修改日期并注明。
- 版本号：项目尚未发布正式版本，暂不引入版本号。
