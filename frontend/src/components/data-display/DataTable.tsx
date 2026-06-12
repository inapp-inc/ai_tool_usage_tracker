import { IconArrowDown, IconArrowUp } from "@tabler/icons-react";
import {
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
} from "@mui/material";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";

import { EmptyState } from "@/components/feedback/EmptyState";
import { tokens } from "@/theme/palette";

export interface Column<T> {
  key: string;
  header: string;
  width?: string | number;
  sortable?: boolean;
  align?: "left" | "right" | "center";
  render?: (row: T, index: number) => ReactNode;
}

type SortDirection = "asc" | "desc";

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  onRowClick?: (row: T) => void;
  stickyHeader?: boolean;
}

const SKELETON_WIDTHS = ["60%", "75%", "90%", "65%", "80%"];

function getRawValue<T>(row: T, key: string): unknown {
  return (row as Record<string, unknown>)[key];
}

function compareValues(a: unknown, b: unknown): number {
  if (a === b) return 0;
  if (a === null || a === undefined) return 1;
  if (b === null || b === undefined) return -1;

  if (typeof a === "number" && typeof b === "number") {
    return a - b;
  }

  return String(a).localeCompare(String(b));
}

export function DataTable<T,>({
  columns,
  rows,
  rowKey,
  loading = false,
  emptyTitle,
  emptyDescription,
  onRowClick,
  stickyHeader = false,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;

    const sorted = [...rows];
    sorted.sort((rowA, rowB) => {
      const result = compareValues(
        getRawValue(rowA, sortKey),
        getRawValue(rowB, sortKey),
      );
      return sortDirection === "asc" ? result : -result;
    });
    return sorted;
  }, [rows, sortDirection, sortKey]);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDirection("asc");
  };

  const renderSortIcon = (columnKey: string) => {
    if (sortKey !== columnKey) return null;
    const Icon = sortDirection === "asc" ? IconArrowUp : IconArrowDown;
    return <Icon size={13} style={{ marginLeft: 4 }} />;
  };

  return (
    <TableContainer>
      <Table stickyHeader={stickyHeader}>
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell
                key={column.key}
                align={column.align ?? "left"}
                sx={{ width: column.width }}
              >
                {column.sortable ? (
                  <TableSortLabel
                    active={sortKey === column.key}
                    direction={sortKey === column.key ? sortDirection : "asc"}
                    onClick={() => handleSort(column.key)}
                    hideSortIcon
                    sx={{ flexDirection: "row", gap: 0.25 }}
                  >
                    {column.header}
                    {renderSortIcon(column.key)}
                  </TableSortLabel>
                ) : (
                  column.header
                )}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>

        <TableBody>
          {loading &&
            Array.from({ length: 5 }).map((_, rowIndex) => (
              <TableRow key={`skeleton-${rowIndex}`}>
                {columns.map((column, colIndex) => (
                  <TableCell key={column.key} align={column.align ?? "left"}>
                    <Skeleton
                      animation="wave"
                      width={
                        SKELETON_WIDTHS[
                          (rowIndex + colIndex) % SKELETON_WIDTHS.length
                        ]
                      }
                      height={16}
                    />
                  </TableCell>
                ))}
              </TableRow>
            ))}

          {!loading && sortedRows.length === 0 && (
            <TableRow>
              <TableCell colSpan={columns.length} sx={{ border: 0, p: 0 }}>
                <EmptyState
                  size="sm"
                  title={emptyTitle ?? "No data"}
                  description={emptyDescription}
                />
              </TableCell>
            </TableRow>
          )}

          {!loading &&
            sortedRows.map((row, index) => (
              <TableRow
                key={rowKey(row)}
                hover={Boolean(onRowClick)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                sx={{
                  cursor: onRowClick ? "pointer" : "default",
                  "&:hover": onRowClick
                    ? { backgroundColor: tokens.bgDefault }
                    : undefined,
                }}
              >
                {columns.map((column) => (
                  <TableCell key={column.key} align={column.align ?? "left"}>
                    {column.render
                      ? column.render(row, index)
                      : String(getRawValue(row, column.key) ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
