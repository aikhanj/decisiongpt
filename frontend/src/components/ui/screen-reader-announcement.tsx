"use client";

interface ScreenReaderAnnouncementProps {
  message: string | null;
}

export function ScreenReaderAnnouncement({
  message,
}: ScreenReaderAnnouncementProps) {
  if (!message) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  );
}
