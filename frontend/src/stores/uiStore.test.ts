/**
 * UI Store tests.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useUIStore } from './uiStore';

describe('uiStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useUIStore.setState({
      toasts: [],
      modals: [],
    });
  });

  describe('Toasts', () => {
    it('adds a toast', () => {
      const { addToast } = useUIStore.getState();
      addToast('Test message', 'success');

      const { toasts } = useUIStore.getState();
      expect(toasts).toHaveLength(1);
      expect(toasts[0].message).toBe('Test message');
      expect(toasts[0].type).toBe('success');
    });

    it('generates unique IDs for toasts', () => {
      const { addToast } = useUIStore.getState();
      addToast('Message 1', 'info');
      addToast('Message 2', 'info');

      const { toasts } = useUIStore.getState();
      expect(toasts[0].id).not.toBe(toasts[1].id);
    });

    it('removes a toast by ID', () => {
      const { addToast, removeToast } = useUIStore.getState();
      addToast('Test message', 'success');

      const { toasts: toastsBeforeRemove } = useUIStore.getState();
      const toastId = toastsBeforeRemove[0].id;

      removeToast(toastId);

      const { toasts: toastsAfterRemove } = useUIStore.getState();
      expect(toastsAfterRemove).toHaveLength(0);
    });

    it('supports different toast types', () => {
      const { addToast } = useUIStore.getState();

      addToast('Success', 'success');
      addToast('Error', 'error');
      addToast('Warning', 'warning');
      addToast('Info', 'info');

      const { toasts } = useUIStore.getState();
      expect(toasts).toHaveLength(4);
      expect(toasts[0].type).toBe('success');
      expect(toasts[1].type).toBe('error');
      expect(toasts[2].type).toBe('warning');
      expect(toasts[3].type).toBe('info');
    });

    it('defaults to info type when not specified', () => {
      const { addToast } = useUIStore.getState();
      addToast('Default message');

      const { toasts } = useUIStore.getState();
      expect(toasts[0].type).toBe('info');
    });
  });

  describe('Modals', () => {
    it('opens a modal', () => {
      const { openModal } = useUIStore.getState();
      openModal('test-modal', { data: 'test' });

      const { modal } = useUIStore.getState();
      expect(modal).not.toBeNull();
      expect(modal?.type).toBe('test-modal');
      expect(modal?.props).toEqual({ data: 'test' });
    });

    it('closes a modal', () => {
      const { openModal, closeModal } = useUIStore.getState();
      openModal('test-modal');
      closeModal();

      const { modal } = useUIStore.getState();
      expect(modal).toBeNull();
    });

    it('replaces modal when opening a new one', () => {
      const { openModal } = useUIStore.getState();
      openModal('modal-1');
      openModal('modal-2');

      const { modal } = useUIStore.getState();
      expect(modal?.type).toBe('modal-2');
    });

    it('opens modal without props', () => {
      const { openModal } = useUIStore.getState();
      openModal('simple-modal');

      const { modal } = useUIStore.getState();
      expect(modal).not.toBeNull();
      expect(modal?.type).toBe('simple-modal');
      expect(modal?.props).toEqual({});
    });
  });
});
