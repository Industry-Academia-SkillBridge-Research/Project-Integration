import { useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { MODEL_PROVIDERS } from '@/config/industryConnectApi';
import { useModelSettings } from '@/hooks/use-model-settings-ic';
import type { ModelSettings } from '@/types/industryConnect';
import PageHeader from '@/components/industryConnect/PageHeader';

export default function IndustryConnectSettings() {
  const { settings, saveSettings } = useModelSettings();
  const [draft, setDraft] = useState<ModelSettings>(settings);

  const handleSave = () => {
    saveSettings(draft);
    toast.success('Settings saved');
  };

  const hasChanges =
    draft.model_provider !== settings.model_provider ||
    draft.ollama_model !== settings.ollama_model;

  return (
    <div className="p-6 max-w-xl mx-auto">
      <PageHeader
        title="Settings"
        subtitle="Configure model provider and other preferences"
      />

      <div className="mt-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Model Configuration</CardTitle>
            <CardDescription>
              Choose which AI model backend is used for project generation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-3">
              <Label className="text-sm font-medium">Model Provider</Label>
              <RadioGroup
                value={draft.model_provider}
                onValueChange={(val) =>
                  setDraft((d) => ({
                    ...d,
                    model_provider: val as ModelSettings['model_provider'],
                  }))
                }
                className="space-y-2"
              >
                {MODEL_PROVIDERS.map((p) => (
                  <div key={p.value} className="flex items-start gap-3">
                    <RadioGroupItem value={p.value} id={`settings-${p.value}`} className="mt-0.5" />
                    <div>
                      <Label
                        htmlFor={`settings-${p.value}`}
                        className="text-sm font-normal cursor-pointer"
                      >
                        {p.label}
                      </Label>
                      {p.value === 'ollama' && (
                        <p className="text-xs text-muted-foreground">
                          Uses the locally fine-tuned Ollama model defined in the server config.
                        </p>
                      )}
                      {p.value === 'gemini' && (
                        <p className="text-xs text-muted-foreground">
                          Calls Google Gemini via the API key set on the backend.
                        </p>
                      )}
                      {p.value === 'ollama_generic' && (
                        <p className="text-xs text-muted-foreground">
                          Uses any Ollama model tag you specify below.
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </RadioGroup>
            </div>

            {draft.model_provider === 'ollama_generic' && (
              <>
                <Separator />
                <div className="space-y-1.5">
                  <Label htmlFor="ollama-model-tag" className="text-sm font-medium">
                    Ollama Model Tag
                  </Label>
                  <Input
                    id="ollama-model-tag"
                    placeholder="e.g. gemma3:1b"
                    value={draft.ollama_model}
                    onChange={(e) => setDraft((d) => ({ ...d, ollama_model: e.target.value }))}
                    className="max-w-xs"
                  />
                  <p className="text-xs text-muted-foreground">
                    Must match a model already pulled in Ollama (run{' '}
                    <code className="font-mono">ollama pull &lt;tag&gt;</code> first).
                  </p>
                </div>
              </>
            )}

            <Separator />

            <Button onClick={handleSave} disabled={!hasChanges}>
              Save Settings
            </Button>
            {!hasChanges && (
              <p className="text-xs text-muted-foreground">No unsaved changes.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
