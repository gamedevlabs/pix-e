// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default withNuxt(
  // Your custom configs here
  skipFormatting,
  {
    rules: {
      'vue/html-self-closing': [
        'error',
        {
          html: {
            void: 'always',
            normal: 'always',
            component: 'always',
          },
          svg: 'always',
          math: 'always',
        },
      ],
    },
  },
)
