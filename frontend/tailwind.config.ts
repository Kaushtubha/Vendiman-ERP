/** @type {import('tailwindcss').Config} */
// =============================================================================
// tailwind.config.ts — Design System Foundation
// =============================================================================
//
// DESIGN SYSTEM DECISIONS:
//
// WHY Tailwind CSS (not plain CSS, styled-components, CSS Modules):
//   - Utility-first: composable classes that co-locate styles with markup.
//   - Design tokens as config: colors, spacing, typography are defined once.
//     Changing the brand color = change one value here. No global CSS file hunt.
//   - PurgeCSS built-in: Only used classes end up in the production bundle.
//     ~5KB CSS vs 300KB for a full component library.
//   - Shadcn compatibility: Shadcn UI is built for Tailwind + CSS variables.
//
// COLOR PALETTE DESIGN:
//   HSL-based colors for precise, consistent theming.
//   WHY HSL: Adjusting lightness only is impossible with hex. HSL makes it
//   trivial to create consistent dark mode variants (same hue/saturation,
//   flipped lightness).
//
//   Primary: Indigo (#4F46E5-ish) — professional, trustworthy for B2B SaaS
//   Why indigo (not blue): Blue is overused. Indigo is distinctive, premium.
//
// =============================================================================

export default {
  // WHY darkMode: 'class' (not 'media'):
  //   Class-based dark mode lets users toggle within the app (persisted to
  //   localStorage via Zustand). System preference (media) doesn't allow
  //   app-level override.
  darkMode: ['class'],

  // Content paths for PurgeCSS — must cover all files that use Tailwind classes
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],

  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      // ── Color System (CSS Variables → Tailwind tokens) ──────────────────
      // WHY CSS variables: Enables runtime dark mode switching without
      // separate class names. Shadcn UI uses this pattern.
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        // ── Domain-specific status colors ────────────────────────────────
        // Consistent across all modules: PO status badges, inventory alerts
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
          muted: 'hsl(var(--success-muted))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
          muted: 'hsl(var(--warning-muted))',
        },
        danger: {
          DEFAULT: 'hsl(var(--danger))',
          foreground: 'hsl(var(--danger-foreground))',
          muted: 'hsl(var(--danger-muted))',
        },
        info: {
          DEFAULT: 'hsl(var(--info))',
          foreground: 'hsl(var(--info-foreground))',
          muted: 'hsl(var(--info-muted))',
        },
        // ── Sidebar ──────────────────────────────────────────────────────
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          primary: 'hsl(var(--sidebar-primary))',
          'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
          accent: 'hsl(var(--sidebar-accent))',
          'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
          border: 'hsl(var(--sidebar-border))',
          ring: 'hsl(var(--sidebar-ring))',
        },
      },

      // ── Typography ──────────────────────────────────────────────────────
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },

      // ── Border Radius ───────────────────────────────────────────────────
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },

      // ── Animations ──────────────────────────────────────────────────────
      // WHY custom animations: Tailwind defaults are generic.
      // These match the Shadcn UI + Framer Motion animation system.
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          from: { transform: 'translateX(100%)' },
          to: { transform: 'translateX(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'pulse-gentle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        shimmer: 'shimmer 2s infinite linear',
        'pulse-gentle': 'pulse-gentle 2s ease-in-out infinite',
      },

      // ── Box Shadows ─────────────────────────────────────────────────────
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.06)',
        'card-hover': '0 4px 8px rgba(0,0,0,0.06), 0 12px 32px rgba(0,0,0,0.10)',
        'sidebar': '2px 0 8px rgba(0,0,0,0.08)',
        'modal': '0 24px 64px rgba(0,0,0,0.24)',
        'glow-primary': '0 0 20px hsla(var(--primary), 0.3)',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),  // Shadcn animation utilities
  ],
}
