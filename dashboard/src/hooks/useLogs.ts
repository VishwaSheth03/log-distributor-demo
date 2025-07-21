import { useEffect, useState } from "react";
import { type LogEntry } from "../types";

export default function useLogs(max = 500) {
    const [logs, setLogs] = useState<LogEntry[]>([]);

    useEffect(() => {
        const ws = new WebSocket(`ws://${location.host}/ws/logs`);
        ws.onmessage = (e) => {
            const entry = JSON.parse(e.data) as LogEntry;
            setLogs((prev) => [...prev.slice(-max + 1), entry]);
        };
        return () => ws.close();
    }, [max]);

    return logs;
}