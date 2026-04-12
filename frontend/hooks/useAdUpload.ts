'use client';

import { useCallback, useState } from 'react';

export type AdInputMode = 'file' | 'url';

export interface AdUploadState {
  mode: AdInputMode;
  file: File | null;
  url: string;
  preview: string | null;
  error: string | null;
}

export function useAdUpload() {
  const [state, setState] = useState<AdUploadState>({
    mode: 'file',
    file: null,
    url: '',
    preview: null,
    error: null,
  });

  const setMode = useCallback((mode: AdInputMode) => {
    setState((prev) => ({ ...prev, mode, error: null }));
  }, []);

  const onFileSelect = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      setState((prev) => ({ ...prev, error: 'Please select an image file' }));
      return;
    }
    const preview = URL.createObjectURL(file);
    setState((prev) => ({ ...prev, file, preview, error: null }));
  }, []);

  const onUrlChange = useCallback((url: string) => {
    setState((prev) => ({ ...prev, url, preview: url || null, error: null }));
  }, []);

  const clear = useCallback(() => {
    if (state.preview && state.file) URL.revokeObjectURL(state.preview);
    setState({ mode: 'file', file: null, url: '', preview: null, error: null });
  }, [state.preview, state.file]);

  const hasInput = state.file !== null || state.url.trim().length > 0;

  return { state, setMode, onFileSelect, onUrlChange, clear, hasInput };
}
