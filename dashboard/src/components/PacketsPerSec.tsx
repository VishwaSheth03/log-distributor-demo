import { useEffect, useRef, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import useMetrics from "../hooks/useMetrics";

export default function PacketsPerSec() {
  const metrics = useMetrics();
  const prev = useRef<number|null>(null);
  const [series, setSeries] = useState<{ts:number, pps:number}[]>([]);

  useEffect(()=>{
    if (!metrics) return;
    if (prev.current !== null){
      const delta = metrics.packets_rx - prev.current;
      setSeries((s)=>[...s.slice(-29), { ts: metrics.ts, pps: delta }]);
    }
    prev.current = metrics.packets_rx;
  }, [metrics]);

  return (
    <>
      <h4>Packets / sec (last 30 s)</h4>
      <LineChart width={480} height={200} data={series}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="ts" hide />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Line type="monotone" dataKey="pps" dot={false} />
      </LineChart>
    </>
  );
}
