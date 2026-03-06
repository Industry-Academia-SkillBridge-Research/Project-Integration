import { useState } from 'react';
import type { ModelSettings } from '@/types/industryConnect';

const STORAGE_KEY = 'industry-connect-model-settings';

const DEFAULT_SETTINGS: ModelSettings = {
  model_provider: 'ollama',
  ollama_model: '',
};

function loadSettings(): ModelSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function useModelSettings() {
  const [settings, setSettings] = useState<ModelSettings>(loadSettings);

  const saveSettings = (next: ModelSettings) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // quota exceeded or private browsing — silently ignore
    }
    setSettings(next);
  };

  return { settings, saveSettings };
}
