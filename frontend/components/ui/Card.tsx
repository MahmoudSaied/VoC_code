import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface CardProps {
    children: ReactNode;
    className?: string;
    title?: string;
}

export function Card({ children, className, title }: CardProps) {
    return (
        <div className={cn("bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden", className)}>
            {title && (
                <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
                    <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
                </div>
            )}
            <div className="p-6">{children}</div>
        </div>
    );
}
