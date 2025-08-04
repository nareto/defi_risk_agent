import "./globals.css";
import { ReactNode } from "react";

export const metadata = {
    title: "DeFi Risk Analyzer",
};

export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="en">
            <body className="min-h-screen bg-gray-50 text-gray-900">
                <main className="container mx-auto p-4 max-w-3xl">{children}</main>
            </body>
        </html>
    );
}
