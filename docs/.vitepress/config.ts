import { defineConfig } from 'vitepress'
import sidebar from './sidebar.json' with { type: 'json' }

export default defineConfig({
  title: 'Hermes Notes',
  description: '个人学习笔记 · 由 Hermes Agent 驱动',
  lang: 'zh-CN',
  cleanUrls: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
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
