import React, { useEffect, useRef, useState } from 'react';
import uPlot from 'uplot';
import Plot from 'react-plotly.js';
import { Activity, Thermometer, Droplets, Users, ShieldAlert, Zap, RefreshCw, AlertCircle } from 'lucide-react';

const WEBSOCKET_URL = "ws://localhost:8000/ws/client";

function App() {
  const [status, setStatus] = useState("Connecting");
  const [occupancy, setOccupancy] = useState("Empty");
  const [bpm, setBpm] = useState("--.-");
  const [temp, setTemp] = useState("--.-");
  const [humidity, setHumidity] = useState("--.-");
  const [sqs, setSqs] = useState("--.-");
  const [prediction, setPrediction] = useState("Waiting for Data");
  const [confidence, setConfidence] = useState(0.0);
  const [samplingRate, setSamplingRate] = useState(100.0);
  const [bestChannel, setBestChannel] = useState("AZ");
  const [stabilityFlag, setStabilityFlag] = useState("Initializing...");
  
  // FFT state
  const [fftData, setFftData] = useState({ freqs: [], mags: [], mag_mags: [] });
  
  const wsRef = useRef(null);
  const rawChartRef = useRef(null);
  const filtChartRef = useRef(null);
  const rawUPlotInstance = useRef(null);
  const filtUPlotInstance = useRef(null);

  // Initialize WebSockets
  useEffect(() => {
    connectWS();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (rawUPlotInstance.current) rawUPlotInstance.current.destroy();
      if (filtUPlotInstance.current) filtUPlotInstance.current.destroy();
    };
  }, []);

  const connectWS = () => {
    setStatus("Connecting");
    const ws = new WebSocket(WEBSOCKET_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("Connected");
      console.log("WebSocket connected.");
    };

    ws.onclose = () => {
      setStatus("Disconnected");
      console.log("WebSocket disconnected. Reconnecting in 3s...");
      setTimeout(connectWS, 3000);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "processed") {
          updateDashboard(payload);
        }
      } catch (err) {
        console.error("Error reading WebSocket payload:", err);
      }
    };
  };

  const updateDashboard = (data) => {
    const isOccupied = data.occupancy === 1;
    setOccupancy(isOccupied ? "Present" : "Empty");
    setTemp(data.temp !== null && data.temp !== undefined ? `${data.temp.toFixed(1)} °C` : "--.- °C");
    setHumidity(data.humidity !== null && data.humidity !== undefined ? `${data.humidity.toFixed(1)} %` : "--.- %");

    if (isOccupied) {
      setBpm(data.bpm > 0 ? data.bpm.toFixed(1) : "CALCULATING");
      setSqs(data.sqs.toFixed(2));
      setPrediction(data.rhythm_prediction);
      setConfidence(data.rhythm_confidence);
      setSamplingRate(data.sampling_rate);
      setBestChannel(data.best_channel);
      setStabilityFlag(data.stability_flag);

      // Update FFT state
      setFftData({
        freqs: data.fft_freqs,
        mags: data.fft_mags,
        mag_mags: data.fft_mag_mags
      });

      // Update uPlot Raw Data
      const rawTimes = data.time_w;
      const axRaw = data.ax_dt;
      const ayRaw = data.ay_dt;
      const azRaw = data.az_dt;
      
      if (rawUPlotInstance.current) {
        rawUPlotInstance.current.setData([rawTimes, axRaw, ayRaw, azRaw]);
      } else if (rawChartRef.current && rawTimes.length > 0) {
        initRawChart(rawTimes, axRaw, ayRaw, azRaw);
      }

      // Update uPlot Filtered Data
      const axFilt = data.ax_f;
      const ayFilt = data.ay_f;
      const azFilt = data.az_f;
      const magFilt = data.mag_f;

      if (filtUPlotInstance.current) {
        filtUPlotInstance.current.setData([rawTimes, axFilt, ayFilt, azFilt, magFilt]);
      } else if (filtChartRef.current && rawTimes.length > 0) {
        initFiltChart(rawTimes, axFilt, ayFilt, azFilt, magFilt);
      }
    } else {
      // Clear charts if unoccupied
      if (rawUPlotInstance.current) {
        rawUPlotInstance.current.destroy();
        rawUPlotInstance.current = null;
      }
      if (filtUPlotInstance.current) {
        filtUPlotInstance.current.destroy();
        filtUPlotInstance.current = null;
      }
    }
  };

  const initRawChart = (t, x, y, z) => {
    if (!rawChartRef.current) return;
    const opts = {
      title: "Raw Accelerometer Channels (Detrended)",
      width: rawChartRef.current.clientWidth,
      height: 200,
      scales: { x: { time: false } },
      series: [
        {},
        { stroke: "#e67e22", label: "Raw AX", width: 1.5 },
        { stroke: "#27ae60", label: "Raw AY", width: 1.5 },
        { stroke: "#2980b9", label: "Raw AZ", width: 1.5 }
      ],
      axes: [
        { stroke: "#7f8c8d" },
        { stroke: "#7f8c8d" }
      ],
      grid: {
        stroke: "rgba(255, 255, 255, 0.05)"
      }
    };
    rawUPlotInstance.current = new uPlot(opts, [t, x, y, z], rawChartRef.current);
  };

  const initFiltChart = (t, x, y, z, m) => {
    if (!filtChartRef.current) return;
    const opts = {
      title: "Filtered Channels & Magnitude",
      width: filtChartRef.current.clientWidth,
      height: 200,
      scales: { x: { time: false } },
      series: [
        {},
        { stroke: "#e67e22", label: "Filtered AX", width: 0.8 },
        { stroke: "#27ae60", label: "Filtered AY", width: 0.8 },
        { stroke: "#2980b9", label: "Filtered AZ", width: 0.8 },
        { stroke: "#e74c3c", label: "Magnitude", width: 2.0 }
      ],
      axes: [
        { stroke: "#7f8c8d" },
        { stroke: "#7f8c8d" }
      ],
      grid: {
        stroke: "rgba(255, 255, 255, 0.05)"
      }
    };
    filtUPlotInstance.current = new uPlot(opts, [t, x, y, z, m], filtChartRef.current);
  };

  // Re-size uPlots when container expands
  useEffect(() => {
    const handleResize = () => {
      if (rawUPlotInstance.current && rawChartRef.current) {
        rawUPlotInstance.current.setSize({
          width: rawChartRef.current.clientWidth,
          height: 200
        });
      }
      if (filtUPlotInstance.current && filtChartRef.current) {
        filtUPlotInstance.current.setSize({
          width: filtChartRef.current.clientWidth,
          height: 200
        });
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const sendCommand = (cmd) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(cmd);
      console.log("Sent command to backend:", cmd);
    } else {
      alert("WebSocket connection is not active.");
    }
  };

  const rhythmStyles = {
    "Normal": { bg: "bg-emerald-950/60 border-emerald-500", text: "text-emerald-400" },
    "Bradycardia": { bg: "bg-rose-950/60 border-rose-600 animate-pulse", text: "text-rose-400" },
    "Tachycardia": { bg: "bg-rose-950/60 border-rose-600 animate-pulse", text: "text-rose-400" },
    "Waiting for Data": { bg: "bg-slate-800/40 border-slate-700", text: "text-slate-400" }
  };
  const currentRhythmStyle = rhythmStyles[prediction] || rhythmStyles["Waiting for Data"];

  return (
    <div className="min-h-screen bg-[#0d1117] text-white p-6 flex flex-col justify-between">
      
      {/* Top Header */}
      <header className="flex flex-wrap items-center justify-between border-b border-[#2c3e50] pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            BCG Live Cloud Healthcare-Monitoring Console
          </h1>
          <p className="text-slate-400 text-sm">Real-time contactless Ballistocardiography processing & AI rhythm logging</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
            status === "Connected" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20 animate-pulse"
          }`}>
            <span className={`w-2 h-2 mr-2 rounded-full ${status === "Connected" ? "bg-emerald-400" : "bg-rose-400 animate-ping"}`} />
            {status}
          </span>
        </div>
      </header>

      {/* Info Cards Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        
        {/* Occupancy Card */}
        <div className="bg-[#161a22] border border-[#2c3e50] rounded-xl p-4 flex items-center justify-between hover:border-slate-600 transition-all duration-300">
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Occupancy Status</p>
            <h3 className={`text-xl font-bold mt-1 ${occupancy === "Present" ? "text-emerald-400" : "text-amber-500"}`}>
              {occupancy.toUpperCase()}
            </h3>
          </div>
          <div className={`p-3 rounded-lg ${occupancy === "Present" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
            <Users className="w-5 h-5" />
          </div>
        </div>

        {/* Temperature Card */}
        <div className="bg-[#161a22] border border-[#2c3e50] rounded-xl p-4 flex items-center justify-between hover:border-slate-600 transition-all duration-300">
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Temperature</p>
            <h3 className="text-xl font-bold mt-1 text-orange-400">
              {temp}
            </h3>
          </div>
          <div className="p-3 rounded-lg bg-orange-500/10 text-orange-400">
            <Thermometer className="w-5 h-5" />
          </div>
        </div>

        {/* Humidity Card */}
        <div className="bg-[#161a22] border border-[#2c3e50] rounded-xl p-4 flex items-center justify-between hover:border-slate-600 transition-all duration-300">
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Humidity</p>
            <h3 className="text-xl font-bold mt-1 text-blue-400">
              {humidity}
            </h3>
          </div>
          <div className="p-3 rounded-lg bg-blue-500/10 text-blue-400">
            <Droplets className="w-5 h-5" />
          </div>
        </div>

        {/* Conditional Cards for Active Occupant */}
        {occupancy === "Present" ? (
          <>
            {/* BPM Card */}
            <div className="bg-[#161a22] border border-[#2c3e50] rounded-xl p-4 flex items-center justify-between hover:border-slate-600 transition-all duration-300">
              <div>
                <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Heart Rate (BPM)</p>
                <h3 className="text-2xl font-black mt-1 text-rose-500 tracking-tight">
                  {bpm}
                </h3>
              </div>
              <div className="p-3 rounded-lg bg-rose-500/10 text-rose-500">
                <Activity className="w-5 h-5 animate-pulse" />
              </div>
            </div>

            {/* AI Rhythm Prediction Card */}
            <div className={`col-span-1 md:col-span-2 border rounded-xl p-4 flex items-center justify-between hover:scale-[1.01] transition-all duration-300 ${currentRhythmStyle.bg}`}>
              <div>
                <p className="text-slate-300 text-xs font-medium uppercase tracking-wider">AI Rhythm Prediction</p>
                <h3 className={`text-2xl font-black mt-1 uppercase ${currentRhythmStyle.text}`}>
                  {prediction}
                </h3>
              </div>
              <div className="text-right">
                <p className="text-slate-400 text-xs uppercase">Confidence</p>
                <h4 className="text-xl font-bold text-slate-200 mt-1">{confidence.toFixed(1)}%</h4>
              </div>
            </div>

            {/* Signal Quality SQS */}
            <div className="bg-[#161a22] border border-[#2c3e50] rounded-xl p-4 flex items-center justify-between hover:border-slate-600 transition-all duration-300">
              <div>
                <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Signal Quality (SQS)</p>
                <h3 className="text-xl font-bold mt-1 text-purple-400">
                  {sqs}
                </h3>
              </div>
              <div className="p-3 rounded-lg bg-purple-500/10 text-purple-400">
                <Zap className="w-5 h-5" />
              </div>
            </div>

            {/* Confidence score */}
            <div className="bg-[#161a22] border border-[#2c3e50] rounded-xl p-4 flex items-center justify-between hover:border-slate-600 transition-all duration-300">
              <div>
                <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Confidence Score</p>
                <h3 className="text-xl font-bold mt-1 text-yellow-400">
                  {confidence.toFixed(1)} %
                </h3>
              </div>
              <div className="p-3 rounded-lg bg-yellow-500/10 text-yellow-400">
                <RefreshCw className="w-5 h-5" />
              </div>
            </div>
          </>
        ) : null}

      </section>

      {/* Main Content Layout */}
      <main className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
        
        {/* Left Side: Real-time Rolling Graphs */}
        <div className="col-span-1 lg:col-span-3 space-y-6">
          {occupancy === "Present" ? (
            <>
              <div className="bg-[#161a22] border border-[#2c3e50] p-4 rounded-xl">
                <div ref={rawChartRef} className="w-full h-full" />
              </div>
              
              <div className="bg-[#161a22] border border-[#2c3e50] p-4 rounded-xl">
                <div ref={filtChartRef} className="w-full h-full" />
              </div>
              
              {/* FFT Spectrum Plot */}
              <div className="bg-[#161a22] border border-[#2c3e50] p-4 rounded-xl">
                <Plot
                  data={[
                    {
                      x: fftData.freqs,
                      y: fftData.mags,
                      type: 'scatter',
                      mode: 'lines',
                      marker: { color: '#8e44ad' },
                      name: 'Best Axis FFT'
                    },
                    {
                      x: fftData.freqs,
                      y: fftData.mag_mags,
                      type: 'scatter',
                      mode: 'lines',
                      marker: { color: '#e74c3c' },
                      name: 'Magnitude FFT'
                    }
                  ]}
                  layout={{
                    title: { text: 'FFT Frequency Spectrum', font: { color: '#2ecc71', size: 14 } },
                    paper_bgcolor: '#161a22',
                    plot_bgcolor: '#161a22',
                    xaxis: { title: { text: 'Frequency (Hz)', font: { color: '#a0aec0' } }, color: '#a0aec0', range: [0, 5] },
                    yaxis: { title: { text: 'Magnitude', font: { color: '#a0aec0' } }, color: '#a0aec0' },
                    margin: { l: 40, r: 20, t: 40, b: 40 },
                    legend: { font: { color: '#a0aec0' } },
                    shapes: [
                      {
                        type: 'rect',
                        xref: 'x',
                        yref: 'paper',
                        x0: 0.8,
                        x1: 3.0,
                        y0: 0,
                        y1: 1,
                        fillcolor: 'rgba(46, 204, 113, 0.15)',
                        line: { width: 0 }
                      }
                    ]
                  }}
                  useResizeHandler={true}
                  className="w-full h-[220px]"
                />
              </div>
            </>
          ) : (
            <div className="bg-[#161a22] border border-dashed border-[#2c3e50] p-12 rounded-xl flex flex-col items-center justify-center h-[500px] text-slate-400">
              <Activity className="w-12 h-12 mb-4 text-amber-500/60 animate-pulse" />
              <h3 className="text-lg font-bold text-slate-200">BCG Telemetry Waveform Paused</h3>
              <p className="text-sm text-slate-500 mt-1">Please sit on the chair to start heart rate telemetry capture.</p>
            </div>
          )}
        </div>

        {/* Right Side: Diagnostics & Alerts Info Panel */}
        <div className="col-span-1 bg-[#161a22] border border-[#2c3e50] rounded-xl p-5 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-md font-bold text-[#e67e22] uppercase tracking-wide border-b border-[#2c3e50] pb-2">
              System Diagnostics
            </h3>
            
            <div className="diagnostic-panel text-xs space-y-2 text-slate-300">
              <div className="flex justify-between">
                <span>Occupancy Status:</span>
                <span className={occupancy === "Present" ? "text-emerald-400 font-bold" : "text-amber-500 font-bold"}>
                  {occupancy}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Heart Monitoring:</span>
                <span className={occupancy === "Present" ? "text-emerald-400" : "text-slate-500"}>
                  {occupancy === "Present" ? "Active" : "Paused"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Sampling rate:</span>
                <span className="text-white">{samplingRate.toFixed(1)} Hz</span>
              </div>
              {occupancy === "Present" && (
                <>
                  <div className="flex justify-between">
                    <span>Best Axis Signal:</span>
                    <span className="text-purple-400 font-bold">{bestChannel.toUpperCase()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Stability Flag:</span>
                    <span className="text-white">{stabilityFlag}</span>
                  </div>
                </>
              )}
            </div>

            <div className="border-t border-[#2c3e50] pt-4 mt-4">
              <h4 className="text-xs font-semibold text-rose-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                Active Alerts
              </h4>
              <div className="space-y-2">
                {occupancy === "Empty" ? (
                  <div className="text-xs bg-amber-500/10 text-amber-400 p-2 rounded border border-amber-500/20">
                    ⚠️ Monitoring Paused (No Occupant)
                  </div>
                ) : (
                  <>
                    {prediction === "Bradycardia" && (
                      <div className="text-xs bg-rose-500/10 text-rose-400 p-2 rounded border border-rose-500/20 animate-pulse">
                        🚨 ALERT: Bradycardia Detected!
                      </div>
                    )}
                    {prediction === "Tachycardia" && (
                      <div className="text-xs bg-rose-500/10 text-rose-400 p-2 rounded border border-rose-500/20 animate-pulse">
                        🚨 ALERT: Tachycardia Detected!
                      </div>
                    )}
                    {prediction === "Normal" && (
                      <div className="text-xs text-emerald-400 p-1 italic">
                        All physiological markers stable.
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Action Simulation Controls */}
          {occupancy === "Present" && (
            <div className="border-t border-[#2c3e50] pt-4 mt-6 space-y-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Inject Simulation Overrides
              </h4>
              <button
                onClick={() => sendCommand("N")}
                className="w-full py-2 px-3 text-xs bg-emerald-600 hover:bg-emerald-500 rounded font-semibold transition duration-200"
              >
                Resume Live Data
              </button>
              <button
                onClick={() => sendCommand("B")}
                className="w-full py-2 px-3 text-xs bg-rose-700 hover:bg-rose-600 rounded font-semibold transition duration-200"
              >
                Simulate Bradycardia (42 BPM)
              </button>
              <button
                onClick={() => sendCommand("T")}
                className="w-full py-2 px-3 text-xs bg-orange-600 hover:bg-orange-500 rounded font-semibold transition duration-200"
              >
                Simulate Tachycardia (145 BPM)
              </button>
            </div>
          )}

        </div>

      </main>

      <footer className="text-center text-slate-500 text-xs border-t border-[#2c3e50] pt-4 mt-2">
        &copy; {new Date().getFullYear()} Antigravity AI BCG Project. Connected to FastAPI Cloud Gateway.
      </footer>

    </div>
  );
}

export default App;
