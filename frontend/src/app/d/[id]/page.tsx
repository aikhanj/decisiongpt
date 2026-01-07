"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

import { SplitPane } from "@/components/layout/split-pane";
import { DecisionHeader } from "@/components/layout/decision-header";
import { ChatPanel } from "@/components/chat/chat-panel";
import { CanvasContainer } from "@/components/canvas/canvas-container";
import { BranchModal } from "@/components/branching/branch-modal";
import { ErrorState, getErrorMessage } from "@/components/ui/error-state";
import { Skeleton, SkeletonMessage, SkeletonCanvas } from "@/components/ui/skeleton";
import type { BranchReason } from "@/types";
import { ApiKeyPrompt } from "@/components/settings/api-key-input";
import { useKeyboardShortcuts, SHORTCUTS } from "@/hooks/use-keyboard-shortcuts";

import {
  getDecision,
  getChatHistory,
  sendChatMessage,
  chooseOption,
  createBranch,
  logOutcome,
  deleteDecision,
  hasApiKey,
} from "@/lib/api";

import type {
  Decision,
  DecisionNode,
  ChatMessage,
  CanvasState,
  Option,
  CommitPlan,
  NodePhase,
  DecisionOutcome,
} from "@/types";

interface WorkspaceState {
  decision: Decision | null;
  currentNode: DecisionNode | null;
  allNodes: DecisionNode[];
  chatMessages: ChatMessage[];
  canvasState: CanvasState | null;
  options: Option[];
  commitPlan: CommitPlan | null;
  outcome: DecisionOutcome | null;
  loading: boolean;
  chatLoading: boolean;
  error: string | null;
}

const initialState: WorkspaceState = {
  decision: null,
  currentNode: null,
  allNodes: [],
  chatMessages: [],
  canvasState: null,
  options: [],
  commitPlan: null,
  outcome: null,
  loading: true,
  chatLoading: false,
  error: null,
};

export default function DecisionWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const decisionId = params.id as string;

  const [state, setState] = useState<WorkspaceState>(initialState);
  const [branchModalOpen, setBranchModalOpen] = useState(false);
  const [branchLoading, setBranchLoading] = useState(false);
  const [apiKeySet, setApiKeySet] = useState<boolean | null>(null);
  const [autoStartTriggered, setAutoStartTriggered] = useState(false);

  // Check API key on mount
  useEffect(() => {
    setApiKeySet(hasApiKey());
  }, []);

  // Load decision data
  const loadDecision = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      const decisionData = await getDecision(decisionId);
      // Get current node from response or fallback to the most recent node
      const currentNode = decisionData.current_node ||
        (decisionData.nodes && decisionData.nodes.length > 0
          ? decisionData.nodes[decisionData.nodes.length - 1]
          : null);

      // Get chat history for current node
      let chatMessages: ChatMessage[] = [];
      if (currentNode) {
        try {
          const chatHistory = await getChatHistory(decisionId, currentNode.id);
          chatMessages = chatHistory.messages || [];
        } catch (e) {
          // Chat history may not exist yet
          console.log("No chat history yet");
        }
      }

      // Extract canvas state and other data from current node
      const canvasState = currentNode?.canvas_state_json as CanvasState | null;
      const options = (currentNode as any)?.options_json || [];
      const commitPlan = (currentNode as any)?.commit_plan_json || null;
      const outcome = (currentNode as any)?.outcome || null;

      setState({
        decision: decisionData,
        currentNode,
        allNodes: decisionData.nodes || [currentNode].filter(Boolean),
        chatMessages,
        canvasState,
        options,
        commitPlan,
        outcome,
        loading: false,
        chatLoading: false,
        error: null,
      });
    } catch (error) {
      console.error("Failed to load decision:", error);
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to load decision",
      }));
    }
  }, [decisionId]);

  useEffect(() => {
    if (decisionId && apiKeySet) {
      loadDecision();
    }
  }, [decisionId, apiKeySet, loadDecision]);

  // Auto-start conversation when chat is empty after loading
  useEffect(() => {
    const shouldAutoStart =
      !state.loading &&
      !state.chatLoading &&
      !autoStartTriggered &&
      state.chatMessages.length === 0 &&
      state.currentNode &&
      state.decision?.situation_text;

    if (shouldAutoStart) {
      setAutoStartTriggered(true);

      // Show immediate welcome message
      const welcomeMessage: ChatMessage = {
        id: `welcome-${Date.now()}`,
        role: "assistant",
        content: "Let me analyze your situation and help you think through this decision...",
        timestamp: new Date().toISOString(),
      };

      setState((prev) => ({
        ...prev,
        chatMessages: [welcomeMessage],
        chatLoading: true,
      }));

      // Trigger AI response
      sendChatMessage(
        decisionId,
        state.currentNode!.id,
        `Help me with this decision: ${state.decision!.situation_text}`
      )
        .then((response) => {
          setState((prev) => ({
            ...prev,
            chatMessages: [response.message],
            canvasState: response.canvas_state || prev.canvasState,
            chatLoading: false,
          }));
        })
        .catch((error) => {
          console.error("Failed to auto-start conversation:", error);
          setState((prev) => ({
            ...prev,
            chatMessages: [],
            chatLoading: false,
          }));
        });
    }
  }, [
    state.loading,
    state.chatLoading,
    state.chatMessages.length,
    state.currentNode,
    state.decision?.situation_text,
    autoStartTriggered,
    decisionId,
  ]);

  // Handle sending chat messages
  const handleSendMessage = useCallback(
    async (content: string) => {
      if (!state.currentNode) return;

      // Immediately show user message with animation
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };

      setState((prev) => ({
        ...prev,
        chatMessages: [...prev.chatMessages, userMessage],
        chatLoading: true,
      }));

      try {
        const response = await sendChatMessage(
          decisionId,
          state.currentNode.id,
          content
        );

        // Add assistant response
        setState((prev) => ({
          ...prev,
          chatMessages: [...prev.chatMessages, response.message],
          canvasState: response.canvas_state || prev.canvasState,
          options: response.options || prev.options,
          currentNode: {
            ...prev.currentNode!,
            phase: response.phase || prev.currentNode!.phase,
          },
          chatLoading: false,
        }));
      } catch (error) {
        console.error("Failed to send message:", error);
        const errorMessage = getErrorMessage(error);
        toast.error(errorMessage, {
          action: {
            label: "Retry",
            onClick: () => handleSendMessage(content),
          },
        });
        setState((prev) => ({ ...prev, chatLoading: false }));
      }
    },
    [decisionId, state.currentNode]
  );

  // Handle choosing an option
  const handleChooseOption = useCallback(
    async (optionId: string) => {
      if (!state.currentNode) return;

      setState((prev) => ({ ...prev, chatLoading: true }));

      try {
        const response = await chooseOption(
          decisionId,
          state.currentNode.id,
          optionId
        );

        setState((prev) => ({
          ...prev,
          commitPlan: response.commit_plan || null,
          currentNode: {
            ...prev.currentNode!,
            phase: "execute" as NodePhase,
          },
          chatMessages: [
            ...prev.chatMessages,
            response.message,
          ],
          chatLoading: false,
        }));

        toast.success("Option selected! Your action plan is ready.");
      } catch (error: any) {
        console.error("Failed to choose option:", error);
        const errorMessage = error?.detail || error?.message || getErrorMessage(error);
        toast.error(errorMessage, {
          action: {
            label: "Retry",
            onClick: () => handleChooseOption(optionId),
          },
        });
        setState((prev) => ({ ...prev, chatLoading: false }));
      }
    },
    [decisionId, state.currentNode]
  );

  // Handle creating a branch
  const handleCreateBranch = useCallback(
    async (reason: BranchReason, details: string) => {
      if (!state.currentNode) return;

      setBranchLoading(true);

      try {
        const response = await createBranch(decisionId, state.currentNode.id, {
          reason,
          details,
        });

        toast.success("Branch created! Exploring alternative path...");
        setBranchModalOpen(false);

        // Reload to get new branch
        await loadDecision();
      } catch (error) {
        console.error("Failed to create branch:", error);
        toast.error("Failed to create branch");
      } finally {
        setBranchLoading(false);
      }
    },
    [decisionId, state.currentNode, loadDecision]
  );

  // Handle logging outcome
  const handleLogOutcome = useCallback(
    async (outcomeData: {
      progress_yesno: boolean;
      sentiment_2h?: number;
      sentiment_24h?: number;
      notes?: string;
    }) => {
      if (!state.currentNode) return;

      try {
        const response = await logOutcome(
          decisionId,
          state.currentNode.id,
          outcomeData
        );

        setState((prev) => ({
          ...prev,
          outcome: response,
        }));

        toast.success("Outcome logged successfully!");
      } catch (error) {
        console.error("Failed to log outcome:", error);
        toast.error("Failed to log outcome");
      }
    },
    [decisionId, state.currentNode]
  );

  // Handle navigating to a different node
  const handleNavigateNode = useCallback(
    (nodeId: string) => {
      const node = state.allNodes.find((n) => n.id === nodeId);
      if (node) {
        setState((prev) => ({
          ...prev,
          currentNode: node,
          canvasState: node.canvas_state_json as CanvasState | null,
          options: (node as any)?.options_json || [],
          commitPlan: (node as any)?.commit_plan_json || null,
        }));
      }
    },
    [state.allNodes]
  );

  // Handle title update
  const handleTitleUpdate = useCallback(
    (newTitle: string) => {
      setState((prev) => ({
        ...prev,
        decision: prev.decision ? { ...prev.decision, title: newTitle } : null,
      }));
      // TODO: Persist title update to backend
    },
    []
  );

  // Handle delete decision
  const handleDeleteDecision = useCallback(async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this decision? This action cannot be undone."
    );

    if (!confirmed) return;

    try {
      await deleteDecision(decisionId);
      toast.success("Decision deleted");
      router.push("/");
    } catch (error) {
      console.error("Failed to delete decision:", error);
      toast.error("Failed to delete decision");
    }
  }, [decisionId, router]);

  // API key not set
  if (apiKeySet === false) {
    return (
      <div className="h-screen flex items-center justify-center p-8">
        <div className="max-w-md w-full space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold">API Key Required</h1>
            <p className="text-muted-foreground">
              Set your OpenAI API key to continue with this decision.
            </p>
          </div>
          <ApiKeyPrompt onKeySet={() => setApiKeySet(true)} />
        </div>
      </div>
    );
  }

  // Loading state with skeleton
  if (state.loading || apiKeySet === null) {
    return (
      <div className="h-screen flex flex-col">
        {/* Skeleton Header */}
        <div className="flex items-center justify-between gap-4 px-6 py-4 border-b bg-background">
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-10 rounded" />
            <Skeleton className="h-2 w-2 rounded-full" />
            <Skeleton className="h-6 w-48" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
          </div>
        </div>

        {/* Skeleton Content */}
        <div className="flex-1 flex">
          {/* Chat skeleton */}
          <div className="w-1/2 border-r p-4 space-y-4">
            <SkeletonMessage />
            <SkeletonMessage isUser />
            <SkeletonMessage />
          </div>
          {/* Canvas skeleton */}
          <div className="w-1/2">
            <SkeletonCanvas />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (state.error) {
    return (
      <div className="h-screen flex items-center justify-center p-8">
        <ErrorState
          title="Failed to load decision"
          message={state.error}
          onRetry={loadDecision}
          showHomeButton
        />
      </div>
    );
  }

  const currentPhase = state.currentNode?.phase || "clarify";

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <DecisionHeader
        title={state.decision?.title || "Untitled Decision"}
        status={state.decision?.status || "active"}
        phase={currentPhase}
        onTitleChange={handleTitleUpdate}
        onBranchClick={() => setBranchModalOpen(true)}
        onOutcomeClick={() => {
          // Switch to outcome tab - handled by canvas
        }}
        onDeleteClick={handleDeleteDecision}
      />

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        <SplitPane
          left={
            <ChatPanel
              messages={state.chatMessages}
              onSendMessage={handleSendMessage}
              isLoading={state.chatLoading}
            />
          }
          right={
            <CanvasContainer
              phase={currentPhase}
              canvasState={state.canvasState}
              options={state.options}
              commitPlan={state.commitPlan}
              outcome={state.outcome}
              nodes={state.allNodes}
              currentNodeId={state.currentNode?.id || ""}
              onChooseOption={handleChooseOption}
              onLogOutcome={handleLogOutcome}
              onNavigateNode={handleNavigateNode}
            />
          }
        />
      </div>

      {/* Branch modal */}
      <BranchModal
        open={branchModalOpen}
        onOpenChange={setBranchModalOpen}
        onCreateBranch={handleCreateBranch}
        isLoading={branchLoading}
      />
    </div>
  );
}
