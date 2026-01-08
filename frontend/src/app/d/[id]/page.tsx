import DecisionWorkspaceClient from "./workspace-client";

// Required for Next.js static export with dynamic routes
// We generate a placeholder page; actual IDs are resolved client-side
export function generateStaticParams() {
  return [{ id: "_" }];
}


export default function DecisionWorkspacePage() {
  return <DecisionWorkspaceClient />;
}
