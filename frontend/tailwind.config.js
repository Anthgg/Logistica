/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['SF Mono', 'Cascadia Code', 'Consolas', 'monospace'],
      },
      colors: {
        bg:       '#F5F7F8',
        surface:  '#FFFFFF',
        raised:   '#FAFBFC',
        subtle:   '#F0F4F7',

        primary:  {
          DEFAULT: '#234A68',
          mid:     '#2D5F85',
          sec:     '#50738D',
          light:   '#E8F0F6',
          xlight:  '#F2F6F9',
        },

        orange:   {
          DEFAULT: '#C96A2B',
          light:   '#F5E6D8',
          xlight:  '#FBF3EC',
        },

        emerald:  {
          DEFAULT: '#28866B',
          light:   '#D6EEE8',
          xlight:  '#EDF8F5',
        },

        amber:    {
          DEFAULT: '#B7791F',
          light:   '#FDEECE',
          xlight:  '#FFFBF0',
        },

        danger:   {
          DEFAULT: '#C44E52',
          light:   '#FAE0E1',
          xlight:  '#FFF5F5',
        },

        neutral:  {
          DEFAULT: '#50728A',
          light:   '#E5EBF0',
        },

        ink:      '#152235',
        muted:    '#64748B',
        faint:    '#94A3B8',
        border:   '#DDE4E8',
        'border-strong': '#C8D4DC',
        'border-subtle': '#EEF2F5',
      },
      borderRadius: {
        xs: '4px',
        sm: '6px',
        md: '10px',
        lg: '14px',
        xl: '18px',
      },
      boxShadow: {
        xs:   '0 1px 2px rgba(21,34,53,0.04)',
        sm:   '0 1px 4px rgba(21,34,53,0.06), 0 1px 2px rgba(21,34,53,0.04)',
        md:   '0 4px 12px rgba(21,34,53,0.08), 0 1px 4px rgba(21,34,53,0.04)',
        lg:   '0 8px 24px rgba(21,34,53,0.10), 0 2px 6px rgba(21,34,53,0.05)',
        dock: '0 -2px 16px rgba(21,34,53,0.14), 0 4px 20px rgba(21,34,53,0.12)',
      },
      fontSize: {
        '2xs': ['10px', { lineHeight: '1.3' }],
        xs:    ['11px', { lineHeight: '1.35' }],
        sm:    ['12px', { lineHeight: '1.4'  }],
        base:  ['13px', { lineHeight: '1.4'  }],
        md:    ['14px', { lineHeight: '1.35' }],
        lg:    ['16px', { lineHeight: '1.3'  }],
        xl:    ['18px', { lineHeight: '1.25' }],
        '2xl': ['22px', { lineHeight: '1.2'  }],
        '3xl': ['26px', { lineHeight: '1.15' }],
      },
      height: {
        topbar: '64px',
        dock:   '58px',
      },
      spacing: {
        px:   '28px',
        dock: '80px',
      },
      transitionTimingFunction: {
        bounce: 'cubic-bezier(0.34, 1.4, 0.64, 1)',
        smooth: 'cubic-bezier(0.25, 0.8, 0.25, 1)',
      },
    },
  },
  plugins: [],
}
