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
import type { BranchReason } from "@/types";
import { ApiKeyPrompt } from "@/components/settings/api-key-input";

import {
  getDecision,
  getChatHistory,
  sendChatMessage,
  chooseOption,
  createBranch,
  logOutcome,
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

      setState((prev) => ({ ...prev, chatLoading: true }));

      try {
        const response = await sendChatMessage(
          decisionId,
          state.currentNode.id,
          content
        );

        // Update state with new messages and canvas state
        setState((prev) => ({
          ...prev,
          chatMessages: [
            ...prev.chatMessages,
            { id: `user-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString() },
            response.message,
          ],
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
        toast.error("Failed to send message");
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
      } catch (error) {
        console.error("Failed to choose option:", error);
        toast.error("Failed to select option");
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

  // Loading state
  if (state.loading || apiKeySet === null) {
    return (
      <div className="h-screen flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center space-y-4"
        >
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading decision...</p>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (state.error) {
    return (
      <div className="h-screen flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4 max-w-md"
        >
          <h2 className="text-xl font-semibold text-destructive">
            Failed to load decision
          </h2>
          <p className="text-muted-foreground">{state.error}</p>
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => router.push("/")}
              className="px-4 py-2 rounded-lg bg-muted hover:bg-muted/80"
            >
              Go Home
            </button>
            <button
              onClick={loadDecision}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Retry
            </button>
          </div>
        </motion.div>
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
