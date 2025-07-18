import {type Analyzer} from "../types";
import {Table, TableBody, TableCell, TableHead, TableRow, Switch, Typography} from "@mui/material";
import { enableAnalyzer, disableAnalyzer } from "../api";

export default function AnalyzerTable({ list }:{ list:Analyzer[] }) {
    const toggle = (a:Analyzer) => 
        a.admin_enabled ? disableAnalyzer(a.id) : enableAnalyzer(a.id);

    return (
        <>
            <Typography variant="h6">Analyzers</Typography>
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
                        <TableRow key={a.id}>
                            <TableCell>{a.id}</TableCell>
                            <TableCell>{a.healthy ? "✅" : "❌"}</TableCell>
                            <TableCell>{a.effective_weight.toFixed(2)}</TableCell>
                            <TableCell>{a.tx_packets}</TableCell>
                            <TableCell>
                                <Switch
                                    checked={a.admin_enabled}
                                    onChange={() => toggle(a)}
                                    size="small"
                                />
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </>
    );
}