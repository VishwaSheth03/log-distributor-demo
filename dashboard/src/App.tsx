import { Container, Grid, Typography } from "@mui/material";
import useMetrics from "./hooks/useMetrics";
import AnalyzerTable from "./components/AnalyzerTable";
import EmitterTable from "./components/EmitterTable";
import PacketsPerSec from "./components/PacketsPerSec";
import BarChartLive from "./components/BarChartLive";

function App() {
    const metrics = useMetrics();

    if (!metrics) return <p>Waiting for data...</p>;

    const analyzerSeries = metrics.analyzers.map((a) => ({
        name: a.id,
        value: a.tx_packets,
    }));

    const queueSeries = [
        { name: "queue", value: metrics.queue_depth },
        { name: "received", value: metrics.packets_rx },
    ];

    return (
        <Container sx={{ mt: 4 }}>
            <Typography variant="h4" gutterBottom>
                Log Distributor Dashboard
            </Typography>
            <Grid container spacing={4}>
                <Grid>
                    <BarChartLive title="Analyzer packet counts"  series={analyzerSeries} />
                </Grid>
                <Grid>
                    <BarChartLive title="Distributor load"  series={queueSeries} />
                </Grid>
                <Grid>
                    <PacketsPerSec />
                </Grid>
                <Grid>
                    <EmitterTable list={metrics.emitters} />
                    <AnalyzerTable list={metrics.analyzers} />
                </Grid>
            </Grid>
        </Container>
    );
}

export default App;