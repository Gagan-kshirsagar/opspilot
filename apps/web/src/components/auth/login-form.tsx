"use client";

/**
 * Login / Register form — uses react-hook-form + zod.
 *
 * Features:
 * - Toggle between sign-in and register mode.
 * - "Continue as demo guest" button.
 * - Inline field errors + form-level error on 401/409.
 * - Loading state on submit.
 * - All semantic tokens, no raw colours.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AxiosError } from "axios";
import { Loader2, AlertCircle, Zap } from "lucide-react";

import { cn } from "@/lib/utils";
import { useLogin, useRegister, useGuestLogin } from "@/lib/query/auth";
import { useAuthStore } from "@/stores/authStore";
import type { ErrorResponse } from "@/lib/auth/types";

// ── Schemas ──────────────────────────────────────────────

const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  name: z.string().optional(),
});

const registerSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  name: z.string().min(1, "Name is required").max(255),
});

type FormValues = {
  email: string;
  password: string;
  name?: string;
};

// ── Component ────────────────────────────────────────────

export function LoginForm() {
  const router = useRouter();
  const { status } = useAuthStore();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "authenticated" || status === "guest") {
      router.push("/dashboard");
    }
  }, [status, router]);


  const isRegister = mode === "register";
  const schema = isRegister ? registerSchema : loginSchema;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", name: "" },
  });

  const loginMutation = useLogin();
  const registerMutation = useRegister();
  const guestMutation = useGuestLogin();

  const isPending =
    loginMutation.isPending ||
    registerMutation.isPending ||
    guestMutation.isPending ||
    isSubmitting;

  function toggleMode() {
    setMode((m) => (m === "login" ? "register" : "login"));
    setFormError(null);
    reset();
  }

  function extractErrorMessage(err: unknown): string {
    if (err instanceof AxiosError) {
      const data = err.response?.data as ErrorResponse | undefined;
      return data?.detail ?? "Something went wrong. Please try again.";
    }
    return "Something went wrong. Please try again.";
  }

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      if (isRegister) {
        await registerMutation.mutateAsync({
          email: values.email,
          password: values.password,
          name: values.name ?? "",
        });
      } else {
        await loginMutation.mutateAsync({
          email: values.email,
          password: values.password,
        });
      }
    } catch (err) {
      setFormError(extractErrorMessage(err));
    }
  }

  async function handleGuest() {
    setFormError(null);
    try {
      await guestMutation.mutateAsync();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    }
  }

  return (
    <div className="w-full max-w-sm animate-fade-in">
      {/* ── Header ─────────────────────────────────────── */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {isRegister ? "Create an account" : "Welcome back"}
        </h1>
        <p className="mt-2 text-sm text-muted">
          {isRegister
            ? "Sign up to get started with OpsPilot"
            : "Sign in to your OpsPilot account"}
        </p>
      </div>

      {/* ── Form-level error ───────────────────────────── */}
      {formError && (
        <div
          role="alert"
          className={cn(
            "mb-4 flex items-start gap-2 rounded-lg border p-3",
            "border-danger/30 bg-danger-soft text-danger text-sm",
          )}
        >
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      {/* ── Form ───────────────────────────────────────── */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Name (register only) */}
        {isRegister && (
          <div className="space-y-1.5">
            <label
              htmlFor="auth-name"
              className="block text-sm font-medium text-foreground"
            >
              Name
            </label>
            <input
              id="auth-name"
              type="text"
              autoComplete="name"
              placeholder="Your name"
              disabled={isPending}
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? "auth-name-error" : undefined}
              className={cn(
                "flex h-10 w-full rounded-lg border bg-surface px-3 text-sm text-foreground",
                "placeholder:text-faint",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "transition-colors",
                errors.name
                  ? "border-danger focus:ring-danger/40"
                  : "border-subtle",
              )}
              {...register("name")}
            />
            {errors.name && (
              <p
                id="auth-name-error"
                className="text-xs text-danger"
                role="alert"
              >
                {errors.name.message}
              </p>
            )}
          </div>
        )}

        {/* Email */}
        <div className="space-y-1.5">
          <label
            htmlFor="auth-email"
            className="block text-sm font-medium text-foreground"
          >
            Email
          </label>
          <input
            id="auth-email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            disabled={isPending}
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? "auth-email-error" : undefined}
            className={cn(
              "flex h-10 w-full rounded-lg border bg-surface px-3 text-sm text-foreground",
              "placeholder:text-faint",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-colors",
              errors.email
                ? "border-danger focus:ring-danger/40"
                : "border-subtle",
            )}
            {...register("email")}
          />
          {errors.email && (
            <p
              id="auth-email-error"
              className="text-xs text-danger"
              role="alert"
            >
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <label
            htmlFor="auth-password"
            className="block text-sm font-medium text-foreground"
          >
            Password
          </label>
          <input
            id="auth-password"
            type="password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            placeholder="••••••••"
            disabled={isPending}
            aria-invalid={!!errors.password}
            aria-describedby={
              errors.password ? "auth-password-error" : undefined
            }
            className={cn(
              "flex h-10 w-full rounded-lg border bg-surface px-3 text-sm text-foreground",
              "placeholder:text-faint",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-colors",
              errors.password
                ? "border-danger focus:ring-danger/40"
                : "border-subtle",
            )}
            {...register("password")}
          />
          {errors.password && (
            <p
              id="auth-password-error"
              className="text-xs text-danger"
              role="alert"
            >
              {errors.password.message}
            </p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isPending}
          className={cn(
            "flex h-10 w-full items-center justify-center gap-2 rounded-lg",
            "bg-accent text-accent-foreground text-sm font-medium",
            "hover:bg-accent-hover active:scale-[.98]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "transition-all",
          )}
        >
          {(loginMutation.isPending || registerMutation.isPending) && (
            <Loader2 className="size-4 animate-spin" />
          )}
          {isRegister ? "Create account" : "Sign in"}
        </button>
      </form>

      {/* ── Divider ────────────────────────────────────── */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-subtle" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-background px-2 text-muted">or</span>
        </div>
      </div>

      {/* ── Guest login ────────────────────────────────── */}
      <button
        type="button"
        onClick={handleGuest}
        disabled={isPending}
        className={cn(
          "flex h-10 w-full items-center justify-center gap-2 rounded-lg",
          "border border-subtle bg-surface text-sm font-medium text-foreground",
          "hover:bg-surface-2 active:scale-[.98]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "transition-all",
        )}
      >
        {guestMutation.isPending ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Zap className="size-4" />
        )}
        Continue as demo guest
      </button>

      {/* ── Toggle mode ────────────────────────────────── */}
      <p className="mt-6 text-center text-sm text-muted">
        {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
        <button
          type="button"
          onClick={toggleMode}
          disabled={isPending}
          className="font-medium text-accent hover:text-accent-hover focus-visible:outline-none focus-visible:underline"
        >
          {isRegister ? "Sign in" : "Create account"}
        </button>
      </p>
    </div>
  );
}
