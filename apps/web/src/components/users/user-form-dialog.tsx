"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateUser, useTeams, useUpdateUser } from "@/lib/query/users";
import type { UserRow } from "@/types/user";

const userSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  email: z.string().email("Please enter a valid email address"),
  role: z.enum(["admin", "manager", "viewer", "guest"]),
  status: z.enum(["active", "pending", "inactive"]),
  team_id: z.string().optional(),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(128)
    .optional()
    .or(z.literal("")),
});

type UserFormValues = z.infer<typeof userSchema>;

interface UserFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userToEdit?: UserRow | null;
}

export function UserFormDialog({
  open,
  onOpenChange,
  userToEdit,
}: UserFormDialogProps) {
  const isEditing = Boolean(userToEdit);
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const { data: teams = [] } = useTeams();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UserFormValues>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      name: "",
      email: "",
      role: "viewer",
      status: "active",
      team_id: "",
      password: "",
    },
  });

  useEffect(() => {
    if (open) {
      if (userToEdit) {
        reset({
          name: userToEdit.name,
          email: userToEdit.email ?? "",
          role: userToEdit.role,
          status: userToEdit.status,
          team_id: userToEdit.team_id ?? "",
          password: "",
        });
      } else {
        reset({
          name: "",
          email: "",
          role: "viewer",
          status: "active",
          team_id: "",
          password: "",
        });
      }
    }
  }, [open, userToEdit, reset]);

  const onSubmit = async (values: UserFormValues) => {
    const payload = {
      name: values.name,
      email: values.email,
      role: values.role,
      status: values.status,
      team_id: values.team_id && values.team_id !== "" ? values.team_id : null,
      ...(values.password ? { password: values.password } : {}),
    };

    if (isEditing && userToEdit) {
      await updateMutation.mutateAsync({
        id: userToEdit.id,
        data: payload,
      });
    } else {
      await createMutation.mutateAsync(payload);
    }
    onOpenChange(false);
  };

  const mutationError = isEditing
    ? updateMutation.error?.response?.data?.detail
    : createMutation.error?.response?.data?.detail;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-surface border-subtle">
        <DialogHeader>
          <DialogTitle className="text-foreground">
            {isEditing ? "Edit User" : "Add New User"}
          </DialogTitle>
          <DialogDescription className="text-muted">
            {isEditing
              ? "Update user profile details and role permissions."
              : "Create a new user account with assigned role and team."}
          </DialogDescription>
        </DialogHeader>

        {mutationError && (
          <div
            role="alert"
            className="rounded-lg bg-danger-soft p-3 text-xs text-danger font-medium border border-danger/20"
          >
            {mutationError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
          {/* Name */}
          <div className="space-y-1.5">
            <Label htmlFor="user-name" className="text-xs font-medium text-foreground">
              Full Name
            </Label>
            <Input
              id="user-name"
              placeholder="e.g. Jane Doe"
              {...register("name")}
              aria-invalid={Boolean(errors.name)}
              className="bg-surface-2 border-subtle"
            />
            {errors.name && (
              <p className="text-xs text-danger">{errors.name.message}</p>
            )}
          </div>

          {/* Email */}
          <div className="space-y-1.5">
            <Label htmlFor="user-email" className="text-xs font-medium text-foreground">
              Email Address
            </Label>
            <Input
              id="user-email"
              type="email"
              placeholder="e.g. jane@company.com"
              {...register("email")}
              aria-invalid={Boolean(errors.email)}
              className="bg-surface-2 border-subtle"
            />
            {errors.email && (
              <p className="text-xs text-danger">{errors.email.message}</p>
            )}
          </div>

          {/* Role & Status Row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="user-role" className="text-xs font-medium text-foreground">
                Role
              </Label>
              <select
                id="user-role"
                {...register("role")}
                className="flex h-8 w-full rounded-lg border border-subtle bg-surface-2 px-2.5 py-1 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="viewer">Viewer</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
                <option value="guest">Guest</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="user-status" className="text-xs font-medium text-foreground">
                Status
              </Label>
              <select
                id="user-status"
                {...register("status")}
                className="flex h-8 w-full rounded-lg border border-subtle bg-surface-2 px-2.5 py-1 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="active">Active</option>
                <option value="pending">Pending</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>

          {/* Team Selection */}
          <div className="space-y-1.5">
            <Label htmlFor="user-team" className="text-xs font-medium text-foreground">
              Team
            </Label>
            <select
              id="user-team"
              {...register("team_id")}
              className="flex h-8 w-full rounded-lg border border-subtle bg-surface-2 px-2.5 py-1 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">No Team Assigned</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>

          {/* Password (Optional for create or update) */}
          <div className="space-y-1.5">
            <Label htmlFor="user-password" className="text-xs font-medium text-foreground">
              {isEditing ? "New Password (leave blank to keep current)" : "Password (optional)"}
            </Label>
            <Input
              id="user-password"
              type="password"
              placeholder="••••••••"
              {...register("password")}
              aria-invalid={Boolean(errors.password)}
              className="bg-surface-2 border-subtle"
            />
            {errors.password && (
              <p className="text-xs text-danger">{errors.password.message}</p>
            )}
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting || createMutation.isPending || updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || createMutation.isPending || updateMutation.isPending}
              className="bg-accent text-accent-foreground hover:bg-accent-hover"
            >
              {isSubmitting || createMutation.isPending || updateMutation.isPending
                ? "Saving…"
                : isEditing
                ? "Update User"
                : "Create User"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
