import { zodResolver } from "@hookform/resolvers/zod";
import { IconActivity, IconEye, IconEyeOff } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate } from "react-router-dom";
import { z } from "zod";

import { login } from "@/api/auth";
import { useAuth } from "@/auth/AuthContext";
import { useAuthStore } from "@/stores/authStore";
import { tokens } from "@/theme/palette";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const mutation = useMutation({ mutationFn: login });

  if (isAuthenticated) {
    return <Navigate to="/insights" replace />;
  }

  const onSubmit = async (data: FormValues) => {
    try {
      const response = await mutation.mutateAsync(data);
      setAuth(response.user, response.accessToken);
      navigate("/insights", { replace: true });
    } catch {
      // Error state rendered via mutation.isError
    }
  };

  const errorMessage =
    mutation.error instanceof Error
      ? mutation.error.message
      : "Sign in failed";

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "background.default",
        px: 2,
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          mb: 3,
        }}
      >
        <Box
          sx={{
            width: 36,
            height: 36,
            borderRadius: "9px",
            backgroundColor: tokens.primary,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            flexShrink: 0,
          }}
        >
          <IconActivity size={20} />
        </Box>
        <Box>
          <Typography variant="body1" sx={{ fontWeight: 600, color: "text.primary" }}>
            AI Tool Tracker
          </Typography>
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            Built by Inapp Foundry
          </Typography>
        </Box>
      </Box>

      <Card sx={{ width: 380, maxWidth: "100%" }}>
        <CardContent sx={{ p: "32px", "&:last-child": { pb: "32px" } }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
            Sign in to your account
          </Typography>

          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <TextField
              {...register("email")}
              fullWidth
              label="Email address"
              type="email"
              size="small"
              autoComplete="email"
              autoFocus
              error={Boolean(errors.email)}
              helperText={errors.email?.message}
            />

            <TextField
              {...register("password")}
              fullWidth
              label="Password"
              type={showPassword ? "text" : "password"}
              size="small"
              autoComplete="current-password"
              error={Boolean(errors.password)}
              helperText={errors.password?.message}
              sx={{ mt: 2 }}
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        size="small"
                        onClick={() => setShowPassword((prev) => !prev)}
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        edge="end"
                      >
                        {showPassword ? (
                          <IconEyeOff size={16} />
                        ) : (
                          <IconEye size={16} />
                        )}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
            />

            {mutation.isError && (
              <Alert severity="error" sx={{ mb: 2, mt: 2 }}>
                {errorMessage}
              </Alert>
            )}

            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="medium"
              disabled={mutation.isPending}
              sx={{ mt: 3 }}
              startIcon={
                mutation.isPending ? (
                  <CircularProgress size={14} color="inherit" />
                ) : undefined
              }
            >
              {mutation.isPending ? "Signing in…" : "Sign in"}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
