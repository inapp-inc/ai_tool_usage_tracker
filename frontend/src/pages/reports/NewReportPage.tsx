import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconArrowLeft,
  IconFileText,
  IconFileTypePdf,
  IconTable,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  FormControl,
  FormHelperText,
  InputLabel,
  ListItemText,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery } from "@tanstack/react-query";
import { format, isSameYear, parseISO } from "date-fns";
import { useMemo, type ReactNode } from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { createReport, type ReportFormat, type ReportSchedule, type ReportType } from "@/api/reports";
import { fetchTeams, type Team } from "@/api/teams";
import { tokens } from "@/theme/palette";

const EMPTY_TEAMS: Team[] = [];

const schema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  type: z.enum([
    "usage_summary",
    "cost_breakdown",
    "team_comparison",
    "user_activity",
    "budget_variance",
  ]),
  format: z.enum(["pdf", "csv", "xlsx"]),
  schedule: z.enum(["once", "daily", "weekly", "monthly"]),
  periodFrom: z.string().min(1, "Start date required"),
  periodTo: z.string().min(1, "End date required"),
  teamIds: z.array(z.string()),
});

type FormValues = z.infer<typeof schema>;

const REPORT_TYPE_OPTIONS: Array<{ value: ReportType; label: string }> = [
  { value: "usage_summary", label: "Usage Summary" },
  { value: "cost_breakdown", label: "Cost Breakdown" },
  { value: "team_comparison", label: "Team Comparison" },
  { value: "user_activity", label: "User Activity" },
  { value: "budget_variance", label: "Budget Variance" },
];

const FORMAT_OPTIONS: Array<{ value: ReportFormat; label: string }> = [
  { value: "pdf", label: "PDF" },
  { value: "csv", label: "CSV" },
  { value: "xlsx", label: "Excel" },
];

const SCHEDULE_OPTIONS: Array<{ value: ReportSchedule; label: string }> = [
  { value: "once", label: "Once" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

function formatReportType(type: ReportType | undefined): string {
  if (!type) {
    return "—";
  }
  return REPORT_TYPE_OPTIONS.find((option) => option.value === type)?.label ?? "—";
}

function formatPeriodPreview(from: string, to: string): string {
  if (!from || !to) {
    return "—";
  }

  const fromDate = parseISO(`${from}T00:00:00`);
  const toDate = parseISO(`${to}T00:00:00`);

  if (isSameYear(fromDate, toDate)) {
    return `${format(fromDate, "MMM d")} – ${format(toDate, "MMM d, yyyy")}`;
  }

  return `${format(fromDate, "MMM d, yyyy")} – ${format(toDate, "MMM d, yyyy")}`;
}

function FormatPreviewIcon({ format }: { format: ReportFormat | undefined }) {
  if (format === "pdf") {
    return <IconFileTypePdf size={16} color="#DC2626" />;
  }
  if (format === "csv") {
    return <IconFileText size={16} color="#16A34A" />;
  }
  if (format === "xlsx") {
    return <IconTable size={16} color="#2563EB" />;
  }
  return null;
}

function PreviewRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
      <Typography
        variant="caption"
        sx={{ color: tokens.textMuted, width: 100, flexShrink: 0 }}
      >
        {label}
      </Typography>
      <Box sx={{ flex: 1 }}>{value}</Box>
    </Box>
  );
}

export function NewReportPage() {
  const navigate = useNavigate();

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const createMutation = useMutation({
    mutationFn: createReport,
    onSuccess: () => {
      navigate("/reports");
    },
  });

  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      type: "usage_summary",
      format: "pdf",
      schedule: "once",
      periodFrom: "",
      periodTo: "",
      teamIds: [],
    },
  });

  const watched = watch();
  const teams = teamsQuery.data ?? EMPTY_TEAMS;

  const selectedTeamNames = useMemo(
    () =>
      teams
        .filter((team) => watched.teamIds.includes(team.id))
        .map((team) => team.name),
    [teams, watched.teamIds],
  );

  const teamsPreview = useMemo(() => {
    if (selectedTeamNames.length === 0) {
      return "All teams";
    }
    if (selectedTeamNames.length <= 3) {
      return selectedTeamNames.join(", ");
    }
    return `${selectedTeamNames.slice(0, 3).join(", ")} +${selectedTeamNames.length - 3} more`;
  }, [selectedTeamNames]);

  const scheduleInfo = useMemo(() => {
    if (watched.schedule === "once") {
      return "This report will be generated once and available for download.";
    }
    if (watched.schedule === "daily") {
      return "This report will run daily and appear in your reports list automatically.";
    }
    if (watched.schedule === "weekly") {
      return "This report will run weekly and appear in your reports list automatically.";
    }
    return "This report will run monthly and appear in your reports list automatically.";
  }, [watched.schedule]);

  const onSubmit = (data: FormValues) => {
    createMutation.mutate({
      name: data.name,
      type: data.type,
      format: data.format,
      schedule: data.schedule,
      periodFrom: new Date(`${data.periodFrom}T00:00:00`).toISOString(),
      periodTo: new Date(`${data.periodTo}T23:59:59`).toISOString(),
      teamIds: data.teamIds,
    });
  };

  return (
    <Box>
      <Button
        variant="text"
        size="small"
        startIcon={<IconArrowLeft size={14} />}
        onClick={() => navigate("/reports")}
        sx={{ mb: 1, ml: -0.5 }}
      >
        Back to Reports
      </Button>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          New Report
        </Typography>
        <Typography variant="body2" sx={{ color: tokens.textMuted }}>
          Configure and generate a usage export
        </Typography>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "3fr 2fr",
          gap: "20px",
        }}
      >
        <Card>
          <CardContent sx={{ p: "24px", "&:last-child": { pb: "24px" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
              Report Configuration
            </Typography>

            <Box component="form" onSubmit={handleSubmit(onSubmit)}>
              <TextField
                {...register("name")}
                fullWidth
                size="small"
                label="Report name"
                error={Boolean(errors.name)}
                helperText={errors.name?.message}
                sx={{ mb: 2 }}
              />

              <Controller
                name="type"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                    <InputLabel id="report-type-label">Report type</InputLabel>
                    <Select
                      {...field}
                      labelId="report-type-label"
                      label="Report type"
                    >
                      {REPORT_TYPE_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />

              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 2,
                  mb: 2,
                }}
              >
                <Controller
                  name="format"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth size="small">
                      <InputLabel id="report-format-label">Format</InputLabel>
                      <Select
                        {...field}
                        labelId="report-format-label"
                        label="Format"
                      >
                        {FORMAT_OPTIONS.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                />

                <Controller
                  name="schedule"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth size="small">
                      <InputLabel id="report-schedule-label">Schedule</InputLabel>
                      <Select
                        {...field}
                        labelId="report-schedule-label"
                        label="Schedule"
                      >
                        {SCHEDULE_OPTIONS.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                />
              </Box>

              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 2,
                  mb: 2,
                }}
              >
                <TextField
                  {...register("periodFrom")}
                  fullWidth
                  size="small"
                  type="date"
                  label="From"
                  slotProps={{ inputLabel: { shrink: true } }}
                  error={Boolean(errors.periodFrom)}
                  helperText={errors.periodFrom?.message}
                />
                <TextField
                  {...register("periodTo")}
                  fullWidth
                  size="small"
                  type="date"
                  label="To"
                  slotProps={{ inputLabel: { shrink: true } }}
                  error={Boolean(errors.periodTo)}
                  helperText={errors.periodTo?.message}
                />
              </Box>

              <Controller
                name="teamIds"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                    <InputLabel id="report-teams-label">Teams</InputLabel>
                    <Select
                      {...field}
                      multiple
                      labelId="report-teams-label"
                      label="Teams"
                      renderValue={(selected) =>
                        teams
                          .filter((team) => selected.includes(team.id))
                          .map((team) => team.name)
                          .join(", ") || "All teams"
                      }
                    >
                      {teams.map((team) => (
                        <MenuItem key={team.id} value={team.id}>
                          <Checkbox checked={field.value.includes(team.id)} />
                          <ListItemText primary={team.name} />
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>Leave empty to include all teams</FormHelperText>
                  </FormControl>
                )}
              />

              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="medium"
                disabled={createMutation.isPending}
                sx={{ mt: 2 }}
                startIcon={
                  createMutation.isPending ? (
                    <CircularProgress size={14} color="inherit" />
                  ) : undefined
                }
              >
                Generate Report
              </Button>
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent sx={{ p: "24px", "&:last-child": { pb: "24px" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
              Report Preview
            </Typography>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
              <PreviewRow
                label="Type"
                value={
                  <Typography variant="body2">
                    {formatReportType(watched.type)}
                  </Typography>
                }
              />
              <PreviewRow
                label="Format"
                value={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <FormatPreviewIcon format={watched.format} />
                    <Typography variant="body2">
                      {FORMAT_OPTIONS.find((option) => option.value === watched.format)
                        ?.label ?? "—"}
                    </Typography>
                  </Box>
                }
              />
              <PreviewRow
                label="Period"
                value={
                  <Typography variant="body2">
                    {formatPeriodPreview(watched.periodFrom, watched.periodTo)}
                  </Typography>
                }
              />
              <PreviewRow
                label="Schedule"
                value={
                  <Typography variant="body2">
                    {SCHEDULE_OPTIONS.find((option) => option.value === watched.schedule)
                      ?.label ?? "—"}
                  </Typography>
                }
              />
              <PreviewRow
                label="Teams"
                value={<Typography variant="body2">{teamsPreview}</Typography>}
              />
            </Box>

            <Alert severity="info" sx={{ mt: 2 }}>
              {scheduleInfo}
            </Alert>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
