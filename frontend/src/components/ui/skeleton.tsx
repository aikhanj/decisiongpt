import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
      {...props}
    />
  );
}

// Pre-built skeleton components for common use cases
export function SkeletonCard() {
  return (
    <div className="rounded-xl border bg-card p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <Skeleton className="h-20 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-24" />
      </div>
    </div>
  );
}

export function SkeletonMessage({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={cn("flex gap-3 px-5 py-2", isUser && "flex-row-reverse")}>
      <Skeleton className="h-8 w-8 rounded-full shrink-0" />
      <div className={cn("space-y-2 flex-1", isUser && "flex flex-col items-end")}>
        <Skeleton className={cn("h-4", isUser ? "w-1/2" : "w-3/4")} />
        <Skeleton className={cn("h-4", isUser ? "w-1/3" : "w-2/3")} />
        {!isUser && <Skeleton className="h-4 w-1/2" />}
      </div>
    </div>
  );
}

export function SkeletonOptionCard() {
  return (
    <div className="rounded-xl border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
      <Skeleton className="h-5 w-full" />
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/30 p-3 space-y-2">
          <Skeleton className="h-3 w-16 bg-emerald-200/50" />
          <Skeleton className="h-4 w-full bg-emerald-200/30" />
        </div>
        <div className="rounded-lg bg-amber-50 dark:bg-amber-950/30 p-3 space-y-2">
          <Skeleton className="h-3 w-16 bg-amber-200/50" />
          <Skeleton className="h-4 w-full bg-amber-200/30" />
        </div>
      </div>
      <Skeleton className="h-10 w-full" />
    </div>
  );
}

export function SkeletonCanvas() {
  return (
    <div className="p-6 space-y-6">
      <div className="space-y-3">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      <div className="grid gap-4">
        <Skeleton className="h-24 w-full rounded-lg" />
        <Skeleton className="h-24 w-full rounded-lg" />
      </div>
    </div>
  );
}
