import { defineConfig } from 'vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

export default defineConfig({
  base: '/hermes-notes/',
  title: 'Hermes Notes',
  description: '个人学习笔记 · 由 Hermes Agent 驱动',
  lang: 'zh-CN',
  cleanUrls: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['style', {}, `
      /* 笔记列表表格 — 最后一列(日期)增加最小宽度 */
      .vp-doc table td:nth-child(4),
      .vp-doc table th:nth-child(4) {
        white-space: nowrap;
        min-width: 110px;
      }
    `],
  ],

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '标签', link: '/tags/' },
    ],

    sidebar,

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索笔记' },
          modal: { noResultsText: '没有找到相关笔记' }
        }
      }
    },

    outline: { level: [2, 3], label: '目录' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    lastUpdated: { text: '最后更新' },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/nousresearch/hermes-agent' }
    ],

    footer: {
      message: '由 Hermes Agent 自动生成',
      copyright: '© 2026 Hermes Notes'
    }
  },
})
