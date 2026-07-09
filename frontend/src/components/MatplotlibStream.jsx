import React from 'react'

export default function MatplotlibStream() {
  // Use the FastAPI endpoint for the MJPEG stream
  const streamUrl = 'http://localhost:8001/api/live/matplotlib-stream'

  return (
    <div className="w-full h-[80vh] min-h-[600px] flex justify-center items-center bg-[#161a22] rounded-2xl overflow-auto border border-brand-900/10 shadow-sm relative">
      <img 
        src={streamUrl} 
        alt="Matplotlib Live Stream"
        className="max-w-none max-h-none"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain' // Maintains aspect ratio
        }}
        onError={(e) => {
          e.target.style.display = 'none';
          e.target.nextSibling.style.display = 'flex';
        }}
      />
      <div className="hidden absolute inset-0 flex-col items-center justify-center text-white/50">
        <p className="text-xl font-bold mb-2">Stream Offline</p>
        <p className="text-sm">Is bcg_live.py running?</p>
      </div>
    </div>
  )
}
