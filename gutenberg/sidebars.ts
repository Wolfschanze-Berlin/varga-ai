import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // Main documentation sidebar
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Project Overview',
      collapsible: true,
      collapsed: false,
      items: [
        'project/index',
        'project/brief',
        {
          type: 'category',
          label: 'Architecture',
          items: [
            'project/architecture/index',
          ],
        },
        {
          type: 'category',
          label: 'Agent Catalog',
          items: [
            'project/agents/index',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Development',
      collapsible: true,
      collapsed: false,
      items: [
        'development/claude-guidelines',
        'development/tools-overview',
        'development/implementation-status',
        'development/deployment-guide',
      ],
    },
    {
      type: 'category',
      label: 'Architecture',
      collapsible: true,
      collapsed: false,
      items: [
        'architecture/overview',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      collapsible: true,
      collapsed: false,
      items: [
        'api/overview',
      ],
    },
    {
      type: 'category',
      label: 'User Guides',
      collapsible: true,
      collapsed: false,
      items: [
        'guides/getting-started',
      ],
    },
    {
      type: 'category',
      label: 'Agents',
      collapsible: true,
      collapsed: false,
      items: [
        'agents/index',
        {
          type: 'category',
          label: 'Language Teacher',
          items: [
            'agents/language-teacher/index',
          ],
        },
        {
          type: 'category',
          label: 'Image Generator',
          items: [
            'agents/image-generator/index',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Telegram Bots',
      collapsible: true,
      collapsed: false,
      items: [
        'telegram-bots/index',
        {
          type: 'category',
          label: 'Language Teacher Bot',
          items: [
            'telegram-bots/language-teacher/overview',
            'telegram-bots/language-teacher/setup',
            'telegram-bots/language-teacher/user-guide',
          ],
        },
        {
          type: 'category',
          label: 'Smart Assistant Bot',
          items: [
            'telegram-bots/smart-assistant/overview',
            'telegram-bots/smart-assistant/setup',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Tutorials',
      collapsible: true,
      collapsed: true,
      items: [
        'tutorial-basics/create-a-document',
        'tutorial-basics/create-a-page',
        'tutorial-basics/create-a-blog-post',
        'tutorial-basics/markdown-features',
        'tutorial-basics/deploy-your-site',
        'tutorial-basics/congratulations',
      ],
    },
    {
      type: 'category',
      label: 'Advanced Topics',
      collapsible: true,
      collapsed: true,
      items: [
        'tutorial-extras/manage-docs-versions',
        'tutorial-extras/translate-your-site',
      ],
    },
  ],
};

export default sidebars;
