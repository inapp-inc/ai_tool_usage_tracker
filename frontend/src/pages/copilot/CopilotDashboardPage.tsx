import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { fetchCopilotInsights, fetchCopilotOverview, fetchCopilotUsers } from "@/api/copilot";
import { fetchTeams, type Team } from "@/api/teams";

type DateRange = { from: string; to: string };

function createDefaultPeriod(): DateRange {
  const to = new Date();
  const from = new Date(to);
  from.setDate(from.getDate() - 30);
  return { from: from.toISOString(), to: to.toISOString() };
}

const PIE_COLORS = ["#2563eb", "#94a3b8", "#e2e8f0"];

function MetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h5" sx={{ mt: 0.5, fontWeight: 600 }}>
          {value}
        </Typography>
        {sub ? (
          <Typography variant="caption" color="text.secondary">
            {sub}
          </Typography>
        ) : null}
      </CardContent>
    </Card>
  );
}

export function CopilotDashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [period] = useState<DateRange>(() => createDefaultPeriod());

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const teams = teamsQuery.data ?? [];
  const teamId = searchParams.get("team_id") ?? teams[0]?.id ?? "";

  const overviewQuery = useQuery({
    queryKey: ["copilot", "overview", teamId, period.from, period.to],
    queryFn: () => fetchCopilotOverview(teamId, period.from, period.to),
    enabled: Boolean(teamId),
  });

  const usersQuery = useQuery({
    queryKey: ["copilot", "users", teamId, period.from, period.to],
    queryFn: () => fetchCopilotUsers(teamId, period.from, period.to),
    enabled: Boolean(teamId),
  });

  const insightsQuery = useQuery({
    queryKey: ["copilot", "insights", teamId, period.from, period.to],
    queryFn: () => fetchCopilotInsights(teamId, period.from, period.to),
    enabled: Boolean(teamId),
  });

  const loading = overviewQuery.isPending || teamsQuery.isPending;
  const overview = overviewQuery.data;
  const topUsers = useMemo(
    () => (usersQuery.data?.users ?? []).slice(0, 10),
    [usersQuery.data],
  );

  const onTeamChange = (nextTeamId: string) => {
    setSearchParams({ team_id: nextTeamId });
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            GitHub Copilot Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Seat utilization and productivity metrics — not token usage.
          </Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel id="copilot-team-label">Team</InputLabel>
          <Select
            labelId="copilot-team-label"
            label="Team"
            value={teamId}
            onChange={(event) => onTeamChange(event.target.value)}
          >
            {teams.map((team: Team) => (
              <MenuItem key={team.id} value={team.id}>
                {team.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      ) : overviewQuery.isError ? (
        <Alert severity="error">Unable to load Copilot analytics. Sync Copilot credentials first.</Alert>
      ) : overview ? (
        <>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard label="Total seats" value={String(overview.total_seats)} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard label="Assigned seats" value={String(overview.assigned_seats)} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard label="Active users" value={String(overview.active_users)} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard label="Inactive users" value={String(overview.inactive_users)} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                label="Monthly cost"
                value={`$${Number(overview.monthly_cost).toFixed(0)}`}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                label="Seat utilization"
                value={`${overview.seat_utilization_pct}%`}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                label="Avg acceptance rate"
                value={
                  overview.average_acceptance_rate != null
                    ? `${overview.average_acceptance_rate}%`
                    : "—"
                }
              />
            </Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Seat utilization
                  </Typography>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={overview.seat_utilization} dataKey="value" nameKey="label" outerRadius={80}>
                        {overview.seat_utilization.map((_, index) => (
                          <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Active users trend
                  </Typography>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={overview.active_users_trend}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" hide />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Suggestions vs acceptances
                  </Typography>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={overview.suggestions_vs_acceptances}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#2563eb" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Top languages
                  </Typography>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={overview.top_languages}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#0ea5e9" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    IDE distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={overview.ide_distribution} dataKey="value" nameKey="label" outerRadius={80}>
                        {overview.ide_distribution.map((_, index) => (
                          <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {insightsQuery.data?.insights?.length ? (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Typography variant="h6" fontWeight={600}>
                Insights
              </Typography>
              {insightsQuery.data.insights.map((insight) => (
                <Alert key={insight.kind} severity={insight.severity === "warning" ? "warning" : "info"}>
                  <strong>{insight.title}:</strong> {insight.message}
                </Alert>
              ))}
            </Box>
          ) : null}

          {topUsers.length ? (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  Top users by suggestions
                </Typography>
                {topUsers.map((user) => (
                  <Box
                    key={user.user_login}
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      py: 1,
                      borderBottom: "1px solid",
                      borderColor: "divider",
                    }}
                  >
                    <Typography>{user.user_login}</Typography>
                    <Typography color="text.secondary">
                      {user.suggestions_count} suggestions · {user.acceptances_count} accepted
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          ) : null}
        </>
      ) : null}
    </Box>
  );
}
