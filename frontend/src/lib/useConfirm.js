import { useCallback, useState } from 'react';

/**
 * Promise-based confirm() replacement that works inside iOS standalone PWAs
 * (where window.confirm() is silently blocked).
 *
 * Usage:
 *   const [confirm, confirmProps] = useConfirm();
 *   ...
 *   if (!(await confirm({ title: 'Cancel workout?', destructive: true }))) return;
 *   ...
 *   <ConfirmModal {...confirmProps} />
 */
export default function useConfirm() {
  const [state, setState] = useState({ open: false });

  const confirm = useCallback((opts = {}) => {
    return new Promise((resolve) => {
      setState({
        open: true,
        title: opts.title,
        message: opts.message,
        confirmLabel: opts.confirmLabel,
        cancelLabel: opts.cancelLabel,
        destructive: !!opts.destructive,
        _resolve: resolve,
      });
    });
  }, []);

  const close = (result) => {
    setState((s) => {
      s._resolve?.(result);
      return { open: false };
    });
  };

  const modalProps = {
    open: state.open,
    title: state.title,
    message: state.message,
    confirmLabel: state.confirmLabel,
    cancelLabel: state.cancelLabel,
    destructive: state.destructive,
    onConfirm: () => close(true),
    onCancel: () => close(false),
  };

  return [confirm, modalProps];
}
