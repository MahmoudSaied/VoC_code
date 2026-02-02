import VocStepper from "@/components/stepper/VocStepper";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center py-12 font-[family-name:var(--font-geist-sans)]">
      <div className="w-full max-w-5xl px-4 mb-8 text-center">
        <h1 className="text-4xl font-extrabold text-slate-800 mb-2 tracking-tight">
          VoC Intelligence Platform
        </h1>
        <p className="text-slate-500 text-lg">
          Automated Review Analysis & Insight Generation
        </p>
      </div>

      <VocStepper />

      <footer className="mt-16 text-xs text-slate-400">
        &copy; {new Date().getFullYear()} HorusCX. All rights reserved.
      </footer>
    </main>
  );
}
