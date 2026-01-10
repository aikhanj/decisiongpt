import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Decision Canvas",
  description: "Make better decisions with AI-powered structured thinking",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:top-2 focus:left-2 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-lg"
        >
          Skip to main content
        </a>
        <TooltipProvider>
          <div className="min-h-screen bg-background">
            {children}
          </div>
          <Toaster
            position="bottom-right"
            richColors
            toastOptions={{
              duration: 4000,
              className: 'backdrop-blur-sm',
              style: {
                border: '1px solid hsl(var(--border))',
                boxShadow: 'var(--shadow-lg)',
              },
            }}
          />
        </TooltipProvider>
      </body>
    </html>
  );
}
