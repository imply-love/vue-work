# yunmo

番剧同好会 —— 追番、安利、找同好（Vue 3 + Flask + MySQL）。前端 Vite（开发端口 3000），后端 Flask（端口 5000），数据库 MySQL `yunmo` 库。

## 📄 文档导航

| 文档 | 说明 |
|---|---|
| [更新日志](./CHANGELOG.md) | 按修改日期整理的项目改动记录 |
| [Git 提交总结（2026-10-29）](./git-commit-log-2026-10-29.md) | 后台管理功能与分页 bug 修复的提交说明 |
| [数据库结构](./server/sql/schema.sql) | 建表 SQL 与增量迁移（文件顶部含新环境手动执行的 ALTER/CREATE 注释） |

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```
