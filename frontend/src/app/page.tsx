"use client";

import { useState, useRef } from "react";
import { ArrowUpRight, Upload, X } from "lucide-react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { startPipelineRun } from "@/lib/api";

export default function Home() {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState("");
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    setIsExecuting(true);
    setError("");
    
    try {
      const runId = await startPipelineRun(url, file);
      router.push(`/run/${runId}`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to initiate execution");
      setIsExecuting(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col relative w-full overflow-x-hidden">
      
      {/* Structural Grid Background Lines */}
      <div className="absolute inset-0 pointer-events-none z-0 opacity-20">
        <div className="absolute top-0 bottom-0 left-[10%] w-[1px] bg-white" />
        <div className="absolute top-0 bottom-0 left-[50%] w-[1px] bg-white hidden md:block" />
        <div className="absolute top-0 bottom-0 right-[10%] w-[1px] bg-white" />
        <div className="absolute top-[20%] left-0 right-0 h-[1px] bg-white" />
        <div className="absolute bottom-[20%] left-0 right-0 h-[1px] bg-white" />
      </div>

      <header className="px-8 py-10 lg:px-[10%] flex justify-between items-end relative z-10">
        <div className="flex flex-col">
          <span className="font-mono text-[10px] tracking-widest uppercase opacity-50 mb-2">RetroFit OS / v3.1</span>
          <h2 className="font-heading italic text-2xl tracking-wide">RetroFit.</h2>
        </div>
        <div className="font-mono text-xs uppercase tracking-widest border border-[#333333] px-4 py-2 hover:bg-white hover:text-black transition-colors cursor-pointer">
          Architecture
        </div>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row w-full px-8 lg:px-[10%] relative z-10 pb-20">
        
        {/* Typographic Core */}
        <div className="flex-1 flex flex-col justify-center pt-20 lg:pt-0 pb-16 lg:pb-0 lg:pr-16">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          >
            <h1 className="text-[13vw] lg:text-[7rem] xl:text-[8.5rem] font-medium tracking-tight leading-[0.85] mb-10 font-heading">
              Parametric <br className="hidden lg:block"/>
              <span className="italic text-[#D4FF26]">Optimization.</span>
            </h1>
            
            <p className="text-lg md:text-xl font-light text-[#777777] max-w-md font-body leading-relaxed mb-6">
              A high-density architecture aligning DOM structure directly to creative payload intent. Pure differential generation.
            </p>

            <div className="font-mono text-[10px] uppercase tracking-widest text-[#777777] flex flex-col gap-2 border-l border-[#333333] pl-4">
              <span>Status: <span className="text-white">Idle</span></span>
              <span>Agents: 6 Available</span>
            </div>
          </motion.div>
        </div>

        {/* Dense Structural Interface */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 1.2 }}
          className="lg:w-[450px] flex flex-col justify-center gap-8"
        >
          <form onSubmit={handleExecute} className="grid-panel p-8 md:p-12 w-full flex flex-col gap-10">
            
            <div>
              <label className="font-mono text-[10px] uppercase tracking-widest text-[#D4FF26] block mb-2 font-bold">
                [01] Target Architecture URL
              </label>
              <div className="structural-input-wrapper">
                <input 
                  type="url" 
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="brand.com/landing"
                  disabled={isExecuting}
                  className="structural-input"
                />
                <div className="structural-input-line" />
              </div>
            </div>

            <div>
              <label className="font-mono text-[10px] uppercase tracking-widest text-[#D4FF26] block mb-2 font-bold">
                [02] Source Payload (Creative)
              </label>
              
              <input 
                type="file" 
                className="hidden" 
                ref={fileInputRef} 
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setFile(e.target.files[0]);
                  }
                }}
              />

              {!file ? (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full border border-dashed border-[#333333] bg-[#111111] hover:bg-[#1a1a1a] transition-colors p-8 flex flex-col items-center justify-center cursor-pointer group"
                >
                  <Upload className="w-5 h-5 mb-4 opacity-40 group-hover:opacity-100 transition-opacity" />
                  <span className="font-body text-sm text-[#777777] group-hover:text-white transition-colors">Select Artifact</span>
                </div>
              ) : (
                <div className="w-full border border-[#D4FF26] bg-[#111111] p-6 flex items-center justify-between">
                  <div className="flex flex-col truncate">
                    <span className="font-mono text-xs text-[#D4FF26] truncate">{file.name}</span>
                    <span className="font-body text-[10px] text-[#777777] mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  <X 
                    className="w-4 h-4 cursor-pointer hover:text-red-500 opacity-60" 
                    onClick={() => setFile(null)} 
                  />
                </div>
              )}
            </div>

            {error && (
              <div className="font-mono text-[10px] text-red-500 bg-red-500/10 p-3 border border-red-500/30">
                ERR: {error}
              </div>
            )}

            <button 
              type="submit"
              disabled={isExecuting || !url}
              className="mt-6 bg-[#Aecf23] hover:bg-[#D4FF26] text-black px-8 py-5 rounded-full flex items-center justify-center gap-3 font-mono text-sm tracking-widest uppercase transition-all duration-300 disabled:opacity-50 disabled:hover:bg-[#Aecf23] w-full lg:w-max ml-auto shadow-[0_0_20px_rgba(212,255,38,0.15)]"
            >
              <span className="font-bold">{isExecuting ? "Initiating Process" : "Execute Run"}</span>
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </form>
        </motion.div>
      </div>

    </main>
  );
}
