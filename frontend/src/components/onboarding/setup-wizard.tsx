"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Cpu,
  Cloud,
  Check,
  ChevronRight,
  ChevronLeft,
  Download,
  Loader2,
  AlertCircle,
  ExternalLink,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import {
  type LLMProvider,
  type OllamaModel,
  type AvailableModel,
  checkOllamaStatus,
  getAvailableModels,
  pullOllamaModel,
  saveSettings,
  testOpenAIKey,
  setLLMProvider,
  setApiKey,
} from "@/lib/api";

interface SetupWizardProps {
  open: boolean;
  onComplete: () => void;
}

type Step = "provider" | "ollama-setup" | "openai-setup" | "complete";

export function SetupWizard({ open, onComplete }: SetupWizardProps) {
  const [step, setStep] = useState<Step>("provider");
  const [provider, setProvider] = useState<LLMProvider | null>(null);

  // Ollama state
  const [ollamaStatus, setOllamaStatus] = useState<"checking" | "running" | "not_running">("checking");
  const [installedModels, setInstalledModels] = useState<OllamaModel[]>([]);
  const [availableModels, setAvailableModels] = useState<AvailableModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadStatus, setDownloadStatus] = useState("");
  const [showDownloadSection, setShowDownloadSection] = useState(false);

  // OpenAI state
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [isTestingKey, setIsTestingKey] = useState(false);
  const [keyValid, setKeyValid] = useState<boolean | null>(null);
  const [keyError, setKeyError] = useState<string | null>(null);

  // Saving state
  const [isSaving, setIsSaving] = useState(false);

  // Check Ollama status when entering Ollama setup
  useEffect(() => {
    if (step === "ollama-setup") {
      checkOllama();
      loadAvailableModels();
    }
  }, [step]);

  const checkOllama = async () => {
    setOllamaStatus("checking");
    const status = await checkOllamaStatus();
    setOllamaStatus(status.status === "running" ? "running" : "not_running");
    setInstalledModels(status.installed_models || []);

    // Auto-select first installed model if available
    if (status.installed_models?.length > 0 && !selectedModel) {
      setSelectedModel(status.installed_models[0].name);
    }
  };

  const loadAvailableModels = async () => {
    const { models } = await getAvailableModels();
    setAvailableModels(models);
  };

  const handleProviderSelect = (p: LLMProvider) => {
    setProvider(p);
    setStep(p === "ollama" ? "ollama-setup" : "openai-setup");
  };

  const handleDownloadModel = async (modelName: string) => {
    setIsDownloading(true);
    setDownloadProgress(0);
    setDownloadStatus("Starting download...");

    try {
      await pullOllamaModel(modelName, (status, progress) => {
        setDownloadStatus(status);
        if (progress !== undefined) {
          setDownloadProgress(progress);
        }
      });

      // Refresh model list
      await checkOllama();
      setSelectedModel(modelName);
      setShowDownloadSection(false);
    } catch (error) {
      setDownloadStatus(`Error: ${error instanceof Error ? error.message : "Download failed"}`);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleTestApiKey = async () => {
    if (!apiKeyInput.trim()) return;

    setIsTestingKey(true);
    setKeyValid(null);
    setKeyError(null);

    const result = await testOpenAIKey(apiKeyInput);
    setKeyValid(result.valid);
    if (!result.valid) {
      setKeyError(result.message);
    }
    setIsTestingKey(false);
  };

  const handleComplete = async () => {
    if (!provider) return;

    setIsSaving(true);
    try {
      await saveSettings({
        llm_provider: provider,
        ollama_model: provider === "ollama" ? selectedModel || undefined : undefined,
        openai_api_key: provider === "openai" ? apiKeyInput : undefined,
      });

      // Also save to localStorage for client-side use
      setLLMProvider(provider);
      if (provider === "openai" && apiKeyInput) {
        setApiKey(apiKeyInput);
      }

      setStep("complete");
      setTimeout(() => {
        onComplete();
      }, 1500);
    } catch (error) {
      console.error("Failed to save settings:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const canProceed = () => {
    if (step === "ollama-setup") {
      return ollamaStatus === "running" && selectedModel;
    }
    if (step === "openai-setup") {
      return keyValid === true;
    }
    return false;
  };

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-xl p-0 overflow-hidden" hideCloseButton>
        <DialogHeader className="p-6 pb-0">
          <DialogTitle className="flex items-center gap-2 text-xl">
            <Sparkles className="w-5 h-5 text-primary" />
            Welcome to Decision Canvas
          </DialogTitle>
        </DialogHeader>

        <div className="p-6">
          <AnimatePresence mode="wait">
            {/* Step 1: Provider Selection */}
            {step === "provider" && (
              <motion.div
                key="provider"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-8">
                  <h2 className="text-lg font-semibold mb-2">Choose Your AI Provider</h2>
                  <p className="text-muted-foreground">
                    How would you like to run AI for decision analysis?
                  </p>
                </div>

                <div className="grid gap-4">
                  {/* Ollama Option */}
                  <button
                    onClick={() => handleProviderSelect("ollama")}
                    className={cn(
                      "p-6 rounded-xl border-2 text-left transition-all hover:border-primary/50 hover:bg-muted/50",
                      provider === "ollama" ? "border-primary bg-primary/5" : "border-border"
                    )}
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-lg bg-emerald-500/10">
                        <Cpu className="w-6 h-6 text-emerald-500" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">Offline (Ollama)</h3>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600">
                            Recommended
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">
                          Run AI locally on your computer. Free, private, and works offline.
                        </p>
                        <div className="flex flex-wrap gap-2 text-xs">
                          <span className="px-2 py-1 rounded bg-muted">Free forever</span>
                          <span className="px-2 py-1 rounded bg-muted">100% private</span>
                          <span className="px-2 py-1 rounded bg-muted">Works offline</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </button>

                  {/* OpenAI Option */}
                  <button
                    onClick={() => handleProviderSelect("openai")}
                    className={cn(
                      "p-6 rounded-xl border-2 text-left transition-all hover:border-primary/50 hover:bg-muted/50",
                      provider === "openai" ? "border-primary bg-primary/5" : "border-border"
                    )}
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-lg bg-blue-500/10">
                        <Cloud className="w-6 h-6 text-blue-500" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold mb-1">Cloud (OpenAI)</h3>
                        <p className="text-sm text-muted-foreground mb-3">
                          Use OpenAI's GPT-4 models. Requires API key and internet.
                        </p>
                        <div className="flex flex-wrap gap-2 text-xs">
                          <span className="px-2 py-1 rounded bg-muted">Most capable</span>
                          <span className="px-2 py-1 rounded bg-muted">Pay per use</span>
                          <span className="px-2 py-1 rounded bg-muted">Needs internet</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-muted-foreground" />
                    </div>
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 2a: Ollama Setup */}
            {step === "ollama-setup" && (
              <motion.div
                key="ollama"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-6">
                  <h2 className="text-lg font-semibold mb-2">Ollama Setup</h2>
                  <p className="text-muted-foreground">
                    Select a model to use for AI analysis
                  </p>
                </div>

                {/* Ollama Status */}
                <div className={cn(
                  "p-4 rounded-lg flex items-center gap-3",
                  ollamaStatus === "checking" && "bg-muted",
                  ollamaStatus === "running" && "bg-emerald-500/10",
                  ollamaStatus === "not_running" && "bg-amber-500/10"
                )}>
                  {ollamaStatus === "checking" && (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Checking Ollama status...</span>
                    </>
                  )}
                  {ollamaStatus === "running" && (
                    <>
                      <Check className="w-5 h-5 text-emerald-500" />
                      <span className="text-emerald-700">Ollama is running</span>
                      <Button variant="ghost" size="sm" className="ml-auto" onClick={checkOllama}>
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    </>
                  )}
                  {ollamaStatus === "not_running" && (
                    <>
                      <AlertCircle className="w-5 h-5 text-amber-500" />
                      <div className="flex-1">
                        <span className="text-amber-700">Ollama is not running</span>
                        <p className="text-xs text-muted-foreground mt-1">
                          Please start Ollama or{" "}
                          <a
                            href="https://ollama.ai"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline inline-flex items-center gap-1"
                          >
                            install it <ExternalLink className="w-3 h-3" />
                          </a>
                        </p>
                      </div>
                      <Button variant="outline" size="sm" onClick={checkOllama}>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Retry
                      </Button>
                    </>
                  )}
                </div>

                {/* Installed Models */}
                {ollamaStatus === "running" && installedModels.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium">Installed Models</h3>
                    <div className="space-y-2">
                      {installedModels.map((model) => (
                        <button
                          key={model.name}
                          onClick={() => setSelectedModel(model.name)}
                          className={cn(
                            "w-full p-3 rounded-lg border text-left transition-all flex items-center justify-between",
                            selectedModel === model.name
                              ? "border-primary bg-primary/5"
                              : "border-border hover:border-primary/50"
                          )}
                        >
                          <div>
                            <span className="font-medium">{model.name}</span>
                            <span className="text-xs text-muted-foreground ml-2">
                              {model.size}
                            </span>
                          </div>
                          {selectedModel === model.name && (
                            <Check className="w-4 h-4 text-primary" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Download New Model */}
                {ollamaStatus === "running" && (
                  <div className="space-y-3">
                    <button
                      onClick={() => setShowDownloadSection(!showDownloadSection)}
                      className="text-sm text-primary hover:underline flex items-center gap-1"
                    >
                      <Download className="w-4 h-4" />
                      {installedModels.length > 0 ? "Download a different model" : "Download a model"}
                    </button>

                    {showDownloadSection && (
                      <div className="space-y-2 p-4 rounded-lg bg-muted/50">
                        {isDownloading ? (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span className="text-sm">{downloadStatus}</span>
                            </div>
                            <Progress value={downloadProgress} />
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {availableModels.map((model) => (
                              <button
                                key={model.name}
                                onClick={() => handleDownloadModel(model.name)}
                                disabled={installedModels.some((m) => m.name.startsWith(model.name))}
                                className={cn(
                                  "w-full p-3 rounded-lg border text-left transition-all",
                                  installedModels.some((m) => m.name.startsWith(model.name))
                                    ? "opacity-50 cursor-not-allowed"
                                    : "hover:border-primary/50 hover:bg-background"
                                )}
                              >
                                <div className="flex items-center justify-between">
                                  <div>
                                    <span className="font-medium">{model.display_name}</span>
                                    {model.recommended && (
                                      <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                                        Recommended
                                      </span>
                                    )}
                                  </div>
                                  <span className="text-xs text-muted-foreground">{model.size}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {model.description}
                                </p>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* No models message */}
                {ollamaStatus === "running" && installedModels.length === 0 && !showDownloadSection && (
                  <div className="text-center py-4 text-muted-foreground">
                    <p>No models installed. Download one to get started.</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 2b: OpenAI Setup */}
            {step === "openai-setup" && (
              <motion.div
                key="openai"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                <div className="text-center mb-6">
                  <h2 className="text-lg font-semibold mb-2">OpenAI Setup</h2>
                  <p className="text-muted-foreground">
                    Enter your OpenAI API key to use GPT-4
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">API Key</label>
                    <div className="flex gap-2">
                      <Input
                        type="password"
                        placeholder="sk-..."
                        value={apiKeyInput}
                        onChange={(e) => {
                          setApiKeyInput(e.target.value);
                          setKeyValid(null);
                          setKeyError(null);
                        }}
                      />
                      <Button
                        variant="outline"
                        onClick={handleTestApiKey}
                        disabled={!apiKeyInput.trim() || isTestingKey}
                      >
                        {isTestingKey ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          "Test"
                        )}
                      </Button>
                    </div>
                    {keyValid === true && (
                      <p className="text-sm text-emerald-600 flex items-center gap-1">
                        <Check className="w-4 h-4" /> API key is valid
                      </p>
                    )}
                    {keyValid === false && (
                      <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" /> {keyError}
                      </p>
                    )}
                  </div>

                  <div className="p-4 rounded-lg bg-muted/50 text-sm">
                    <p className="text-muted-foreground">
                      Your API key is stored locally and sent directly to OpenAI.
                      We never see or store your key on our servers.
                    </p>
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline inline-flex items-center gap-1 mt-2"
                    >
                      Get an API key from OpenAI <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Complete */}
            {step === "complete" && (
              <motion.div
                key="complete"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8"
              >
                <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-emerald-500" />
                </div>
                <h2 className="text-xl font-semibold mb-2">You're all set!</h2>
                <p className="text-muted-foreground">
                  Start making better decisions with AI.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation */}
        {step !== "complete" && (
          <div className="flex items-center justify-between p-6 pt-0 border-t mt-4">
            <Button
              variant="ghost"
              onClick={() => setStep("provider")}
              disabled={step === "provider"}
              className="gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </Button>

            {step !== "provider" && (
              <Button
                onClick={handleComplete}
                disabled={!canProceed() || isSaving}
                className="gap-2"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Get Started
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
