import {useEffect, useState} from "react";
import { type MetricsPayload } from "../types";

export default function useMetrics() {
    const [data, setData] = useState<MetricsPayload | null>(null);

    useEffect(() => {
        const ws = new WebSocket(`ws://${location.host}/ws/metrics`);
        ws.onmessage = (evt) => {
            const payload = JSON.parse(evt.data) as MetricsPayload;
            setData(payload);
        };
        return () => ws.close();
    }, []);

    return data;
}