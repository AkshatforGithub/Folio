import "./globals.css";

export const metadata = {
  title: "Flowwatch",
  description: "Monitor n8n workflow runs and alert on failures",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground">{children}</body>
    </html>
  );
}