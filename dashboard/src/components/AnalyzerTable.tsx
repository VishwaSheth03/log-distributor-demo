import { useState, useEffect } from "react";
import {type Analyzer} from "../types";
import {Table, TableBody, TableCell, TableHead, TableRow, Switch, Typography} from "@mui/material";
import { enableAnalyzer, disableAnalyzer } from "../api";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import { IconButton } from "@mui/material";
import { removeAnalyzer } from "../api";
import AddAnalyzerDialog from "./AddAnalyzerDialog";

function AnalyzerRow({ a }: { a: Analyzer }) {
    const [localHealthy, setLocalHealthy] = useState(a.healthy);
    const [localEnabled, setLocalEnabled] = useState(a.admin_enabled);
    const [localWeight, setLocalWeight] = useState(a.effective_weight);
    const [localTxPackets, setLocalTxPackets] = useState(a.tx_packets);

    useEffect(() => {
        setLocalHealthy(a.healthy);
        setLocalEnabled(a.admin_enabled);
        setLocalWeight(a.effective_weight);
        setLocalTxPackets(a.tx_packets);
    }, [a]);

    const toggleEnabled = () => {
        const next = !localEnabled;
        setLocalEnabled(next);
        if (next) {
            enableAnalyzer(a.id).catch(console.error);
        } else {
            disableAnalyzer(a.id).catch(console.error);
        }
    };

    return (
        <TableRow key={a.id}>
            <TableCell>{a.id}</TableCell>
            <TableCell>{localHealthy && localEnabled ? "✅" : "❌"}</TableCell>
            <TableCell>{localWeight.toFixed(2)}</TableCell>
            <TableCell>{localTxPackets}</TableCell>
            <TableCell>
                <Switch
                    checked={localEnabled}
                    onChange={toggleEnabled}
                    size="small"
                />
                <IconButton
                    onClick={() => {
                        removeAnalyzer(a.id).catch(console.error);
                    }}
                    size="small"
                    sx={{ ml: 1 }}
                >
                    <DeleteIcon fontSize="small" />
                </IconButton>
            </TableCell>
        </TableRow>
    );
}

export default function AnalyzerTable({ list }:{ list:Analyzer[] }) {
    const [open, setOpen] = useState(false);

    return (
        <>
            <Typography variant="h6" display="flex" alignItems="center">
                Analyzers
                <IconButton onClick={() => setOpen(true)} size="small" sx={{ ml: 1 }}>
                    <AddIcon />
                </IconButton>
            </Typography>
            <AddAnalyzerDialog open={open} onClose={() => setOpen(false)} />
            <Table size="small">
                <TableHead>
                    <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>Healthy</TableCell>
                        <TableCell>Weight</TableCell>
                        <TableCell>Packets Transmitted</TableCell>
                        <TableCell>Enabled</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {list.map((a) => (
                        <AnalyzerRow key={a.id} a={a} />
                    ))}
                </TableBody>
            </Table>
        </>
    );
}