/**
 * Test utilities and custom render functions.
 */

import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string;
}

/**
 * Custom render function with router wrapper.
 */
export function renderWithRouter(
  ui: ReactElement,
  { route = '/', ...renderOptions }: CustomRenderOptions = {}
) {
  window.history.pushState({}, 'Test page', route);

  return render(ui, {
    wrapper: ({ children }) => <BrowserRouter>{children}</BrowserRouter>,
    ...renderOptions,
  });
}

/**
 * Helper to create mock functions with type safety.
 */
export function createMockFn<T extends (...args: any[]) => any>(): T {
  return (() => {}) as T;
}
