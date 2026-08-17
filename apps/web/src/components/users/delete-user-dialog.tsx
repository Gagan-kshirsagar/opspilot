"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useBulkDeleteUsers, useDeleteUser } from "@/lib/query/users";
import type { UserRow } from "@/types/user";

interface DeleteUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userToDelete?: UserRow | null;
  selectedIds?: string[];
  onDeleted?: () => void;
}

export function DeleteUserDialog({
  open,
  onOpenChange,
  userToDelete,
  selectedIds = [],
  onDeleted,
}: DeleteUserDialogProps) {
  const deleteSingleMutation = useDeleteUser();
  const bulkDeleteMutation = useBulkDeleteUsers();

  const isBulk = Boolean(!userToDelete && selectedIds.length > 0);
  const count = isBulk ? selectedIds.length : 1;

  const isPending =
    deleteSingleMutation.isPending || bulkDeleteMutation.isPending;

  const error =
    deleteSingleMutation.error?.response?.data?.detail ??
    bulkDeleteMutation.error?.response?.data?.detail;

  const handleDelete = async () => {
    try {
      if (isBulk) {
        await bulkDeleteMutation.mutateAsync(selectedIds);
      } else if (userToDelete) {
        await deleteSingleMutation.mutateAsync(userToDelete.id);
      }
      onDeleted?.();
      onOpenChange(false);
    } catch {
      // Error handled by mutation state
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-surface border-subtle">
        <DialogHeader>
          <DialogTitle className="text-foreground">
            {isBulk
              ? `Delete ${count} Users?`
              : `Delete ${userToDelete?.name ?? "User"}?`}
          </DialogTitle>
          <DialogDescription className="text-muted">
            {isBulk
              ? `Are you sure you want to permanently delete these ${count} selected users? This action cannot be undone.`
              : `Are you sure you want to permanently delete ${userToDelete?.name} (${userToDelete?.email})? This action cannot be undone.`}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div
            role="alert"
            className="rounded-lg bg-danger-soft p-3 text-xs text-danger font-medium border border-danger/20"
          >
            {error}
          </div>
        )}

        <DialogFooter className="pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={isPending}
          >
            {isPending ? "Deleting…" : isBulk ? `Delete ${count} Users` : "Delete User"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
