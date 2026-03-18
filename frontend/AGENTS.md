# GraphSentinel Frontend Agent Guidelines

## Overview
This document provides guidance for AI agents working on the GraphSentinel frontend - an AI-powered AML fraud detection dashboard built with Next.js, React, and TypeScript.

## Codebase Structure
- `src/app/` - Next.js app router (page.tsx, layout.tsx, globals.css)
- `src/components/` - Reusable UI components
  - `AdversarialTestPanel.tsx` - Fraud detection test runner
  - `AgentActivityPanel.tsx` - Multi-agent timeline visualization
  - `AlertFeed.tsx` - Alert list with filtering and investigation
  - `FilterBar.tsx` - Collapsible filter controls
  - `GraphVisualizer.tsx` - Force-directed knowledge graph visualization
  - `RiskRing.tsx` - Risk score circular indicator
  - `SARReport.tsx` - Suspicious Activity Report viewer
  - `StatsCard.tsx` - Animated metric cards
  - `ThemeToggle.tsx` - Dark/light mode switch
  - `ui/` - shadcn/ui primitives (button, card, table, tabs, etc.)
- `src/lib/` - Utility functions (clsx/tailwind-merge wrapper)
- `src/types/` - TypeScript interfaces for API responses
- `tests/e2e/` - Playwright end-to-end tests

## Key Patterns
1. **Client Components**: All interactive components use `"use client"` directive
2. **State Management**: React hooks (useState, useMemo) - no external state library
3. **Styling**: Tailwind CSS v4 with custom CSS variables for theming
4. **Animations**: Framer Motion for layout and enter/exit transitions
5. **Data Fetching**: Direct fetch() calls to backend API at http://localhost:8000
6. **Component Composition**: Hierarchical structure with Dashboard as root

## Development Commands
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run test:e2e` - Run Playwright E2E tests

## API Endpoints Consumed
- POST /api/run-pipeline - Execute synthetic pipeline (Track B)
- GET /api/demo-track-a - Retrieve pre-cached results (Track A)
- POST /api/run-pipeline-csv - Process uploaded CSV files
- GET /api/adversarial-test?test=<id> - Run adversarial fraud tests
- POST /api/feedback - Submit investigator feedback on alerts

## Testing Strategy
- E2E tests only with Playwright (tests/e2e/dashboard.spec.ts)
- No unit/jest tests currently implemented
- Tests cover: dashboard loading, panel visibility, Track A execution, scrollability

## Styling & Theming
- Dark theme by default with light mode toggle
- Custom CSS variables in globals.css for colors, radii, effects
- Glass morphism, risk-score color coding, animated transitions
- Uses shadcn/ui base-nova style with lucide icons

## Dependencies of Note
- @base-ui/react - Headless UI primitives
- framer-motion - Animation library
- react-force-graph-2d - Knowledge graph visualization
- html2pdf.js - PDF export for SAR reports
- lucide-react - Icon library
- tailwindcss@4 - Utility-first CSS framework