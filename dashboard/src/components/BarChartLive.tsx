import {BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid} from "recharts";

interface Props {
    series: {name: string; value: number}[];
    title: string;
}

export default function BarChartLive({series, title}: Props) {
    return (
        <>
            <h4>{title}</h4>
            <BarChart width={480} height={200} data={series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" />
            </BarChart>
        </>
    )
}