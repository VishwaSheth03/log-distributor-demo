import { Table, TableHead, TableRow, TableCell, TableBody, Paper, Typography } from "@mui/material";
import useLogs from "../hooks/useLogs";

export default function LogTable() {
  const logs = useLogs();

  return (
    <Paper sx={{ maxHeight: 300, overflow: "auto", mt: 2 }}>
        <Typography variant="h6" sx={{ mt: 3 }}>
            Last 500 Logs
        </Typography>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell>Packet&nbsp;ID</TableCell>
            <TableCell>Emitter</TableCell>
            <TableCell>Analyzer</TableCell>
            <TableCell>Timestamp</TableCell>
            <TableCell>Message</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {logs.map((l, idx) => (
            <TableRow key={idx}>
              <TableCell>{l.packet.packetId}</TableCell>
              <TableCell>{l.packet.emitter}</TableCell>
              <TableCell>{l.analyzer}</TableCell>
              <TableCell sx={{ whiteSpace: "nowrap" }}>
                {l.packet.messages[0].ts.split("T")[1].slice(0, 12)}
              </TableCell>
              <TableCell>{l.packet.messages[0].message}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
}
