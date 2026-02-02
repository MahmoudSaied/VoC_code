"use client";

import { useState } from "react";
import { Company, VoCService } from "@/lib/api";
import { Card } from "../ui/Card";
import { Loader2, Play, AlertCircle } from "lucide-react";

interface StepAppIdsProps {
    initialData: Company[];
    onComplete: (data: { job_id: string; brands: Company[] }) => void;
}

export function StepAppIds({ initialData, onComplete }: StepAppIdsProps) {
    const [items, setItems] = useState<Company[]>(initialData);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateItem = (index: number, field: keyof Company, value: string) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };
        setItems(newItems);
    };

    const handleStartScraping = async () => {
        setLoading(true);
        setError(null);

        // Generate Job ID
        const jobId = `job_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

        try {
            const response = await VoCService.startScraping({
                brands: items,
                job_id: jobId
            });

            onComplete({ job_id: jobId, brands: items });

        } catch (err) {
            console.error(err);
            setError("Failed to start scraping job. Check backend connection.");
            setLoading(false); // Only stop loading on error, otherwise parent handles flow
        }
    };

    return (
        <Card title="Step 3: Verify App Store IDs" className="w-full max-w-2xl mx-auto">
            <div className="space-y-4">
                <div className="bg-calo-mint p-3 rounded-md flex gap-2 text-sm text-calo-green-dark border border-calo-green-primary/20">
                    <AlertCircle className="h-5 w-5 shrink-0 text-calo-green-primary" />
                    <p>
                        Check the IDs below. If an ID is missing or incorrect, you can edit it manually.
                        Only rows with at least one ID will be scraped.
                    </p>
                </div>

                <div className="space-y-3">
                    {items.map((item, index) => (
                        <div key={index} className="p-3 bg-white rounded-lg border border-slate-200 shadow-sm">
                            <h4 className="font-semibold text-calo-text-main mb-2 truncate">
                                {item.company_name}
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-semibold text-calo-text-secondary block mb-1">Android App ID</label>
                                    <input
                                        type="text"
                                        value={item.android_id || ""}
                                        onChange={(e) => updateItem(index, "android_id", e.target.value)}
                                        placeholder="com.example.app"
                                        className="w-full rounded border border-calo-border px-2 py-1.5 text-sm font-mono text-calo-text-main focus:ring-1 focus:ring-calo-primary"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-calo-text-secondary block mb-1">Apple App ID</label>
                                    <input
                                        type="text"
                                        value={item.apple_id || ""}
                                        onChange={(e) => updateItem(index, "apple_id", e.target.value)}
                                        placeholder="123456789"
                                        className="w-full rounded border border-calo-border px-2 py-1.5 text-sm font-mono text-calo-text-main focus:ring-1 focus:ring-calo-primary"
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {error && <p className="text-sm text-red-500">{error}</p>}

                <button
                    onClick={handleStartScraping}
                    disabled={loading}
                    className="w-full mt-4 flex items-center justify-center gap-2 bg-calo-primary hover:bg-calo-dark text-white font-bold py-3 px-4 rounded-full shadow-md hover:shadow-lg transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <>
                            <Loader2 className="h-5 w-5 animate-spin" /> Starting Job...
                        </>
                    ) : (
                        <>
                            <Play className="h-5 w-5" /> Start Scraping Reviews
                        </>
                    )}
                </button>
            </div>
        </Card>
    );
}
